# prompt-rules — Personal Prompt Writing Guide

> Extracted from 79 optimization rounds across 7 prompts (CLAUDE.md + 4 skills + test-hardening + billy-remediation).
> 79 kept, 0 reverted. Billy-remediation scored 96% at V0 with 0 optimization rounds.
> Apply these BEFORE writing any new skill or prompt. 2-minute checklist at bottom.

---

## Universal Rules (apply to EVERY skill/prompt)

### Rule 1: Verification is mechanical or it doesn't exist
Every quality standard must have a grep command, file count, threshold, or concrete test. "Ask yourself if..." is not verification. "Ensure quality..." is not verification.

**Evidence:** Every skill scored 5-7/10 on Verification until aspirational checks became grep commands. Average jump: +3.4 points per skill.

**Template:**
```
❌ "Every component should have a test"
✅ "Every component has a test. Verify: for each .tsx in src/components/, a corresponding .test.tsx exists."
```

### Rule 2: One skill, one domain, zero duplication
Each skill owns its unique content and points to others with one-liner cross-references. If the same information appears in two skills, agents read it twice and waste context window.

**Evidence:** Cutting duplication was the highest-ROI change. CLAUDE.md's design section went from 62→24 lines (-38) with zero information loss — just a table + skill pointer. Architecture skill dropped 23 lines of CLAUDE.md duplication in Round 1 and jumped +8 points.

**Template:**
```
❌ [Repeating the color tokens from CLAUDE.md]
✅ "Token values and hex codes are in CLAUDE.md. This skill adds the Tailwind class mapping and component usage patterns."
```

### Rule 3: Start with prerequisites and unique value
First section of every skill must answer: what to read before this, what this skill uniquely adds, and (if applicable) which skills to load for which task type.

**Evidence:** Every skill scored 7-8/10 on Objective Clarity until it got a prerequisites + routing section. Then 9-10. The task-to-skill routing table (from-damage-suite Round 5) was +2 points in one change.

**Template:**
```
## Prerequisites
Read `CLAUDE.md` first. Load `[other-skill].md` alongside this for [X patterns].

## What this skill adds that others don't:
- [Unique contribution 1]
- [Unique contribution 2]
```

### Rule 4: Anti-patterns name the alternative, not just the prohibition
"Don't use X" is half a rule. "Don't use X — use Y because Z" is a complete rule. Anti-patterns must be domain-specific, not generic boilerplate. Split into categories if the skill serves multiple domains.

**Evidence:** CLAUDE.md's Do Not section scored 5/10 when it was empty, 8/10 with generic Workers gotchas, and 10/10 when split into Platform + Architecture categories with alternatives. from-damage-suite's code-pattern anti-patterns scored 9→10 only after adding domain-specific items (async client components, barrel exports).

**Template:**
```
❌ "Don't use localStorage"
✅ "Don't use localStorage — use IndexedDB (via `idb`). localStorage is sync, 5MB max, unavailable in Workers."

❌ "Handle errors properly"
✅ "Don't return raw errors to the client — catch, log server-side, return structured { error: string } response."
```

### Rule 5: Code examples include the failure path
Happy-path-only examples score 6-7. Examples with try/catch, error recovery, and loading states push to 9-10. Every code pattern should show what happens when things go wrong.

**Evidence:** from-damage-suite scored 6/10 on Edge Case Coverage until error boundary, loading skeleton, and form validation patterns were added. damage-suite-data jumped +2 when `safeRunPodJob()` and `safeR2Upload()` wrappers with failure handling were added.

**Template:**
```
❌ const result = await client.submitJob(input)  // assume success

✅ try {
     const result = await client.submitJob(input)
     return result
   } catch (error) {
     console.error('[RunPod] Job failed:', error)
     return null  // Caller shows "processing pending" in UI
   }
```

