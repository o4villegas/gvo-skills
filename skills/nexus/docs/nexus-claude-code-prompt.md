# Nexus Build Prompt — Claude Code Agent Instructions

> **You are building the Nexus unified skill orchestration system.**
> Read `nexus-unified-skill-system.md` and `nexus-SKILL.md` (provided alongside this file) for architecture context.
> You have direct access to all repos and files referenced below.

---

## Execution Order

Complete each step fully before moving to the next. Verify after each step.

---

### Step 1: Create Directory Structure

```bash
mkdir -p /home/lando555/.claude/skills/nexus/{pipeline,agents,skills,archive,references}
```

### Step 2: Install Master SKILL.md

Copy the provided `nexus-SKILL.md` to:
```
/home/lando555/.claude/skills/nexus/SKILL.md
```
This is the ONLY skill that auto-loads. Everything else is on-demand.

### Step 3: Migrate Existing Skills

List `~/.claude/skills/user/` and copy each skill directory into `nexus/skills/`:

```bash
# Copy all existing skills (preserve directory structure)
for skill_dir in /home/lando555/.claude/skills/user/*/; do
  skill_name=$(basename "$skill_dir")
  case "$skill_name" in
    skill-forge|skill-creator)
      # Archive superseded skills
      cp -r "$skill_dir" "/home/lando555/.claude/skills/nexus/archive/$skill_name"
      echo "ARCHIVED: $skill_name"
      ;;
    *)
      cp -r "$skill_dir" "/home/lando555/.claude/skills/nexus/skills/$skill_name"
      echo "MIGRATED: $skill_name"
      ;;
  esac
done
```

If `~/.claude/skills/user/` is empty on this machine (VPS), note that and continue — the skills will be migrated from the local WSL machine separately.

### Step 4: Extract Tier 1 Skills from Repos

Read each SKILL.md before copying — verify it exists and has proper frontmatter.

**From agentsys:**
```bash
SRC="/home/lando555/agentsys/.kiro/skills"
DST="/home/lando555/.claude/skills/nexus/skills"
for skill in debate consult orchestrate-review validate-delivery deslop repo-intel; do
  if [ -f "$SRC/$skill/SKILL.md" ]; then
    mkdir -p "$DST/$skill"
    cp "$SRC/$skill/SKILL.md" "$DST/$skill/"
    echo "INSTALLED: $skill (agentsys)"
  else
    echo "MISSING: $SRC/$skill/SKILL.md"
  fi
done
```

**NOTE on agentsys skills:** These are written for the agentsys multi-tool framework (Claude Code, Gemini CLI, Codex, etc.). Some reference `$ARGUMENTS`, `Task()`, `AskUserQuestion()`, and platform-specific state dirs. After copying, adapt each to work in our single-Claude-Code environment:
- Replace `Task({ subagent_type: ... })` references with direct execution
- Replace `$ARGUMENTS` with standard frontmatter trigger patterns
- Keep all the logic, patterns, templates — just remove the multi-tool dispatch layer
- The `consult` skill is the exception — keep its multi-tool capability intact since it's specifically for getting second opinions from other models

**From everything-claude-code:**
```bash
SRC="/home/lando555/everything-claude-code/skills"
DST="/home/lando555/.claude/skills/nexus/skills"
for skill in council blueprint verification-loop agentic-engineering search-first continuous-agent-loop; do
  if [ -f "$SRC/$skill/SKILL.md" ]; then
    mkdir -p "$DST/$skill"
    cp "$SRC/$skill/SKILL.md" "$DST/$skill/"
    echo "INSTALLED: $skill (ECC)"
  else
    echo "MISSING: $SRC/$skill/SKILL.md"
  fi
done
```

**From slavingia/skills:**
```bash
SRC="/home/lando555/skills/skills"
DST="/home/lando555/.claude/skills/nexus/skills"
for skill in validate-idea mvp pricing marketing-plan first-customers grow-sustainably; do
  if [ -f "$SRC/$skill/SKILL.md" ]; then
    mkdir -p "$DST/$skill"
    cp "$SRC/$skill/SKILL.md" "$DST/$skill/"
    echo "INSTALLED: $skill (slavingia)"
  fi
done
```

**From claude-skills:**
```bash
DST="/home/lando555/.claude/skills/nexus/skills"
# Engineering skills
for skill in focused-fix autoresearch-agent karpathy-coder codebase-onboarding; do
  SRC="/home/lando555/claude-skills/engineering/$skill"
  if [ -f "$SRC/SKILL.md" ]; then
    mkdir -p "$DST/$skill"
    cp "$SRC/SKILL.md" "$DST/$skill/"
    echo "INSTALLED: $skill (claude-skills/engineering)"
  fi
done
# Finance
for skill in financial-analyst saas-metrics-coach; do
  SRC="/home/lando555/claude-skills/finance/$skill"
  if [ -f "$SRC/SKILL.md" ]; then
    mkdir -p "$DST/$skill"
    cp "$SRC/SKILL.md" "$DST/$skill/"
    echo "INSTALLED: $skill (claude-skills/finance)"
  fi
done
```

