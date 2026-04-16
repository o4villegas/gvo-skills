# Nexus — Unified Skill Orchestration System

> **Target:** `/home/lando555/.claude/skills/nexus/`
> **Mirror:** `/mnt/c/Users/Lando/.claude/skills/nexus/`
> **Worker:** `skill-evolution.lando555.workers.dev` → repo `/home/lando555/skill-evolution/`
> **Worker spec:** Uploaded separately as `skill-evolution-prompt.md`

---

## Directory Structure to Create

```
~/.claude/skills/nexus/
├── SKILL.md                          # Master orchestrator (auto-loads every session)
├── registry.json                     # Lightweight skill index for on-demand loading
├── pipeline/                         # Phase instructions (loaded per-phase)
│   ├── 01-interview.md
│   ├── 02-domain-check.md
│   ├── 03-plan-development.md
│   ├── 04-approval.md
│   ├── 05-implementation.md
│   ├── 06-pre-delivery.md
│   └── 07-final-delivery.md
├── agents/                           # Expert perspective definitions
│   ├── architect.md
│   ├── implementer.md
│   ├── ux-specialist.md
│   ├── qa-engineer.md
│   ├── domain-researcher.md
│   └── lead.md
├── skills/                           # All on-demand skills (see Sources below)
├── archive/                          # Superseded skills (skill-forge, skill-creator)
└── references/                       # Non-executable pattern docs
```

## Source Repos (all at `/home/lando555/`)

Read these directly — do NOT rely on summaries. Every repo is cloned and ready.

| Repo | Path | Skill Location | Count |
|------|------|---------------|-------|
| agentsys | `/home/lando555/agentsys/` | `.kiro/skills/*/SKILL.md` | 30 |
| everything-claude-code | `/home/lando555/everything-claude-code/` | `skills/*/SKILL.md` (English originals only) | 183 |
| slavingia/skills | `/home/lando555/skills/` | `skills/*/SKILL.md` | 10 |
| claude-skills | `/home/lando555/claude-skills/` | `engineering/*/SKILL.md`, `c-level-advisor/*/SKILL.md`, `marketing-skill/*/SKILL.md`, `product-team/*/SKILL.md`, `finance/*/SKILL.md`, `project-management/*/SKILL.md`, `business-growth/*/SKILL.md` | 239 |
| OpenSpace | `/home/lando555/OpenSpace/` | `openspace/skill_engine/` (Python reference for Worker port) | — |
| claw-code | `/home/lando555/claw-code/` | No SKILL.md files — Rust Claude Code alt, reference only | 0 |

Also read: `CLAUDE.md`, `AGENTS.md` at each repo root for architecture context.

## Existing Lando Skills to Migrate

Source: `~/.claude/skills/user/` on WSL. List the directory — migrate everything except skill-forge and skill-creator (archive those). Known skills from prior work:

from-desktop, from-prompter, from-kc-records, from-billy, kc-pulse, ux-diagnostic, financial-data-translator, from-aristotle, review-hunter, skill-evolution (if exists)

## Skills to Extract from Repos

### Tier 1 — Install directly into `nexus/skills/`

From **agentsys** `.kiro/skills/`:
- `debate` — Multi-round adversarial debates. Phase 3 roundtable.
- `consult` — Cross-tool AI consultation. Multi-model second opinions.
- `orchestrate-review` — Parallel multi-pass code review with iteration loop. Phase 5.
- `validate-delivery` — Autonomous delivery validation (tests, build, reqs, regressions). Phase 7.
- `deslop` — AI slop detection and removal. Phase 5 polish.
- `repo-intel` — Git history + AST analysis. Phase 2 domain check.

From **everything-claude-code** `skills/`:
- `council` — Four-voice decision council (Architect, Skeptic, Pragmatist, Critic). Phase 3.
- `blueprint` — Multi-session project planner with cold-start context briefs. Phase 3.
- `verification-loop` — Build/type/lint/test/security verification. Phase 5/7.
- `agentic-engineering` — Eval-first execution + model routing philosophy. Core.
- `search-first` — Search codebase before writing. Phase 2.
- `continuous-agent-loop` — Autonomous build/verify/iterate. Phase 5.

From **slavingia/skills** `skills/`:
- `validate-idea`, `mvp`, `pricing` — Business/startup skills for GVO work.

From **claude-skills** `engineering/`:
- `focused-fix` — Targeted bug fixing. Phase 5 quick path.
- `autoresearch-agent` — Autonomous research loops. Enhances from-prompter.
- `karpathy-coder` — Karpathy-style methodical coding.

### Tier 2 — Extract to `nexus/references/`

From agentsys: `drift-analysis`, `enhance-prompts`, `enhance-skills`, `learn`, `discover-tasks`
From ECC: `coding-standards`, `mcp-server-patterns`, `tdd-workflow`, `e2e-testing`, `security-review`

### Skip

- All non-English translations (docs/zh-CN/, docs/ko-KR/, docs/zh-TW/, docs/tr/, docs/ja-JP/)
- OpenSpace gdpval_bench skills (benchmark artifacts)
- Language-specific skills not in Lando's stack (Go, Rust, Python, Swift, Kotlin, Java, C++, Perl, Django, Laravel, Spring Boot, Flutter, etc.)
- Enterprise ops (Jira, Confluence, Terraform, Helm, K8s)
- Healthcare/regulatory, supply chain, crypto/DeFi

## Pipeline ↔ Skill Mapping

| Phase | Skills to Load | When |
|-------|---------------|------|
| 1. Interview | nexus SKILL.md (built-in) | Always |
| 2. Domain Check | repo-intel, search-first, from-desktop | New build / enhancement |
| 3. Plan Development | council, blueprint, debate | New build |
| 4. Approval | nexus SKILL.md (built-in) | Always |
| 5. Implementation | orchestrate-review, deslop, verification-loop, continuous-agent-loop, from-billy | All builds |
| 6. Pre-Delivery | ux-diagnostic, verification-loop | Builds with UI |
| 7. Final Delivery | validate-delivery | All builds |
| Bug fix | focused-fix → verification-loop → validate-delivery | Direct to Phase 5 |
| KC task | from-kc-records, kc-pulse, financial-data-translator | Domain-specific |
| Skill mgmt | skill-evolution Worker API | Direct |
| Prompt work | from-prompter, autoresearch-agent | Direct |

## Lando's Stack Defaults

CF Workers + Hono + D1 (Drizzle ORM) + R2 + KV | React Router v7 + Tailwind + shadcn/ui | Vitest + Playwright | `wrangler deploy`

## registry.json Format

```json
{
  "version": 1,
  "updated": "ISO-8601",
  "skills": [
    {
      "id": "council__imp_a1b2c3d4",
      "name": "council",
      "description": "Four-voice decision council...",
      "path": "skills/council/SKILL.md",
      "category": "workflow",
      "tags": ["planning", "decision", "multi-perspective"],
      "triggers": ["council", "second opinion", "multiple perspectives", "tradeoff"],
      "isActive": true,
      "source": "everything-claude-code"
    }
  ]
}
```

Generate `id` as `{name}__imp_{random8hex}`. Parse `description` and `triggers` from each SKILL.md frontmatter. Set `source` to the originating repo.
