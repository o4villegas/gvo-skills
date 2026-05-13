/**
 * GitHub source for read-only access to gvo-skills.
 *
 * Strategy:
 *   - File reads use `raw.githubusercontent.com` (no rate limit, no auth, direct text).
 *   - Directory listings use the GitHub Contents API.
 *   - Recursive find uses the GitHub Git Trees API (single call, returns whole tree).
 *   - Code search uses an in-Worker grep over fetched files. The tree call is cached
 *     so repeated searches don't re-fetch the file list. Text search is capped at 100
 *     files per query and skips non-text extensions to keep latency bounded.
 *   - All responses are cached in KV with TTL 300s. Skill files don't change often;
 *     a 5-minute staleness is acceptable. Push-based invalidation can be added later
 *     via a GitHub webhook hitting a `/cache/invalidate` endpoint.
 *
 * No GitHub token is used. The repo is public; the public quota (60 req/h unauthenticated
 * per IP) is enough given KV caches hit-after-first.
 */
import { ToolError } from "./mcp";

const CACHE_TTL_SECONDS = 300;
const USER_AGENT = "gvo-skills-mcp/0.1 (Cloudflare Worker; +https://gvo-skills-mcp.lando555.workers.dev)";

type GitHubEnv = {
  GITHUB_OWNER: string;
  GITHUB_REPO: string;
  GITHUB_REF: string;
  CACHE: KVNamespace;
};

export type DirEntry = {
  name: string;
  type: "file" | "dir" | "symlink" | "submodule";
  path: string;
  size: number;
};

export type SearchHit = {
  path: string;
  matches: Array<{ line: number; snippet: string }>;
};

function cacheKey(env: GitHubEnv, kind: string, key: string): string {
  return `${kind}:${env.GITHUB_OWNER}/${env.GITHUB_REPO}@${env.GITHUB_REF}:${key}`;
}

async function cached<T>(
  env: GitHubEnv,
  kind: string,
  key: string,
  loader: () => Promise<T>,
): Promise<T> {
  const k = cacheKey(env, kind, key);
  const hit = await env.CACHE.get(k, "text");
  if (hit !== null) {
    try {
      return JSON.parse(hit) as T;
    } catch {
      // Corrupted cache entry — fall through and reload.
    }
  }
  const value = await loader();
  // Don't fail the request if KV write fails — caching is opportunistic.
  await env.CACHE.put(k, JSON.stringify(value), {
    expirationTtl: CACHE_TTL_SECONDS,
  }).catch(() => {});
  return value;
}

async function ghGet(url: string, accept = "application/vnd.github+json"): Promise<Response> {
  return fetch(url, {
    headers: {
      "User-Agent": USER_AGENT,
      Accept: accept,
    },
  });
}

export async function fetchFile(env: GitHubEnv, path: string): Promise<string> {
  return cached(env, "file", path, async () => {
    const url = `https://raw.githubusercontent.com/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/${env.GITHUB_REF}/${path}`;
    const res = await ghGet(url, "*/*");
    if (res.status === 404) {
      throw new ToolError(`File not found: ${path}`);
    }
    if (!res.ok) {
      throw new ToolError(
        `GitHub raw fetch failed for '${path}': ${res.status} ${res.statusText}`,
      );
    }
    return res.text();
  });
}

export async function listDirectory(env: GitHubEnv, path: string): Promise<DirEntry[]> {
  return cached(env, "dir", path || ".", async () => {
    const url = `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/contents/${path}?ref=${env.GITHUB_REF}`;
    const res = await ghGet(url);
    if (res.status === 404) {
      throw new ToolError(`Directory not found: ${path || "(repo root)"}`);
    }
    if (!res.ok) {
      throw new ToolError(
        `GitHub contents fetch failed for '${path}': ${res.status} ${res.statusText}`,
      );
    }
    const data = (await res.json()) as unknown;
    if (!Array.isArray(data)) {
      throw new ToolError(`Path is not a directory: ${path}`);
    }
    return (data as Array<Record<string, unknown>>).map((e) => ({
      name: String(e.name ?? ""),
      type: (e.type as DirEntry["type"]) ?? "file",
      path: String(e.path ?? ""),
      size: typeof e.size === "number" ? e.size : 0,
    }));
  });
}

