# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`gvo-skills` is a centralized Claude Code skill library, kept as the single source of truth across three environments. The root is pure markdown + shell — no build, no tests, no CI, no linter. The sole exception is `mcp-server/`, a TypeScript Cloudflare Worker subproject with its own `package.json` and deploy pipeline (see [The mcp-server Worker](#the-mcp-server-worker) below).

| Environment | Clone | Skills symlink |
|---|---|---|
| WSL (CLI) | `~/gvo-skills` | `~/.claude/skills -> ~/gvo-skills/skills` |
| Windows (Desktop) | `C:\dev\gvo-skills` | `C:\Users\Lando\.claude\skills -> C:\dev\gvo-skills\skills` (junction) |
| VPS | `~/gvo-skills` | `~/.claude/skills -> ~/gvo-skills/skills` |

Edits land here → `git push` → other environments pull via `./sync.sh`. Claude Code Desktop's `SessionStart` hook calls `sync.sh` automatically; CLI and VPS run it manually. Pushes that touch `mcp-server/` additionally trigger a Cloudflare Workers Builds deploy.

## Layout (the parts that matter)

```
gvo-skills/
├── skills/
│   ├── nexus/                              # Orchestrator. Has its own CLAUDE.md — read it.
│   │   ├── SKILL.md                        # Auto-loaded master skill
│   │   ├── registry.json                   # Canonical skill index (single source of truth, 64 entries)
│   │   ├── pipeline/                       # 7 phase files
│   │   ├── agents/                         # 6 expert personas
│   │   ├── skills/                         # 28 nested Tier-1 skills (siblings live at top level)
│   │   └── references/                     # 16 Tier-2 reference docs
│   ├── awesome-claude-corporate-skills-main/   # Vendored bundle (166 skills, 14 role categories)
│   │                                       # Treat as READ-ONLY. Register via scripts/sync-bundle-registry.py.
│   ├── <66 top-level skills>/              # gvo-router, from-prompter, kc-trivia-work, etc.
│   ├── learned/                            # Gitignored placeholder (skill-evolution output)
│   └── user/                               # Gitignored placeholder
├── mcp-server/                             # Cloudflare Worker exposing this repo to claude.ai cloud over MCP
│   ├── src/{index,mcp,tools,github}.ts     # Hono entrypoint + JSON-RPC dispatcher + tool impls + GitHub adapter
│   ├── README.md                           # Setup, deploy, troubleshooting — read it before touching this
│   ├── package.json                        # The ONLY npm project in this repo
│   └── wrangler.toml                       # GITHUB_OWNER/REPO/REF + KV namespace binding
├── scripts/
│   ├── sync-bundle-registry.py             # Bundle import tool (audit | stub | apply)
│   └── validate.py                         # Manual pre-commit validator (description cap, registry integrity)
├── setup.sh                                # One-time per-env install (creates symlink, registers chrome-devtools MCP)
└── sync.sh                                 # Daily pull + symlink verify + inventory
```

A root-level `registry.json` previously existed as a subset mirror of nexus's. It was removed because only `gvo-router` read it and a single source of truth is cleaner. `skills/nexus/registry.json` is now the only registry.

## SKILL.md anatomy

