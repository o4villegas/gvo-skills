# Empirical Verification — Evidence Protocol

This file defines what counts as evidence, how the Auditor enforces it, and the format
of the verification matrix that ships with every delivery.

## The Core Rule

**No claim may stand in prose without command output backing it.**

A claim is any sentence that asserts a state of the world: "tests pass", "build
succeeds", "the file exists", "the function works", "no security issues found", "verified
in production", "ready to ship", "deploy succeeded", "all checks green", "complete",
"done", "fixed".

Backing means: a fenced code block immediately follows (or table cell adjacent) showing:
1. The exact command that was run
2. The literal output of that command (or relevant excerpt with line numbers)
3. A plain-English summary of what the output proves

Without all three, the claim is `[UNVERIFIED]` and must be tagged that way in the
delivery.

## What Counts as Evidence

| Evidence type | Example | Counts? |
|---------------|---------|---------|
| Literal command + output | `npm test` → `Tests: 47 passed, 47 total` | Yes |
| File read with cited line numbers | "src/auth.ts:42 returns null on missing token" | Yes |
| HTTP response with status code | `curl -s -o /dev/null -w "%{http_code}" https://...` → `200` | Yes |
| Git log / diff | `git log --stat HEAD~1..HEAD` showing 3 files changed | Yes |
| Build artifact hash | `sha256sum dist/worker.js` → `abc123...` | Yes |
| "I verified it" prose | (no command, no output) | NO |
| "It should work" prose | (speculation) | NO |
| "Looks good" prose | (subjective) | NO |
| "Tests pass" with no test output | (claim without backing) | NO |
| Output paraphrased / summarized | "the tests all passed" without `npm test` output | NO |

## Auditor Workflow

### 1. Receive Lead Deliverable

The Auditor receives the Lead's full deliverable, including the evidence section. It
parses every claim and the command/output backing it.

### 2. Re-Run Independently

The Auditor does NOT trust the Lead's transcript. It re-runs every command itself
through its own tool calls. If the Lead said "I ran `npm test` and got X", the Auditor
runs `npm test` itself and compares.

If the re-run output matches the Lead's claim → PASS.
If the re-run output differs → FAIL, with both outputs cited.
If the command can't be re-run (e.g., it needs production access the Auditor doesn't
have, or it's destructive and was a one-shot) → UNVERIFIED.

### 3. Produce the Matrix

```
| # | Claim                            | Lead   | Re-run command       | Auditor result   | Verdict    |
|---|----------------------------------|--------|----------------------|------------------|------------|
| 1 | "tests pass"                     | Test   | npm test             | 47/47 passed     | PASS       |
| 2 | "no type errors"                 | Build  | tsc --noEmit         | 0 errors         | PASS       |
| 3 | "deploy succeeded"               | Build  | wrangler deployments | 1 active deploy  | PASS       |
| 4 | "no security issues"             | Build  | (no command claimed) | n/a              | UNVERIFIED |
| 5 | "feature works in prod"          | Build  | curl https://prod/x  | 503 error        | FAIL       |
```

### 4. Report to Director (Parallel Chain)

The Auditor returns the matrix directly to the Director. The Lead does NOT see it before
the Director does. This prevents the Lead from rewriting failures before they reach
delivery.

## Verdict Handling

### PASS
- Lead's claim is verified
- Director includes the row in the final verification matrix surfaced to the user
- No further action

### FAIL
- Lead's claim does not match independent re-run
- Director returns the row to the Lead with the failing output
- Lead has up to 2 fix cycles to remedy
- After 2 failed fix cycles, halt: surface the failure trail to the user
- Do NOT silently retry past the limit — see hard rule §5 in SKILL.md

### UNVERIFIED
- No command exists to verify the claim, OR the command requires user/production access
  the Auditor lacks
- This is the ONLY trigger that breaks auto mode
- Director MUST surface to the user: "This claim cannot be verified — [reason]. Should I
  proceed assuming it's true, or do you want to verify it manually first?"
- If user says "proceed", continue and tag the claim `[UNVERIFIED]` in delivery
- If user says "verify first", stop and let them check

## Verification Matrix in Final Delivery

Every delivery (except `Class: quick`) includes the matrix. Format:

```
## Verification

| What was checked | How | Result |
|------------------|-----|--------|
| Tests pass       | `npm test` | 47/47 passed |
| Build succeeds   | `npm run build` | 0 errors, 142kb output |
| Deploy live      | `curl https://prod/health` | HTTP 200 |
```

For UNVERIFIED rows, add a note row beneath:

```
| Security review  | (no scanner run)            | [UNVERIFIED — see ledger A4] |
```

The user-facing summary that follows the matrix must say in plain English:
- What's PASS: "Three checks confirmed — your tests pass, the build is clean, and the
  live site responds healthy."
- What's FAIL or UNVERIFIED: "One check could not be confirmed: I didn't run a security
  scanner. If that matters, run [tool] yourself and let me know."

## Anti-Patterns (Direct Triggers for Failure)

These are common verification-theater patterns the Auditor must catch:

| Anti-pattern | Why it fails | Fix |
|--------------|--------------|-----|
| `✓ Tests pass` (checkmark only) | No command, no output | Show `npm test` + its output |
| "I verified the file exists" | "Verified" is the claim, no read shown | Cite `path:line` from a `Read` |
| "All systems green" | Generic, no per-system evidence | Per-system rows in matrix |
| "Should work" / "looks correct" | Speculation | Run a command that proves it |
| Tool-output evidence in tool calls but plain summary in prose | The user only sees prose | Mirror tool output into delivery in code blocks |
| Single command output covering multiple claims | Conflates evidence | One row per claim, even if same command |
| Lead summarizes own evidence ("our tests pass") | Self-reporting, not audited | Auditor re-runs and writes the row |

The user's CLAUDE.md (Trap #7 in the verification checklist) calls out this exact
problem. The verify-gate Stop hook on Claude Code Desktop fires on it. In claude.ai,
there is no such hook — the Auditor is the only line of defense.

## Confidence % vs Evidence

The user's CLAUDE.md mandates a confidence % on every non-trivial claim, plus a
"to raise confidence: ..." follow-up. This is separate from the verification matrix.

| Concept | Format | Example |
|---------|--------|---------|
| Verification | matrix row, command + output | `npm test → 47/47 passed | PASS` |
| Confidence | % + follow-up sentence | "Confidence: 92%. To raise: run `npm run check` end-to-end on a clean checkout." |

Both appear in the final delivery. Verification is binary (PASS/FAIL/UNVERIFIED).
Confidence is a dial that reflects what the matrix doesn't cover (assumptions, untested
edge cases, what the Auditor couldn't reach).

## Plain English Translation Rule

Inside code blocks and table cells: technical content is fine (commit hashes, command
names, file paths, library versions).

Outside code blocks and table cells: translate to plain English. The user's CLAUDE.md
provides the mapping table — it's the law for user-facing prose.

| Technical | Plain English |
|-----------|---------------|
| commit `d7433f8` | "the change we just made" |
| `npm audit` | "the security scanner" |
| `tsc --noEmit` | "the type checker" |
| GHSA-xxxx-xxxx | "the security warning" |
| `Cloudflare Workers` | "the Cloudflare service that runs the site" |
| `D1` | "the project's database" |

If a term has no good substitute, introduce it with a one-clause gloss the first time:
"the type checker (a tool that catches mismatches in how data flows through the code)".

## What the User Sees (End-to-End)

```
Result
------
Auth refactor is complete. The login endpoint now uses the new token format, and the
old format still works for in-flight sessions.

Verification
------------
| What was checked      | How                         | Result          |
|-----------------------|-----------------------------|-----------------|
| Tests pass            | `npm test`                  | 84/84 passed    |
| Type checker clean    | `tsc --noEmit`              | 0 errors        |
| Live login works      | `curl -X POST .../login`    | HTTP 200, token returned |
| Old token format      | `curl -H "X-Old-Token..."`  | HTTP 200 (compat) |

Three checks confirmed: tests pass, types are clean, both new and old logins work
against the live site.

Assumption Ledger
-----------------
| ID | Decision               | Confidence | Alternative |
|----|------------------------|------------|-------------|
| A1 | Kept old format alive  | High       | Hard cutover (would break in-flight sessions) |
| A2 | 7-day compat window    | Medium     | 30 days (safer but extends complexity) |
```

That's the shape. Everything inside the matrix and ledger uses technical terms freely.
The summary sentence above each section is plain English.
