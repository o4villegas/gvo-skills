/**
 * MCP tool definitions and handlers.
 *
 * Tool names match the suffixes that the gvo-router skill scans for in §1 of its
 * SKILL.md (`__codebase_read_file`, `__codebase_search_code`, etc.). Once registered,
 * claude.ai prefixes each tool with `mcp__<connector-hash>__` — the suffix is stable.
 */
import { fetchFile, listDirectory, findFiles, searchCode } from "./github";
import { ToolError } from "./mcp";

export type AppEnv = {
  GITHUB_OWNER: string;
  GITHUB_REPO: string;
  GITHUB_REF: string;
  ROOT_ID: string;
  CACHE: KVNamespace;
};

type ToolDefinition = {
  name: string;
  description: string;
  inputSchema: {
    type: "object";
    properties: Record<string, { type: string; description?: string }>;
    required?: string[];
  };
};

type ToolResult = {
  content: Array<{ type: "text"; text: string }>;
};

const TOOLS: ToolDefinition[] = [
  {
    name: "codebase_list_allowed_roots",
    description:
      "List the codebase roots this server exposes. Returns the root ids that can be passed to other codebase_* tools as the `root` argument.",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "codebase_read_file",
    description:
      "Read a single file from the codebase by repo-relative path. Returns the file's text content. Use for SKILL.md files, registry.json, and project files.",
    inputSchema: {
      type: "object",
      properties: {
        path: {
          type: "string",
          description: "Repo-relative path, e.g. 'skills/nexus/registry.json'. Leading '/' is tolerated.",
        },
        root: {
          type: "string",
          description: "Root id returned by codebase_list_allowed_roots.",
        },
      },
      required: ["path", "root"],
    },
  },
  {
    name: "codebase_list_directory",
    description:
      "List directory entries (files and subdirectories) at the given path. Returns name, type, size, and path for each entry.",
    inputSchema: {
      type: "object",
      properties: {
        path: {
          type: "string",
          description:
            "Repo-relative directory path. Empty string or '.' means the repo root. No trailing slash needed.",
        },
        root: {
          type: "string",
          description: "Root id returned by codebase_list_allowed_roots.",
        },
      },
      required: ["root"],
    },
  },
  {
    name: "codebase_find_files",
    description:
      "Find files in the codebase matching a glob pattern. Supports ** for any path including /, * for any chars except /, and ? for a single char. Returns repo-relative paths.",
    inputSchema: {
      type: "object",
      properties: {
        pattern: {
          type: "string",
          description: "Glob pattern, e.g. '**/SKILL.md' or 'skills/*/SKILL.md'.",
        },
        root: {
          type: "string",
          description: "Root id returned by codebase_list_allowed_roots.",
        },
      },
      required: ["pattern", "root"],
    },
  },
  {
    name: "codebase_search_code",
    description:
      "Search file contents in the codebase for a literal substring (case-insensitive). Returns matching paths with line snippets. Limited to text-ish files; capped at 100 candidate files per search.",
    inputSchema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "Literal substring to search for. Not a regex.",
        },
        root: {
          type: "string",
          description: "Root id returned by codebase_list_allowed_roots.",
        },
      },
      required: ["query", "root"],
    },
  },
];

export function listTools(): ToolDefinition[] {
  return TOOLS;
}

function textResult(text: string): ToolResult {
  return { content: [{ type: "text", text }] };
}

function assertRoot(root: string, env: AppEnv): void {
  if (root !== env.ROOT_ID) {
    throw new ToolError(
      `Unknown root '${root}'. This server exposes only '${env.ROOT_ID}'. Call codebase_list_allowed_roots first.`,
    );
  }
}

function normalizePath(input: string): string {
  // Strip leading '/' and './'; tolerate empty/undefined.
  return input.replace(/^\.?\//, "").replace(/^\/+/, "");
}

export async function callTool(
  name: string,
  args: Record<string, unknown>,
  env: AppEnv,
): Promise<ToolResult> {
  switch (name) {
    case "codebase_list_allowed_roots":
      return textResult(
        JSON.stringify(
          {
            roots: [
              {
                id: env.ROOT_ID,
                repo: `${env.GITHUB_OWNER}/${env.GITHUB_REPO}`,
                ref: env.GITHUB_REF,
              },
            ],
          },
          null,
          2,
        ),
      );

    case "codebase_read_file": {
      const path = normalizePath(String(args.path ?? ""));
      const root = String(args.root ?? "");
      assertRoot(root, env);
      if (!path) throw new ToolError("Missing 'path' argument");
      const content = await fetchFile(env, path);
      return textResult(content);
    }

    case "codebase_list_directory": {
      const path = normalizePath(String(args.path ?? ""));
      const root = String(args.root ?? "");
      assertRoot(root, env);
      const entries = await listDirectory(env, path);
      return textResult(JSON.stringify({ path: path || ".", entries }, null, 2));
    }

    case "codebase_find_files": {
      const pattern = String(args.pattern ?? "");
      const root = String(args.root ?? "");
      assertRoot(root, env);
      if (!pattern) throw new ToolError("Missing 'pattern' argument");
      const matches = await findFiles(env, pattern);
      return textResult(
        JSON.stringify({ pattern, matches, count: matches.length }, null, 2),
      );
    }

    case "codebase_search_code": {
      const query = String(args.query ?? "");
      const root = String(args.root ?? "");
      assertRoot(root, env);
      if (!query) throw new ToolError("Missing 'query' argument");
      const results = await searchCode(env, query);
      return textResult(
        JSON.stringify({ query, results, count: results.length }, null, 2),
      );
    }

    default:
      throw new ToolError(`Unknown tool: ${name}`);
  }
}
