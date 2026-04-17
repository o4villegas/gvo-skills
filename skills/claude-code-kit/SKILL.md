---
name: claude-code-kit
description: >
  Boris Cherny's Claude Code best-practices kit — 6 slash commands (verify, commit-push-pr,
  fix-errors, pr-feedback, new-feature, review), 4 subagents (build-validator, code-architect,
  code-simplifier, verify-app), and project templates (CLAUDE.md, settings.json, hooks.json).
  Use when bootstrapping a new project with Claude Code conventions, or when you need
  lightweight slash commands for common inner-loop workflows (typecheck/lint/test, commit+PR,
  error fixing, code review, PR feedback). Trigger on "verify", "commit push pr",
  "fix errors", "pr feedback", "new feature plan", "code review", "simplify code",
  "validate build", "verify app", "scaffold claude code", "claude code template".
---

# claude-code-kit

Portable Claude Code conventions lifted from Boris Cherny's workflow. This skill is a
reference library, not an executable pipeline — you pick the piece you need.

## What's here

```
claude-code-kit/
├── commands/                   # Slash-command templates
│   ├── verify.md              # typecheck → lint → test → build
│   ├── commit-push-pr.md      # conventional commit → push → gh pr create
│   ├── fix-errors.md          # autofix typecheck/lint/test failures
│   ├── pr-feedback.md         # handle PR comments + update CLAUDE.md
│   ├── new-feature.md         # 4-phase feature flow (plan→build→verify→cleanup)
│   └── review.md              # structured code review output
├── agents/                     # Subagent prompts
│   ├── build-validator.md     # validates production build output
│   ├── code-architect.md      # planning agent — emits implementation plan
│   ├── code-simplifier.md     # reduces complexity without changing behavior
│   └── verify-app.md          # end-to-end verification checklist
└── templates/
    ├── CLAUDE.md.template            # project CLAUDE.md starter
    ├── project-settings.example.json # .claude/settings.json (bun stack)
    └── project-hooks.example.json    # .claude/hooks.json (auto-format on Write|Edit)
```

## When to use

Reach for this skill when:
- **Starting a new project** — copy `templates/CLAUDE.md.template` to the repo root and fill in stack-specific sections.
- **Missing a slash command** — copy the relevant file from `commands/` into the project's `.claude/commands/` directory.
- **Want a lightweight subagent** — the four agents here are smaller and more focused than orchestration skills like `apex` or `verification-loop`. Use them when you just need one narrow capability (simplify a file, validate a build) without spinning up a full pipeline.

## How commands and agents differ from existing gvo-skills

| Need | Use this kit | Use the heavier skill |
|---|---|---|
| One-off verify run | `commands/verify.md` | — |
| Full delivery gate | — | `verification-loop`, `apex` |
| Plan a feature lightly | `agents/code-architect.md` | — |
| Plan a multi-session build | — | `conductor`, `blueprint`, `full-stack-orchestration` |
| Clean up after Claude | `agents/code-simplifier.md` | `simplify` (ECC plugin) |
| Build output sanity | `agents/build-validator.md` | `verification-loop` |

Pick the kit for light, per-project conventions. Pick the heavier skills for multi-phase orchestration.

## Stack notes

The templates assume **bun** as the package manager (`bun run typecheck`, `bun run lint`, etc.).
If the target project uses npm/pnpm/yarn, search-and-replace `bun run` in whichever files you copy.

## Provenance

Curated by Boris Cherny (creator of Claude Code). Original content lived at `~/claude-code-kit/`
(untracked local scratch) and was consolidated into this gvo-skills skill on 2026-04-17.
See `README.md` for Boris's nine-point workflow philosophy.
