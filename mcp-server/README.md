# gvo-skills-mcp

Cloudflare Worker that exposes the `gvo-skills` GitHub repo as an MCP server over HTTP. Designed to replace the VPS-hosted `from-desktop` MCP that the `gvo-router` skill expects in `claude.ai` cloud sessions.

| | |
|---|---|
| **Source repo** | `o4villegas/gvo-skills` (public, this repo) |
| **Worker URL** | `https://gvo-skills-mcp.lando555.workers.dev` |
| **MCP endpoint** | `POST /mcp` (JSON-RPC 2.0) |
| **Health** | `GET /health` |
| **Auth** | None (read-only over a public repo) |
| **Cache** | KV namespace, 5-minute TTL per path |

## Tools exposed

All read-only; scoped to the GitHub repo + ref configured in `wrangler.toml`:

- `codebase_list_allowed_roots`
- `codebase_read_file`
- `codebase_list_directory`
- `codebase_find_files` (glob)
- `codebase_search_code` (literal substring, case-insensitive)

Names match the suffixes `gvo-router/SKILL.md` §1 scans for.

## First-time setup

```bash
cd mcp-server
npm install

# Authenticate Wrangler if you haven't already
npx wrangler login

# Create the KV namespace and paste the returned id into wrangler.toml
npx wrangler kv:namespace create GVO_SKILLS_CACHE
# → outputs something like: id = "abc123..."  — copy that into wrangler.toml's PLACEHOLDER_ID

# Deploy
npm run deploy
```

After deploy, verify:

```bash
curl https://gvo-skills-mcp.lando555.workers.dev/health
# expected: { "status": "ok", "service": "gvo-skills-mcp", ... }
```

## Connecting to claude.ai

1. Open `claude.ai` → Settings → Connectors (or Integrations / Custom MCP, depending on the UI version).
2. Add a custom MCP server:
   - **URL**: `https://gvo-skills-mcp.lando555.workers.dev/mcp`
   - **Name**: any (e.g. `gvo-skills`). The gvo-router skill scans by tool-name suffix, not server name.
   - **Auth**: none
3. Upload the `gvo-router` skill to claude.ai. The easiest path is the pre-built bundle at `skills/gvo-router/gvo-router.zip` (contains `SKILL.md` + all three reference files in the correct directory layout). Manual alternative: paste the contents of `skills/gvo-router/SKILL.md` plus the three reference files in `skills/gvo-router/references/`.
4. In any claude.ai session, type one of the router's trigger phrases (`build me`, `fix`, `implement`, `plan`, `use the router`, etc.). The router should:
   - Detect the codebase tools in the session catalog,
   - Read `skills/nexus/registry.json` from this Worker,
   - Spawn its 3-tier opus organization,
   - Deliver a verification matrix + assumption ledger.

If the router stops at §1 saying the from-desktop MCP isn't connected, double-check the MCP was added in step 2 and re-trigger.

## Deploy via git push (after first manual deploy)

The user's standard pattern is `git push` → Cloudflare Workers Builds → auto-deploy. To wire it up:

1. In the Cloudflare dashboard → Workers & Pages → `gvo-skills-mcp` → Settings → Git integration.
2. Connect the `o4villegas/gvo-skills` repo.
3. Set **Root directory** to `mcp-server`.
4. **Build command**: `npm install`
5. **Deploy command**: `npm run deploy`
6. **Branch**: `main`

After this, every push to `main` that touches `mcp-server/` triggers a build.

## Local development

```bash
npm run dev          # wrangler dev — runs locally with an in-memory KV shim
npm run typecheck    # tsc --noEmit
npm run tail         # stream production logs
```

Hit the local server with:

```bash
curl -s -X POST http://localhost:8787/mcp \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## How it works

| Tool | Backing GitHub call | Cache key |
|---|---|---|
| `codebase_read_file` | `https://raw.githubusercontent.com/<owner>/<repo>/<ref>/<path>` | `file:<owner>/<repo>@<ref>:<path>` |
| `codebase_list_directory` | `https://api.github.com/repos/<owner>/<repo>/contents/<path>?ref=<ref>` | `dir:<...>:<path>` |
| `codebase_find_files` | `https://api.github.com/repos/<owner>/<repo>/git/trees/<ref>?recursive=1` (cached, filtered with a glob regex) | `tree:<...>:_recursive` |
| `codebase_search_code` | Reuses the tree call + in-Worker grep over fetched files (text-only extensions; capped at 100 files; ranked SKILL.md/registry.json first) | `search:<...>:q:<lowercased-query>` |

KV TTL is 300 seconds. Skill files change rarely, so 5 minutes of staleness is acceptable. If you want push-driven invalidation, add a GitHub webhook hitting a `POST /cache/invalidate` endpoint and clear the namespace there — left as a follow-up for when it actually matters.

## What this Worker is NOT

- Not a write surface. There are no POST tools — claude.ai cannot modify gvo-skills through this.
- Not authenticated. The public repo is the trust boundary; anyone with the URL gets the same reads.
- Not a replacement for skill-evolution. That Worker is separate (`skill-evolution.lando555.workers.dev`) and currently passive.
- Not Claude Code's skill loader. Claude Code Desktop and the WSL CLI read skills from the local filesystem via the `~/.claude/skills/` symlink; they don't need this MCP.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `/health` returns 200 but `tools/list` returns nothing | Worker is on an older deploy without tools wired | Re-run `npm run deploy` and check `wrangler tail` for errors |
| GitHub returns 403 with "API rate limit exceeded" | Unauthenticated 60-req/hour bucket exhausted (likely from a hot loop bypassing the cache) | Wait an hour, or add a GitHub PAT as a Worker secret (`wrangler secret put GITHUB_TOKEN`) and update `src/github.ts` to send `Authorization: Bearer ...` |
| `codebase_search_code` is slow first call, fast after | Expected — first call fetches up to 100 files; subsequent calls hit KV cache | n/a |
| `Directory not found` on a directory that exists locally but not on `main` | The Worker reads the GitHub `main` branch, not your working tree | Commit + push first, or change `GITHUB_REF` in `wrangler.toml` to a different branch |