Frontmatter is just two fields (no `allowed-tools` in this repo — it's a harness concept, not a skill-file concept):

```yaml
---
name: <directory-name>
description: >
  Plain-English sentence describing what the skill does, followed by trigger
  phrases inline: 'Trigger on "phrase one", "phrase two", "phrase three"' or
  'Use when the user wants X, Y, or Z'. Activation is matched against this
  text — without trigger phrases the skill will never load.
---

# <Title>

<body>
```

The folded scalar (`description: >`) lets the description span multiple lines while collapsing to one paragraph at parse time. Use it for anything longer than ~80 chars.

### The 1024-character description limit (claude.ai cloud)

claude.ai cloud sessions enforce a **1024-character cap on each skill's description**. Skills with longer descriptions fail to register and cannot route work.

Two independent sources confirm the cap:

1. Commit `a2db4d7` in this repo — fixed `gvo-router` from 1035 chars (broken) to 891 chars (working).
2. `agentsys/checklists/new-skill.md:21` (mature plugin ecosystem under the `agent-sh` org) — documents "Max 1024 characters" as the canonical skill description limit.

Anthropic's public skill docs describe the progressive-disclosure use of the description field but don't publish the numeric cap. Treat 1024 as the hard upper bound; aim for ≤ 900 for safe headroom.

Before committing a new or edited SKILL.md, run `python3 scripts/validate.py` — it flags `DESC_OVER_LIMIT` (FAIL, > 1024) and `DESC_NEAR_LIMIT` (WARN, 900–1023). Or measure a single file directly:

```bash
python3 -c "
import re, yaml, sys
with open(sys.argv[1]) as f:
    fm = yaml.safe_load(re.match(r'^---\n(.*?)\n---', f.read(), re.DOTALL).group(1))
print(len(fm['description'].strip()))
" skills/<name>/SKILL.md
```

Claude Code (Desktop/CLI) is more permissive than the cloud, but the same skill files are used by both — keep all descriptions under 1024.

## The canonical registry

`skills/nexus/registry.json` is the **only** registry. 64 entries (current). Both `nexus` (Claude Code orchestrator) and `gvo-router` (claude.ai cloud router) read it.

When adding a top-level skill:

1. Create `skills/<name>/SKILL.md` with valid frontmatter (`name`, `description`).
2. Run `python3 scripts/validate.py` to confirm the description is under 1024 chars and the frontmatter parses.
3. Add an entry to `skills/nexus/registry.json`. Use the schema below.
4. Commit and push. Run `./sync.sh` on other environments.

Entry schema:

```json
{
  "id": "<name>__imp_<8-hex-chars>",
  "name": "<name>",
  "description": "<≤280 chars; can be a trimmed version of SKILL.md description>",
  "path": "<see path rules below>",
  "category": "planning|delivery|review|workflow|...",
  "tags": [],
  "triggers": ["phrase one", "phrase two"],
  "isActive": true,
  "source": "<provenance label, e.g. 'gvo-skills' or upstream repo slug>"
}
```

Path resolution (relative to `skills/nexus/`):

| Skill location | Path field |
|---|---|
| Nested under nexus at `skills/nexus/skills/<name>/SKILL.md` | `skills/<name>/SKILL.md` |
| Top-level sibling at `skills/<name>/SKILL.md` | `../<name>/SKILL.md` |
| Vendored in the corporate-skills bundle | `../awesome-claude-corporate-skills-main/<category>/<name>/SKILL.md` |

`triggers: []` (empty) means the skill relies on description-text matching only — less reliable. Populate `triggers` explicitly for new entries.

## The vendored corporate-skills bundle

`skills/awesome-claude-corporate-skills-main/` is a flattened vendor of [hesreallyhim/awesome-claude-corporate-skills](https://github.com/hesreallyhim/awesome-claude-corporate-skills) — 166 SKILL.md files across 14 role categories (`00-meta` through `13-document-processing`). `INDEX.md` at the bundle root catalogs all 166.

**Do not edit files inside this directory by hand.** It's vendored — changes get clobbered on next vendor refresh.

To register additional bundle skills in nexus:

```bash
# 1. Audit: see what's net-new vs. what collides with existing nexus/PLUGIN_SKILLS entries
python3 scripts/sync-bundle-registry.py audit skills/awesome-claude-corporate-skills-main

# 2. Stub: emit skeleton entries with triggers=[] for human curation
python3 scripts/sync-bundle-registry.py stub skills/awesome-claude-corporate-skills-main --out candidates.json

# 3. Hand-edit candidates.json — at minimum fill in `triggers` for each entry

# 4. Apply: append validated entries to skills/nexus/registry.json (skips collisions)
python3 scripts/sync-bundle-registry.py apply candidates.json
```

The script writes to `skills/nexus/registry.json` (the only registry). `PLUGIN_SKILLS` inside the script is the list of skill names already provided by the Claude Code harness (`claude-api`, `nexus`, `from-prompter`, etc.) — these are skipped to prevent double-registration. Update `PLUGIN_SKILLS` when Anthropic ships new plugin skills.

Currently 21 of the 166 bundle skills are registered (commit `6b2d3ef`).

### Known-broken vendored files (do not try to fix)

`validate.py` reports ~38 FAIL rows inside `skills/awesome-claude-corporate-skills-main/` that are upstream artifacts, not local bugs:

- **~26 files lack YAML frontmatter entirely** — mostly under `02-finance-accounting/` (e.g. `model-update`, `deal-tracker`, `teaser`, `unit-economics`, `dd-checklist`, etc.). These render as `BAD_FRONTMATTER`. They will not register on claude.ai cloud as skills; they may still be useful as reference documents.
- **~8 files have `name` mismatching the directory** (e.g. `call-prep-common-room/` has `name: call-prep`; `resume-generator/` has `name: tailored-resume-generator`). Render as `NAME_DIR_MISMATCH`.
- **1 file missing `description`** (`02-finance-accounting/check-model/`).

These are someone else's repository to fix. If you care enough, file an upstream issue at [hesreallyhim/awesome-claude-corporate-skills](https://github.com/hesreallyhim/awesome-claude-corporate-skills). Do not edit them locally — `git mv` or rewrite would be clobbered on the next vendor refresh.

`skills/everything-claude-code/SKILL.md` also reports `NAME_DIR_MISMATCH` (`name: everything-claude-code-conventions` vs dir `everything-claude-code`) — this is an intentional historical name from when the skill was migrated. Leave it.

## The mcp-server Worker

`mcp-server/` is a Cloudflare Worker (TypeScript + Hono) that exposes the public GitHub state of this repo as an MCP server over HTTP. It exists because **claude.ai cloud sessions cannot read the local filesystem** — the `gvo-router` skill (cloud-side counterpart to `nexus`) needs to read `skills/nexus/registry.json` and individual SKILL.md files at runtime. The Worker proxies GitHub Raw + Tree API + a small in-Worker substring grep, cached in KV with a 5-minute TTL. It replaces the older VPS-hosted `from-desktop` MCP that the skill used to depend on.

- **Deployed at**: `https://gvo-skills-mcp.lando555.workers.dev`
- **Endpoints**: `POST /mcp` (JSON-RPC 2.0; honors both `application/json` and `text/event-stream` Accept headers — claude.ai's client requires SSE in practice), `GET /health`, `GET /` (banner), `GET /mcp` with SSE (empty-stream stub for clients that probe it)
- **Tools** (all read-only, names match the `codebase_*` suffixes `gvo-router/SKILL.md` §1 scans for): `codebase_list_allowed_roots`, `codebase_read_file`, `codebase_list_directory`, `codebase_find_files`, `codebase_search_code`
- **Source of truth for reads**: GitHub `main` branch via `wrangler.toml`'s `[vars]` (`GITHUB_OWNER=o4villegas`, `GITHUB_REPO=gvo-skills`, `GITHUB_REF=main`). Local working-tree changes are invisible until pushed.
- **Trust boundary**: the public repo. No auth; anyone with the URL gets the same reads.
- **KV namespace**: `CACHE` binding (id in `wrangler.toml`), 300s TTL per path.

Detailed setup, the GitHub-API/KV cache key schema, and a troubleshooting table live in `mcp-server/README.md` — read that before deploying or debugging. A one-shot probe at `scripts/probe-mcp-sse.sh` exercises all four JSON/SSE response paths against production; run it after each deploy.

## Common commands

### Repo root (skill library)

```bash
./setup.sh                              # First-time per-env install (creates symlink, registers chrome-devtools MCP)
./sync.sh                               # Daily: git pull --ff-only + symlink verify + inventory
./sync.sh --force                       # Skip ff-only check (rarely needed)
python3 scripts/validate.py             # Pre-commit gate: description cap, frontmatter, registry integrity
python3 scripts/validate.py --quiet     # Summary line only
python3 scripts/validate.py --json      # Machine-readable findings
git push origin main                    # Triggers env propagation on next sync.sh + auto-deploys mcp-server/ if it changed
```

### mcp-server/ subproject (Cloudflare Worker)

```bash
cd mcp-server
npm install                             # one-time
npm run dev                             # wrangler dev → localhost:8787
npm run typecheck                       # tsc --noEmit (only build-style gate in the repo)
npm run deploy                          # wrangler deploy (skip unless out-of-band — git push to main auto-deploys)
npm run tail                            # stream production logs
```

There is no `npm test`, `make`, or `pytest` anywhere in this repo. `mcp-server/` has `npm run typecheck` but no test suite. Validation is otherwise manual:

- **Full validator**: `python3 scripts/validate.py` — runs in ~0.1s on the whole repo. Checks description length, frontmatter integrity, registry JSON well-formedness, and registry path resolution. Exit code 0 (clean), 1 (FAIL), or 2 (WARN-only). The `scripts/validate.py` file currently sits uncommitted in the working tree — it's intended to mature through real-world use before being wired to CI.
- **Single-file description check**: see the `python3` snippet in the 1024-character section above.
- **Registry JSON well-formed**: `python3 -c "import json; json.load(open('skills/nexus/registry.json'))"` after every registry edit.
- **Skill file count vs. registry count**: `find skills -maxdepth 2 -name SKILL.md | wc -l` and `grep -c '^      "name":' skills/nexus/registry.json` (already printed by `sync.sh`).
- **Worker liveness after deploy**: `curl https://gvo-skills-mcp.lando555.workers.dev/health` — expects `{"status":"ok",...}`.

## Cross-environment gotchas

- **`setup.sh` refuses to run from a UNC path** (`//wsl$/...`, `\\wsl$\...`). It must run natively — WSL bash inside WSL, PowerShell on Windows (using `mklink /J`), bash on the VPS. Running Windows-bash against a WSL path creates broken symlinks.
- **Windows symlinks** are directory junctions, not POSIX symlinks. README documents `cmd /c mklink /J "C:\Users\Lando\.claude\skills" "C:\dev\gvo-skills\skills"`.
- **Line endings**: `.gitattributes` forces LF for `*.sh` / `*.bash` to prevent `bash\r` errors on WSL. Keep it that way.

## What NOT to do in this repo

| Don't | Do |
|---|---|
| Edit files inside `skills/awesome-claude-corporate-skills-main/` | Submit upstream or wrap in a new top-level skill |
| Add a skill without updating `skills/nexus/registry.json` | The registry IS the discovery surface — add an entry with triggers |
| Write skill descriptions over 1024 chars | Trim with ≥100 char headroom; use `description: >` for multi-line. Run `python3 scripts/validate.py` to confirm. |
| Skip `triggers` in new registry entries | Populate explicitly — empty triggers mean nexus won't match the skill |
| Run `setup.sh` from a UNC path | Run natively in each target environment |
| Commit `.claude/` | It's gitignored — per-checkout local config only |
| Resurrect the root `registry.json` | It was deleted on purpose; the nexus copy is canonical. Adding a second registry re-introduces drift. |
| Try to fix vendored corporate-bundle frontmatter errors | They're upstream — file an issue at hesreallyhim/awesome-claude-corporate-skills instead |
| Add build/test tooling unprompted to the repo root | The root is intentionally markdown+shell; `mcp-server/` is the one place TypeScript lives |
| `wrangler deploy` from `mcp-server/` while debugging locally | Push to `main` instead — Cloudflare Workers Builds runs the deploy, matching the canonical pipeline. Out-of-band `npm run deploy` masks builds-config bugs. |

## Nexus internals

Detailed runtime architecture (session enforcement, model lock, the seven-phase pipeline, anti-patterns) lives in `skills/nexus/CLAUDE.md`. Read that file before touching anything under `skills/nexus/` — it documents non-negotiable constraints (Opus 4.6 [1M] lock, `alwaysThinkingEnabled=true`, `MAX_THINKING_TOKENS=31999`, `/fast` blocked).