### Rule 6: Tables beat prose for reference material
If agents need to look something up (color tokens, component specs, routing decisions, scoring scales), a table is always more scannable than paragraphs or code blocks. Tables compress information by 40-60% vs. equivalent prose.

**Evidence:** CLAUDE.md's design system went from 62 lines of CSS blocks to 24 lines with a token table. damage-suite-verify's "this not that" went from 65 lines of code blocks to a 5-row comparison table. Every conversion improved Signal-to-Noise by 1-2 points.

**Template:**
```
❌ ```css
   --ds-success: #22c55e;        /* Completed */
   --ds-success-subtle: #052e16; /* Badge background */
   ```

✅ | Semantic | Base class | Subtle class | Use |
   |----------|-----------|-------------|-----|
   | Success | `text-ds-success` | `bg-ds-success-subtle` | Completed, synced |
```

### Rule 7: Threshold everything
Replace "reasonable" with a number. Replace "should have" with a count. Replace "consistent" with a grep pattern. Vague standards can't be enforced.

**Evidence:** damage-suite-verify scored 8→9 on Requirements Specificity when "Bundle size is reasonable" became "no route chunk >250KB" and "No visual orphans" became "check headings at 375px width."

**Template:**
```
❌ "Bundle size should be reasonable"
✅ "Bundle size: npm run build output shows no individual route chunk >250KB."

❌ "Tests should cover edge cases"
✅ "Test coverage ratio: find src/components -name '*.tsx' | wc -l vs find . -name '*.test.tsx' | wc -l — ratio >0.5 minimum."
```

### Rule 8: Combined verify commands with && chaining
Multiple verification steps should be combined into one copy-pastable line with `&&` chaining. Agents copy-paste one-liners; they skip multi-step lists.

**Evidence:** CLAUDE.md's 6 individual verification commands (15 lines) became two copy-pastable one-liners (4 lines). Verification Coverage went from 8→10.

**Template:**
```
❌ # Step 1
   npx tsc --noEmit
   # Step 2
   npm run lint
   # Step 3  
   npm run test

✅ npx tsc --noEmit && npm run lint && npm run test && npm run build && echo "✅ All gates passed"
```

### Rule 9: Exhaustive file scope beats conceptual scope
List every file the agent WILL modify and every file it must NOT modify. Don't describe scope conceptually — enumerate it. Agents interpret "don't modify production code" creatively; they can't misinterpret a file list.

**Evidence:** Test-hardening R4 — adding exhaustive writable + untouchable file lists jumped Scope Boundary 8→10 and Do Not Quality 8→10 in one change (+4 total).

**Template:**
```
❌ "Only modify test files and config"
✅ "Files you WILL modify (exhaustive):
    - tests/unit/api/api-routes.test.ts — Phase 1
    - eslint.config.mjs — Phase 4
    Do NOT modify: auth-middleware.test.ts, auth-password.test.ts, ..."
```

### Rule 10: Regression guard — count before, count after, every phase
For any prompt that modifies existing files, require the agent to record a measurable baseline metric (test count, lint error count, TS error count) BEFORE each phase and verify it doesn't regress AFTER. Agents trust their own output; counting doesn't.

**Evidence:** Test-hardening R1 — adding the Regression Guard was the single largest score jump: Adversarial Review 6→9 (+3).

**Template:**
```
❌ "Run tests after each phase"
✅ "Before AND after every phase, record:
    npx vitest run 2>&1 | grep 'Tests'
    Rule: passing count must NEVER decrease between phases."
```

### Rule 11: Replace speculation with verified source flow
When describing component behavior, rendering flow, or data shape — read the actual source and describe what it does, not what it "probably" does. "Probably", "likely", "may not match" are optimization debt. Every speculative phrase is a -1 on Requirements Specificity.

**Evidence:** Test-hardening R2 — replacing speculative ReportList diagnosis with verified 6-step rendering flow jumped Requirements Specificity 7→9 and Context 9→10. Prior QA prompt passed at baseline because "all paths came from Read tool output — no guessing."