/**
 * Fetch the full repo tree once per cache TTL. Used by both find_files and search_code.
 */
async function fullTree(env: GitHubEnv): Promise<Array<{ path: string; type: string; size?: number }>> {
  return cached(env, "tree", "_recursive", async () => {
    const url = `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/git/trees/${env.GITHUB_REF}?recursive=1`;
    const res = await ghGet(url);
    if (!res.ok) {
      throw new ToolError(
        `GitHub tree fetch failed: ${res.status} ${res.statusText}`,
      );
    }
    const data = (await res.json()) as {
      tree: Array<{ path: string; type: string; size?: number }>;
      truncated?: boolean;
    };
    if (data.truncated) {
      // Tree was truncated by GitHub (>100k entries). This repo is far smaller, so
      // we'd only hit this on a runaway commit. Surface a partial result rather than fail.
      console.warn("[gvo-skills-mcp] tree truncated by GitHub; results may be incomplete");
    }
    return data.tree.map(({ path, type, size }) => ({ path, type, size }));
  });
}

function globToRegex(glob: string): RegExp {
  let re = "^";
  for (let i = 0; i < glob.length; i++) {
    const c = glob[i];
    if (c === "*" && glob[i + 1] === "*") {
      re += ".*";
      i++;
    } else if (c === "*") {
      re += "[^/]*";
    } else if (c === "?") {
      re += "[^/]";
    } else if (".+()|^$[]\\{}".includes(c)) {
      re += "\\" + c;
    } else {
      re += c;
    }
  }
  re += "$";
  return new RegExp(re);
}

export async function findFiles(env: GitHubEnv, pattern: string): Promise<string[]> {
  const tree = await fullTree(env);
  const re = globToRegex(pattern);
  return tree.filter((e) => e.type === "blob" && re.test(e.path)).map((e) => e.path);
}

const TEXT_EXTENSIONS =
  /\.(md|markdown|txt|json|jsonc|yaml|yml|toml|ts|tsx|js|jsx|mjs|cjs|sh|bash|py|html|css|scss|sql|env|gitignore|gitattributes)$/i;

const SEARCH_FILE_CAP = 100;
const MAX_SNIPPETS_PER_FILE = 5;
const MAX_SNIPPET_CHARS = 200;

export async function searchCode(env: GitHubEnv, query: string): Promise<SearchHit[]> {
  const needle = query.toLowerCase();
  return cached(env, "search", `q:${needle}`, async () => {
    const tree = await fullTree(env);
    // Prefer SKILL.md and registry.json early so the most relevant results return first.
    const ranked = tree
      .filter((e) => e.type === "blob" && TEXT_EXTENSIONS.test(e.path))
      .sort((a, b) => priority(b.path) - priority(a.path))
      .slice(0, SEARCH_FILE_CAP);

    const hits: SearchHit[] = [];
    for (const entry of ranked) {
      let content: string;
      try {
        content = await fetchFile(env, entry.path);
      } catch {
        continue;
      }
      const lines = content.split("\n");
      const matches: SearchHit["matches"] = [];
      for (let i = 0; i < lines.length && matches.length < MAX_SNIPPETS_PER_FILE; i++) {
        if (lines[i].toLowerCase().includes(needle)) {
          matches.push({
            line: i + 1,
            snippet: lines[i].trim().slice(0, MAX_SNIPPET_CHARS),
          });
        }
      }
      if (matches.length > 0) {
        hits.push({ path: entry.path, matches });
      }
    }
    return hits;
  });
}

function priority(path: string): number {
  if (path.endsWith("SKILL.md")) return 3;
  if (path.endsWith("registry.json")) return 3;
  if (path.endsWith(".md")) return 2;
  if (path.endsWith(".json")) return 1;
  return 0;
}
