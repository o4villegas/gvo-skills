# Phase 7 — Final Delivery

**Goal:** Autonomous validation, environment-specific delivery, documentation updates, and skill-evolution recording. The user should be able to use the deliverable immediately with zero follow-up questions.

## Skills to load

| Skill | Role |
|-------|------|
| `validate-delivery` | Autonomous validation of requirements met, tests pass, no regressions |
| `verification-loop` | Final pre-push gate (redundant with Phase 6 but cheap) |

## Validation — autonomous

Run `validate-delivery` against the Phase 1 spec and Phase 4 plan. Must verify **empirically**:

- [ ] All committed features work at runtime (open, click, submit — don't trust code)
- [ ] All tests pass (`npm test` green)
- [ ] Build succeeds (`npm run build`)
- [ ] No TypeScript errors (`npx tsc -b --noEmit`)
- [ ] No lint errors (`npm run lint`)
- [ ] No console errors in the dev server
- [ ] No uncaught network errors in the browser devtools
- [ ] Error handling: 500/timeout/empty states render gracefully
- [ ] Responsive (if UI): 320 / 375 / 768 / 1440 all render correctly
- [ ] Accessibility (if UI): keyboard navigation works, focus visible, contrast OK
- [ ] Deployed (if applicable): production URL responds 200 on primary route
- [ ] Docs updated: README, CLAUDE.md, any changelog

Any failure → return to Phase 5 step 7. Do not ship with unchecked items.

## Delivery by environment

### Claude Code CLI (local repo, CF Workers)

```bash
# 1. Verification gate (redundant but cheap insurance)
npx tsc -b --noEmit && npm run lint && npm test && npm run build && echo "OK"

# 2. Commit anything dangling
git add <files>
git commit -m "<type>: <description>"

# 3. Push — triggers Cloudflare auto-build and deploy
git push origin main
```

**Never use `wrangler deploy` as the primary path.** `git push` with CF Git integration is the canonical deploy for Lando's projects.

After push, check Cloudflare dashboard or build logs to confirm the deploy succeeded. Report the production URL back to the user.

### claude.ai with Canvas/Artifacts

- Write all deliverable files to `/mnt/user-data/outputs/`
- Use relative paths inside (not `/mnt/...` in the code itself)
- Include a `README.md` in the output bundle explaining how to run locally
- Reference the files in chat by path, then describe what the user should click first

### API-only / script

- Output the script, a one-line invocation example, and 2–3 sample runs showing expected output
- Cover success + at least one error case

## Delivery format

Present in this exact order:

```markdown
## Done — [task name]

**What shipped:** [1 sentence]

**Where it lives:**
- Repo: [path or URL]
- Deployed: [production URL or "local only"]
- Files created: [count]
- Lines of code: [±]

**How to use it:** [1-3 steps]

**Verified:**
- ✅ All tests passing ([count])
- ✅ Build green
- ✅ [domain-specific: e.g., "CSV import + 3 sample records succeed"]
- ✅ Deployed to [URL] at [timestamp]

**Known limitations:**
- [if any — better to surface than hide]

**Next steps (optional):**
- [1–3 suggestions for future work, only if user asked for them]
```

## Skill evolution recording

After delivery, record a task analysis to the skill-evolution Worker:

```bash
curl -X POST https://skill-evolution.lando555.workers.dev/analyses \
  -H "Content-Type: application/json" \
  -d '{
    "taskId": "<uuid>",
    "taskCompleted": true,
    "skillJudgments": [
      {"skillId": "council", "skillApplied": true, "note": "Used for Phase 3 planning"},
      {"skillId": "verification-loop", "skillApplied": true, "note": "All gates passed"},
      {"skillId": "ux-diagnostic", "skillApplied": false, "note": "No UI surface"}
    ]
  }'
```

Only record skills you actually invoked. Honesty matters — the Worker uses these judgments to evolve skill priorities over time.

**If the Worker URL 404s** (Step 10 not yet deployed), skip the recording silently. Don't fail the delivery over observability.

## Documentation updates

| File | Update when |
|------|-------------|
| `README.md` | New features, new commands, new env vars |
| `CLAUDE.md` | Architectural decisions, new patterns, new "Do not" entries |
| `CHANGELOG.md` | Every delivery (conventional-commits format) |
| `.env.example` | New secrets |

Do not write docs the user didn't ask for. But **do** update the ones that lie if you changed underlying behavior.

## Anti-patterns

| Do NOT | Do instead |
|--------|------------|
| Declare "done" without running the validation checklist | Run it. Every box. |
| Use `wrangler deploy` as the main deploy path | `git push origin main` |
| Silently skip items you couldn't verify | Flag them in "Known limitations" |
| Skip the skill evolution recording | Record it — the data is the point |
| Push with a red test suite | Fix, then push |
| Add "closing thoughts" or self-congratulation | Deliver terse, factual completion |

## Handoff back to user

Phase 7 ends when the user has the deliverable in their hands and the validation checklist is 100% green. Await the next request.