**Template:**
```
❌ "The component probably renders the button after data loads"
✅ "Verified rendering flow (from src/components/reports/ReportList.tsx):
    1. loading starts true → renders skeleton (lines 80-88)
    2. useEffect fires fetchReports()
    3. setLoading(false) in finally block
    4. If reports.length > 0 → 'Generate Report' button at line 120"
```

### Rule 12: Fix the root cause layer, not the symptom layer
When describing a bug fix, identify which architectural layer owns the root cause. The symptom and the fix are often in different layers. Agents default to fixing at the symptom layer — the prompt must name the correct layer AND explicitly prohibit the wrong-layer fix.

**Evidence:** Billy finding #1 — "3 routes return 404." Agent instinct: build 3 new `page.tsx` files (routing layer). Actual root cause: sidebar `navItems` arrays have wrong hrefs (navigation layer). The billy-remediation prompt had to say "Do NOT create new route pages — fix the navItems hrefs" twice. Without this, a 2-line fix becomes a 200-line wrong-layer solution.

**Template:**
```
❌ "Fix the 404 errors on /dashboard, /analysis, /settings"
✅ "The 404s are caused by sidebar navItems linking to routes with no page.tsx.
    Fix: update hrefs in DesktopSidebar.tsx:8-13 and MobileNav.tsx:8-12.
    Do NOT create new page.tsx files — the route groups are correct, the links are wrong."
```

### Rule 13: Remediation is closed scope — discovery is a separate phase
A remediation prompt fixes a known list of issues from an audit, test report, or chaos test. It does NOT include a "look for anything else" sweep. Discovery (finding new bugs) and remediation (fixing known bugs) have different risk profiles — combining them causes scope creep. If discovery is wanted, make it Phase 0, read-only: log findings but don't fix them until scoped.

**Evidence:** Billy-remediation was scoped to 9 verified findings. When asked "does this prompt also look for new bugs?" the answer was no — and that's correct. Adding a discovery sweep was offered as an opt-in Phase 0, not a default. The test-hardening agent stayed within scope because the file list was exhaustive (Rule 9) and the issues were enumerated.

**Template:**
```
❌ "Fix these 8 issues and also do a general quality sweep while you're in there"
✅ "Fix these 8 issues. Do NOT fix, refactor, or improve anything not listed.
    If you notice a new issue, log it to tasks/findings.md but do NOT fix it."
```

---

## Skill-Specific Rules

### Architecture skills (like from-damage-suite)
- **Include a server/client decision tree** for any React 19 / Next.js project. This was +2 points across two dimensions in a single change.
- **Show the platform binding access pattern** — how to get env vars, database connections, storage handles. This is the #1 runtime error agents hit.
- **Add pattern compliance bash checks** beyond the standard build gates — these catch architecture violations that compile fine but break the design.

### Design skills (like damage-suite-design)
- **Include both the token definition AND the Tailwind class mapping** — tokens alone aren't actionable.
- **Include setup instructions** (globals.css, tailwind.config.ts, font loading) — not just usage patterns.
- **Include a component cheat sheet table** — one row per component with key classes.
- **Include a scoring calibration** — what does a 5 vs 7 vs 9 look like, with examples.

### Verification skills (like damage-suite-verify)
- **Orchestrate other skills' verification commands** — be the conductor, not a standalone checklist.
- **Handle N/A dimensions** — not every task needs all scoring dimensions.
- **Include budget awareness** — agents running with `--max-budget-usd` need to know when to accept 85% and stop.

### Data skills (like damage-suite-data)
- **Include the DB access helper implementation** — without it, agents invent their own (wrong) pattern.
- **Include failure handling for every external service** — each gets a `safe*()` wrapper pattern.
- **Include the offline sync replay logic** — FIFO ordering, retry count, break-on-failure.

