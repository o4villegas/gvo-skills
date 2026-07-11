# State directory & pipeline memory

Everything the pipeline learns and decides is written to `.fable-flow/` in the **target repo**
(the repo the pipeline is operating on — not the gvo-skills repo). Add `.fable-flow/` to the target
repo's `.git/info/exclude` at Phase 0 (a local ignore — never edit the tracked `.gitignore`), so it
never shows up in the user's diffs. This directory is the audit trail (every claim in the final
summary traces to a file here) and the resume mechanism (stage entry points read whatever exists).

```
.fable-flow/
├── task.md                       task, flags, slug, base SHA, timestamp, resolved decisions
├── explore-structure.md          scout digests (one per lens)
├── explore-conventions.md
├── explore-blast-radius.md
├── plan-v0.md                    the architect's raw plan (pre-hardening fallback)
├── plan.md                       the hardened plan after the Phase-4 scoring loop
├── plan-rounds/round-NNN.json    one file per plan-hardening round (item, change, scores, keep/revert)
├── track-<n>-report.md           implementer reports (branch, commit, test evidence)
├── review-round-<r>-<lens>.md    reviewer reports
├── iterations/<n>-<slug>.md      iterate records (bug, repro evidence, root cause, fix, tests)
└── memory/lessons/<slug>.md      cross-run lessons — read at Phase 0, written at Phase 7 and by iterate
```

## Memory protocol (this pipeline's own surface, per Fable's "give it a memory surface")

This is a **separate, per-repo lessons surface** — deliberately not entangled with the three memory
systems documented in the global CLAUDE.md (homunculus, claude-mem, file-based auto-memory). It is
local to the target repo and git-ignored, so lessons never leave the machine.

- **Read at Phase 0.** If `.fable-flow/memory/lessons/` exists, read each file (the first line is
  its one-line summary) and carry the relevant lessons **inline** into the architect, implementer,
  and reviewer prompts — worktree subagents cannot read `.fable-flow/` themselves, so injection is
  the only way lessons reach them.
- **Write at Phase 7 (Remember) and after every Iterate.** Store one lesson per file with a
  one-line summary at the top. Record corrections and confirmed approaches alike, including why they
  mattered. Don't save what the repo or chat history already records; update an existing note rather
  than creating a duplicate; delete notes that turn out to be wrong.
- **Instance vs lesson.** The *instance* (a specific bug and its fix) lives in an iteration record
  under `iterations/`. The *lesson* (what stops the next run repeating it) lives under
  `memory/lessons/`. Keep them distinct.
- **Promoting to the team.** To share a hard-won lesson with collaborators, copy the stable ones
  into the target repo's tracked `CLAUDE.md` (all agents read that natively) and delete the local
  copies. To reset a repo's pipeline memory, delete `.fable-flow/memory/`.

## Resume

Because every phase writes here, the pipeline resumes from any stage by reading what exists. If a
run fails partway, the orchestrator reports which files are present and which stage re-entry phrase
picks up from there (see the SKILL's stage entry table). Do not silently re-run completed phases —
read their artifacts first.
