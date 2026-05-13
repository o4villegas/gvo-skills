# gvo-skills

Centralized Claude Code skill library. Single source of truth across all environments.

## Environments

| Environment | Clone Location | Skills Symlink |
|-------------|---------------|----------------|
| WSL (CLI) | `~/gvo-skills` | `~/.claude/skills -> ~/gvo-skills/skills` |
| Windows (Desktop) | `C:\dev\gvo-skills` | `C:\Users\Lando\.claude\skills -> C:\dev\gvo-skills\skills` |
| VPS | `~/gvo-skills` | `~/.claude/skills -> ~/gvo-skills/skills` |

## Setup (per environment)

```bash
git clone git@github.com:o4villegas/gvo-skills.git ~/gvo-skills
cd ~/gvo-skills
chmod +x setup.sh sync.sh
./setup.sh
```

## Daily sync

```bash
~/gvo-skills/sync.sh
```

## Structure

```
gvo-skills/
├── skills/                       # All skill directories
│   ├── nexus/                    # Orchestrator + bundled sub-skills + canonical registry
│   │   └── registry.json         # Canonical skill index (single source of truth)
│   ├── gvo-router/               # claude.ai cloud entry-point router (3-tier org + Auditor)
│   ├── gvo-router-cc/            # Claude Code port of gvo-router
│   ├── from-prompter/            # Prompt engineering
│   ├── pdf/                      # PDF processing
│   ├── ...                       # All other skills
│   └── review-hunter/            # Review aggregation
├── mcp-server/                   # Cloudflare Worker exposing this repo to claude.ai over MCP
├── scripts/
│   ├── validate.py               # Pre-commit gate (description cap, frontmatter, registry)
│   ├── sync-bundle-registry.py   # Curated bundle import tool
│   └── probe-mcp-sse.sh          # Production probe for the gvo-skills-mcp Worker
├── setup.sh                      # First-time symlink setup
├── sync.sh                       # Pull + verify
└── .gitignore
```

For deep guidance (mcp-server architecture, skill conventions, validation, cross-env
gotchas) read `CLAUDE.md` at the repo root.

## Adding a new skill

1. Create `skills/<name>/SKILL.md` with `name:` and `description:` frontmatter (keep
   the description under 1024 chars; aim for ≤900 for headroom)
2. Add entry to `skills/nexus/registry.json` (the canonical registry)
3. Run `python3 scripts/validate.py` to catch description-cap and frontmatter issues
4. Commit and push
5. Run `sync.sh` on other environments

## Windows setup (PowerShell as Admin)

```powershell
cd C:\dev
git clone git@github.com:o4villegas/gvo-skills.git
# Create directory junction (works without admin for dirs)
cmd /c mklink /J "C:\Users\Lando\.claude\skills" "C:\dev\gvo-skills\skills"
```