### Remediation prompts (like test-hardening, billy-remediation, QA audit)
- **Deep empirical recon before writing V0** — read every relevant source file, run every test, check every lint output. Prompts written after deep audits start at 80%+ and sometimes need 0 rounds.
- **Enumerate writable files exhaustively** — explicit file lists prevent drift.
- **Include regression guards with counting** — before/after metrics per phase.
- **Diagnose then fix for runtime issues** — mandate a diagnostic command BEFORE prescribing a fix.
- **Name the fix layer explicitly** — when the symptom and root cause are in different layers, say which layer to fix AND prohibit the wrong-layer fix.
- **Scope is the issue list, period** — new findings go to a log file for separate scoping.

---

## Rules 14-16 (added from Phase 12 findings)

### Rule 14: Verified signatures for every external interface
When a prompt references a function signature, type interface, or API contract — copy the exact definition from grep/source output. Do NOT write interfaces from memory. Fabricated interfaces are the #1 cause of compile failures in remediation prompts.

**Evidence:** Phase 12 cited `assessRoom(input: FDAMInput)` with a fabricated 8-field interface. The actual function was `analyzeFDAM` with a 7-field interface (different field names). Three verification rounds were needed to catch this. Cost of NOT verifying: agent compile failure + 30min backtrack.

**Template:**
```
❌ "Call assessRoom with the room data"
✅ "Call analyzeFDAM (fdam.ts L213). Verified signature:
    export function analyzeFDAM(input: FDAMInput): FDAMResult
    FDAMInput (L15-23): { zone, sootType, overallSeverity, odorLevel, isFireOrigin, roomSqFt, affectedSurfaces }"
```

### Rule 15: Reference implementations cite exact file + line range
When a working reference exists in another codebase, cite the specific file path and line range. Vague references ("look at SmokeScan") cause agents to search or guess. Precise references ("SmokeScan storage.ts:74-100") give the agent the exact pattern to study.

**Evidence:** Phase 12's R2→base64 fix was modeled on SmokeScan's `getImageAsBase64`. Citing the exact file+lines let the agent match the pattern on the first try without searching.

**Template:**
```
❌ "Reference SmokeScan for the RunPod pattern"
✅ "Reference: SmokeScan /home/lando555/smokescan/src/worker/services/storage.ts:74-100 (R2 → base64 via btoa + byte-by-byte)"
```

### Rule 16: Group tightly-coupled fixes into single phases
When fixes are interdependent (e.g., base64 conversion + payload format change + think-block stripping), group them into one phase with one STOP gate. Artificial separation creates windows where code is in an inconsistent state and individual phases can't be meaningfully tested.

**Evidence:** Phase 12 agent batched Phases A-C (all RunPod pipeline fixes) despite the prompt specifying them as separate phases with separate STOP gates. The agent's instinct was correct — testing base64 conversion without the payload format change is meaningless.

**Template:**
```
❌ Phase A: Add base64 helper → STOP → Phase B: Fix payload → STOP → Phase C: Strip think blocks → STOP
✅ Phase A: Fix RunPod pipeline (base64 + payload + think-blocks) → STOP
```

## 2-Minute Pre-Writing Checklist

Run through this BEFORE writing any new skill or prompt:

```
□  1. VERIFY:      Does every standard have a grep/count/threshold? (Rule 1)
□  2. DEDUP:       Does any content duplicate another skill? Cut it, add pointer. (Rule 2)
□  3. PREREQS:     Does the first section say what to read first + unique value? (Rule 3)
□  4. DO NOTS:     Are anti-patterns domain-specific with alternatives? (Rule 4)
□  5. FAILURES:    Do code examples show the error path, not just happy path? (Rule 5)
□  6. TABLES:      Can any prose/CSS block become a scannable table? (Rule 6)
□  7. THRESHOLDS:  Are there any vague words (reasonable, consistent, should)? (Rule 7)
□  8. ONE-LINER:   Can verification steps be &&-chained into one command? (Rule 8)
□  9. FILE SCOPE:  Are writable + read-only files enumerated explicitly? (Rule 9)
□ 10. REGRESSION:  Is there a before/after counting mandate for each phase? (Rule 10)
□ 11. SPECULATION: Did I read the source, or am I guessing? Kill every "probably". (Rule 11)
□ 12. FIX LAYER:   Does the prompt name which layer to fix AND block the wrong layer? (Rule 12)
□ 13. CLOSED SCOPE: Is the issue list exhaustive? No discovery unless Phase 0. (Rule 13)
```