### Step 5: Extract Tier 2 References

Copy these as reference docs (not executable skills):

```bash
REFS="/home/lando555/.claude/skills/nexus/references"

# From agentsys
for skill in drift-analysis enhance-prompts enhance-skills learn discover-tasks; do
  if [ -f "/home/lando555/agentsys/.kiro/skills/$skill/SKILL.md" ]; then
    cp "/home/lando555/agentsys/.kiro/skills/$skill/SKILL.md" "$REFS/${skill}.md"
    echo "REF: $skill"
  fi
done

# From everything-claude-code
for skill in coding-standards mcp-server-patterns tdd-workflow e2e-testing security-review; do
  if [ -f "/home/lando555/everything-claude-code/skills/$skill/SKILL.md" ]; then
    cp "/home/lando555/everything-claude-code/skills/$skill/SKILL.md" "$REFS/${skill}.md"
    echo "REF: $skill"
  fi
done
```

Also copy the existing prompt-rules if available:
```bash
cp /home/lando555/damage-suite/.claude/skills/prompt-rules.md "$REFS/" 2>/dev/null
```

### Step 6: Create Reference — Stack Conventions

Write `nexus/references/stack-conventions.md` documenting Lando's standard stack:
- CF Workers + Hono + D1 (Drizzle ORM) + R2 + KV
- React Router v7 + Tailwind + shadcn/ui
- Vitest (unit) + Playwright (e2e)
- wrangler.toml / wrangler.json patterns
- CLAUDE.md conventions from existing projects (read a few for patterns)
- Midnight glassmorphism aesthetic (cyan #00D6B4, violet #825AFF, amber #FF9F43 on #0A0D12)

Read CLAUDE.md files from 2-3 of Lando's projects (`service-planner`, `damage-suite`, `kc-cogs`) to extract recurring patterns.

### Step 7: Write Pipeline Phase Files

Create each file in `nexus/pipeline/`. Keep each under 150 lines. Be specific and actionable.

**01-interview.md** — Question templates, decision tree for "enough info?", examples of good questions for different project types (new app, enhancement, bug fix, research). Include the categories: What, Who, Where, Scale, Constraints, Existing work. Reference ask_user_input tool for claude.ai context.

**02-domain-check.md** — How to identify relevant domains. Skill loading protocol (read registry → match → load SKILL.md). Web search strategy. From-desktop codebase reading protocol. Source relevance check with user. Reference: `repo-intel` for codebase analysis, `search-first` for pattern discovery.

**03-plan-development.md** — Reference `council` skill for the four-voice pattern. Reference `blueprint` for multi-session plans. Reference `debate` for contentious decisions. Reference `agentic-engineering` for core principles (eval-first, 15-min decomposition, model routing). Define the plan output format: architecture, file structure, implementation sequence, test plan, risk register.

**04-approval.md** — Summary template. How to present architecture (use visualize tools in claude.ai, or ASCII in CLI). Risk communication. Rejection handling: return to Phase 3 with new constraints.

**05-implementation.md** — Reference `orchestrate-review` for parallel code review. Reference `deslop` for slop detection. Reference `verification-loop` for quality gates. Reference `continuous-agent-loop` for autonomous iteration. Define sequence: scaffold → core → polish → deslop → test → review → harden → iterate. Code quality rules: no TODOs, no placeholders, no commented-out code.

**06-pre-delivery.md** — How to present work. Enhancement suggestion format. When to run `ux-diagnostic`. Refactor protocol. Final verification pass.

**07-final-delivery.md** — Reference `validate-delivery` for autonomous validation. Quality checklist. Delivery format per environment (Claude Code vs claude.ai). Documentation requirements. Skill evolution recording via Worker API.

### Step 8: Write Agent Perspective Files

Create each in `nexus/agents/`. Keep under 100 lines each. These define the expert lens used during Phase 3 council.

**architect.md** — System design, data model, API surface. Lando's stack defaults and when to deviate. Module boundary rules. Scalability considerations.

**implementer.md** — Efficient implementation path. Dependency audit (prefer built-in over npm). Stack-specific gotchas: D1 has no transactions (use `.batch()`), Workers have no filesystem, Drizzle on D1 quirks. Code organization patterns from existing projects.

**ux-specialist.md** — 2026 design conventions. Lando's aesthetic (midnight glassmorphism). WCAG 2.2 AA minimum. Mobile-first default. Micro-interactions. Reference `ux-diagnostic` for audit methodology.

**qa-engineer.md** — Edge case identification. Security checklist (auth, validation, CORS, injection). Performance budgets. Chaos test patterns (from-billy personas). Reference `orchestrate-review` for multi-pass review methodology.

**domain-researcher.md** — Industry norm research strategy. Competitor analysis framework. How to use web search effectively. Source quality evaluation.

**lead.md** — Synthesis of multi-perspective input. User communication format. Approval presentation. Rejection handling. Status updates.

### Step 9: Build registry.json

Scan all skills in `nexus/skills/` and generate the registry:

```bash
cd /home/lando555/.claude/skills/nexus
```

For each skill directory, read SKILL.md, parse YAML frontmatter (between `---` markers), extract `name`, `description`, and trigger phrases (quoted strings in description). Generate entry:

```json
{
  "id": "{name}__imp_{random8hex}",
  "name": "{name}",
  "description": "{first 200 chars of description}",
  "path": "skills/{name}/SKILL.md",
  "category": "workflow",
  "tags": [],
  "triggers": ["extracted", "trigger", "phrases"],
  "isActive": true,
  "source": "{originating repo or 'existing'}"
}
```

Write the complete registry to `nexus/registry.json`.

### Step 10: Build & Deploy Skill Evolution Worker

Follow the complete spec in the uploaded `skill-evolution-prompt.md`. Implementation order:

1. `cd /home/lando555 && mkdir skill-evolution && cd skill-evolution`
2. `npm init -y && npm install hono drizzle-orm && npm install -D wrangler drizzle-kit @cloudflare/workers-types typescript`
3. Write Drizzle schema (`src/db/schema.ts`) — tables: skill_records, skill_lineage_parents, execution_analyses, skill_judgments, skill_tags
4. `npx wrangler d1 create skill-evolution` → copy ID to wrangler.toml
5. Write utility libs: skill-id, diff, snapshot, metrics
6. Write routes: skills, analyses, evolution, health
7. Write Hono app entry point
8. `npx drizzle-kit generate` → `npx wrangler d1 migrations apply skill-evolution`
9. `npx wrangler deploy`
10. Write companion SKILL.md → install to `nexus/skills/skill-evolution/`
11. Seed by reading all skills from nexus/skills/ and POSTing to `/skills/register`

### Step 11: Sync to Windows

```bash
rsync -av --delete \
  /home/lando555/.claude/skills/nexus/ \
  /mnt/c/Users/Lando/.claude/skills/nexus/
```

### Step 12: Verify

```bash
echo "=== Skills installed ==="
find /home/lando555/.claude/skills/nexus/skills -name "SKILL.md" | wc -l

echo "=== Registry ==="
python3 -c "import json; d=json.load(open('/home/lando555/.claude/skills/nexus/registry.json')); print(f'{len(d[\"skills\"])} skills registered')"

echo "=== Pipeline files ==="
ls /home/lando555/.claude/skills/nexus/pipeline/

echo "=== Agent files ==="
ls /home/lando555/.claude/skills/nexus/agents/

echo "=== Worker ==="
curl -s https://skill-evolution.lando555.workers.dev/dashboard | head -5

echo "=== Windows mirror ==="
test -f /mnt/c/Users/Lando/.claude/skills/nexus/SKILL.md && echo "OK" || echo "MISSING"
```

---

## Repo Deep-Dive Guidance

When extracting skills, READ these files first for each repo to understand conventions:

| Repo | Read First |
|------|-----------|
| agentsys | `CLAUDE.md`, `AGENTS.md`, `.kiro/skills/consult/SKILL.md` (most complex skill — shows full pattern) |
| everything-claude-code | `CLAUDE.md`, `AGENTS.md`, `skills/council/SKILL.md`, `skills/blueprint/SKILL.md` |
| claude-skills | `CLAUDE.md`, `CONVENTIONS.md`, `SKILL-AUTHORING-STANDARD.md`, `engineering/SKILL.md` (bundle entry) |
| slavingia/skills | `README.md` |
| OpenSpace | `openspace/skill_engine/store.py`, `openspace/skill_engine/evolver.py` (Worker port reference) |

## Anti-Patterns

| Do NOT | Do Instead |
|--------|------------|
| Load all skills on startup | Only nexus SKILL.md auto-loads; everything else on-demand via registry |
| Delete old skills during migration | Archive to nexus/archive/ |
| Copy non-English translations | Only copy from `skills/` or `.kiro/skills/` (English originals) |
| Copy all 726 skills | Only Tier 1 (33 skills) and Tier 2 (10 references) |
| Install agentsys skills without adapting | Remove multi-tool dispatch layer; keep logic and templates |
| Add to kc-actuals or kc-menu-1 databases | Use the new skill-evolution D1 database |
| Create a monorepo with service-planner | Skill-evolution is standalone at `/home/lando555/skill-evolution/` |
| Skip the registry.json generation | The master SKILL.md depends on it for on-demand loading |
| Write pipeline/agent files as vague prose | Be specific: reference exact skill names, exact patterns, exact thresholds |
