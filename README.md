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
├── skills/              # All skill directories
│   ├── nexus/           # Orchestrator + bundled sub-skills + registry
│   ├── from-prompter/   # Prompt engineering
│   ├── pdf/             # PDF processing
│   ├── ...              # All other skills
│   └── review-hunter/   # Code review hunter
├── registry.json        # Nexus skill index (root copy)
├── setup.sh             # First-time symlink setup
├── sync.sh              # Pull + verify
└── .gitignore
```

## Adding a new skill

1. Create `skills/<name>/SKILL.md`
2. Add entry to `registry.json` (and `skills/nexus/registry.json`)
3. Commit and push
4. Run `sync.sh` on other environments

## Windows setup (PowerShell as Admin)

```powershell
cd C:\dev
git clone git@github.com:o4villegas/gvo-skills.git
# Create directory junction (works without admin for dirs)
cmd /c mklink /J "C:\Users\Lando\.claude\skills" "C:\dev\gvo-skills\skills"
```