If you can check all 13 before writing, the prompt starts at ~90%+ instead of ~68%.
Deep recon + full checklist = 0 optimization rounds needed (proven by billy-remediation: 96% at V0).

---

## Rule Applicability Matrix

| Rule | Universal | New Feature | Bug Fix | UI Polish | Audit/Remediation |
|------|:---------:|:-----------:|:-------:|:---------:|:-----------------:|
| 1. Mechanical verification | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2. No duplication | ✅ | ✅ | ✅ | ✅ | ✅ |
| 3. Prerequisites first | ✅ | ✅ | ✅ | ✅ | ✅ |
| 4. Alternatives in Do Nots | ✅ | ✅ | ✅ | ✅ | ✅ |
| 5. Failure path examples | ✅ | ✅ | ✅ | ○ | ○ |
| 6. Tables > prose | ✅ | ✅ | ○ | ✅ | ✅ |
| 7. Threshold everything | ✅ | ✅ | ✅ | ✅ | ✅ |
| 8. && chain verification | ✅ | ✅ | ✅ | ✅ | ✅ |
| 9. Exhaustive file scope | ○ | ○ | ✅ | ○ | **✅✅** |
| 10. Regression guard | ○ | ○ | ✅ | ○ | **✅✅** |
| 11. Kill speculation | ✅ | ✅ | **✅✅** | ✅ | **✅✅** |
| 12. Root cause layer | ○ | ○ | **✅✅** | ○ | **✅✅** |
| 13. Closed remediation scope | ○ | ○ | ✅ | ○ | **✅✅** |
| 14. Verified signatures | ○ | ○ | **✅✅** | ○ | **✅✅** |
| 15. Reference impl paths | ○ | ✅ | ✅ | ○ | ✅ |
| 16. Group coupled fixes | ○ | ○ | ✅ | ○ | **✅✅** |

✅ = applies, ✅✅ = critical for this category, ○ = nice-to-have

---

## Meta-insight: Why zero reverts across 79 rounds?

The 0/79 revert rate reveals that V0 failure modes are predictable and structural:

1. Mechanical verification missing (Rule 1)
2. Domain-specific anti-patterns missing (Rule 4)
3. Skill hierarchy / cross-references missing (Rules 2-3)
4. Failure path coverage missing (Rule 5)
5. Deduplication discipline missing (Rule 2)
6. Scope enumeration missing (Rule 9)
7. Regression counting missing (Rule 10)
8. Speculation instead of source-reading (Rule 11)
9. Wrong-layer fix not blocked (Rule 12)
10. Open-ended scope inviting drift (Rule 13)

These 10 structural gaps explain ~95% of all optimization rounds.

**The 0-round proof:** Billy-remediation (prompt #10) applied all 13 rules before writing V0. Result: 96% score, 0 optimization rounds, 0 reverts. Compare to test-hardening (prompt #9), which applied rules AFTER writing V0: 79% baseline, 6 rounds needed to reach 96%. Same author, same codebase, same day — the only difference was when the rules were applied.

**The formula:** Deep recon (read every relevant source file) + 13-rule checklist (applied before writing, not after) = V0 that needs no optimization. Time invested in recon pays back 5-10× in rounds saved. The optimization loop exists for prompts written without the checklist — it's the safety net, not the process.
