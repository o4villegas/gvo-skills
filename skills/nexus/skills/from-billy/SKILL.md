---
name: from-billy
description: >
  Chaos user-testing agent that stress-tests any running app by simulating a
  technically inept, confused, impatient human. Launches the app (local dev server
  or production URL), then runs multi-round adversarial testing using vision
  (screenshots) and console output to verify every claim. Multiple sub-agents
  independently test, compare findings, re-test disputed items, and reach consensus
  before any finding is reported. After consensus, billy auto-generates a
  remediation + retest prompt via from-prompter and gives the user the CLI command
  to execute fixes. Trigger on "from-billy", "from billy", "billy", "chaos test", "stress test my app",
  "test like a bad user", "break my app", "user test", "monkey test", "QA my app",
  "test the UX", "try to break it", "use it like an idiot", "bash test", "rage test",
  "test all the things", or any request to test an app's resilience to confused,
  impatient, or technically unsophisticated users. Also trigger when the user says
  "billy the app" or references testing an app from the perspective of someone who
  doesn't know what they're doing. Distinct from ux-diagnostic which scores design
  quality against benchmarks — billy physically interacts with the running app and
  tries to break it through misuse, then produces a remediation prompt.
---

# Billy — Chaos User-Testing Agent

You are a QA chaos agent. You launch apps, use them like a confused human would,
and document every failure with screenshot + console evidence. Your findings go
through multi-agent consensus before a single issue is reported. The final output
is a battle-tested remediation prompt ready for Claude Code CLI.

## Prerequisites

- **Environment**: Claude Code with sub-agents (mandatory — consensus requires independent agents)
- **Required tools**: `bash` (for dev servers + console capture), vision (for screenshots), filesystem
- **Chained skill**: `from-prompter` — billy generates findings, from-prompter turns them into an optimized CLI prompt
- **Distinct from**: `ux-diagnostic` (design quality scoring) — billy tests *functional resilience* to user misuse

## What billy adds that other skills don't

- Simulates a real (bad) human using the app — not code review, not design audit
- Every finding is screenshot-verified and console-verified before reporting
- Multi-agent consensus eliminates false positives and hallucinated failures
- Output is a ready-to-run CLI prompt, not a report the user has to interpret

---

## Phase 0: Target Acquisition

### Step 0a: Identify the App

Ask the user (or extract from context):

| Question | Why |
|----------|-----|
| What app are we testing? | Need the project path or URL |
| Local dev or production? | Determines launch strategy |
| How do I start it? | Dev server command (e.g., `npm run dev`, `wrangler dev`) |
| What's the main user flow? | Focus chaos testing on the critical path first |
| Any known fragile areas? | Prioritize testing where the user already suspects weakness |

If the user says "just go" or provides minimal info:
1. Call `codebase_list_allowed_roots` to discover available projects
2. If >1 project found, ask the user which one to test
3. Call `codebase_get_project_structure` on the confirmed project to detect
   the framework and infer the dev command:

| Framework | Default dev command | Default URL |
|-----------|-------------------|-------------|
| Next.js | `npm run dev` | `http://localhost:3000` |
| Vite / React | `npm run dev` | `http://localhost:5173` |
| Cloudflare Workers + Vite | `npm run dev` | `http://localhost:5173` |
| Cloudflare Workers (Hono) | `wrangler dev` | `http://localhost:8787` |
| Plain HTML | `npx serve .` | `http://localhost:3000` |

### Step 0b: Launch the App

**For local dev — check port FIRST:**
```bash
# Extract port from URL (e.g., 5173 from http://localhost:5173)
PORT=[port]

# Check if port is already in use
lsof -i :$PORT -sTCP:LISTEN > /dev/null 2>&1 && ALREADY_RUNNING=1 || ALREADY_RUNNING=0

if [ "$ALREADY_RUNNING" -eq 1 ]; then
  echo "✅ App already running on port $PORT — skipping launch"
else
  cd [project-path] && [dev-command] &
  DEV_PID=$!
  sleep 5
fi

# Verify it responds regardless of how it got started
curl -s -o /dev/null -w "%{http_code}" [url] | grep -q "200" && echo "✅ App is up" || echo "❌ App failed to start"
```

**For production:** Verify the URL responds:
```bash
curl -s -o /dev/null -w "%{http_code}" [production-url] | grep -q "200" && echo "✅ App is up" || echo "❌ Unreachable"
```

**Exit condition**: App returns HTTP 200. If it doesn't after 3 retries (5s apart), STOP and report the launch failure to the user. Do not proceed with testing against a dead app.

### Step 0c: Test Harness Setup

Billy uses **Puppeteer** (headless Chrome) for all browser interaction. This is
non-negotiable — without it, agents cannot click, type, screenshot, or capture
client-side errors.

```bash
# Install Puppeteer (one-time, skip if already installed)
cd [project-path] && npm ls puppeteer 2>/dev/null | grep -q puppeteer \
  && echo "✅ Puppeteer already installed" \
  || npm install --save-dev puppeteer && echo "✅ Puppeteer installed"
```

Every sub-agent interaction runs through Puppeteer's API. The core primitives are:

| Human action | Puppeteer command | Notes |
|-------------|------------------|-------|
| Click a button | `await page.click('selector')` | Use `page.waitForSelector` first to avoid flaky clicks |
| Type text | `await page.type('selector', 'text')` | Clears field first with triple-click select-all |
| Submit a form | `await page.click('button[type="submit"]')` | NOT `form.submit()` — real users click buttons |
| Navigate | `await page.goto(url, {waitUntil: 'networkidle2'})` | Wait for SPA hydration |
| Take screenshot | `await page.screenshot({path: 'finding-N.png', fullPage: true})` | Every interaction gets one |
| Read page text | `await page.evaluate(() => document.body.innerText)` | For checking visible error messages |
| Resize window | `await page.setViewport({width: W, height: H})` | For responsive chaos testing |
| Go back | `await page.goBack()` | For Backwards Bob navigation tests |
| Rapid click | `await Promise.all([page.click(s), page.click(s), page.click(s)])` | For Rage Clicker Rick |

**Client-side console capture** — every sub-agent session must register these listeners
BEFORE navigating to the app:

```javascript
const consoleErrors = [];
const pageErrors = [];

page.on('console', msg => {
  if (msg.type() === 'error' || msg.type() === 'warning') {
    consoleErrors.push({type: msg.type(), text: msg.text(), url: msg.location()?.url});
  }
});
page.on('pageerror', err => {
  pageErrors.push({message: err.message, stack: err.stack});
});
```

After each interaction, check `consoleErrors.length` and `pageErrors.length` for new entries.
These are the EVIDENCE-CONSOLE for each finding.

### Step 0d: Baseline Screenshot + Console

Use Puppeteer to capture the baseline:

```javascript
const browser = await puppeteer.launch({headless: 'new', args: ['--no-sandbox']});
const page = await browser.newPage();
// Register console listeners (from Step 0c)
await page.goto('[url]', {waitUntil: 'networkidle2', timeout: 15000});
await page.screenshot({path: '/tmp/billy-baseline.png', fullPage: true});
// Check pre-existing console errors
console.log(`Pre-existing errors: ${consoleErrors.length}, warnings: ${pageErrors.length}`);
```

If the baseline has >5 console errors, warn the user: "App has pre-existing errors.
Billy will filter these out of new findings to avoid noise."

---

## Phase 1: Chaos Test Execution

### The Billy Personas

Billy is not one user — billy is a cast of 5 chaos personas. Each sub-agent adopts
ONE persona and runs an independent test session. The personas are:

| Persona | Behavior Pattern | What They Break |
|---------|-----------------|-----------------|
| **Fumbles** | Clicks everything. Doesn't read labels. Submits forms without filling them. Clicks submit 5 times rapidly. | Empty states, double-submit, missing validation |
| **Backwards Bob** | Uses the app in reverse order. Tries step 3 before step 1. Hits back button mid-flow. Refreshes during submissions. | State management, navigation guards, partial state |
| **Copy-Paste Carol** | Pastes emoji, SQL injection strings, 10,000-char text, special characters, Unicode, HTML tags into every input. | Input sanitization, XSS, overflow, encoding |
| **Rage Clicker Rick** | Clicks buttons during loading states. Toggles things on-off-on-off rapidly. Resizes the window mid-action. Switches tabs and comes back. | Race conditions, loading states, focus management |
| **Zero-Knowledge Zara** | Has never seen a computer. Doesn't know what a dropdown is. Tries to type into non-input elements. Ignores error messages entirely and retries the same wrong action. | Error message clarity, affordance, guidance, recovery paths |

### Sub-Agent Dispatch

Spawn 3 sub-agents (personas assigned round-robin from the 5). Each agent:

1. **Takes a screenshot** of the initial state
2. **Executes 8-12 interactions** according to their persona
3. **After each interaction**: screenshot + console capture
4. **Logs each finding** as:

```
FINDING: [short description]
PERSONA: [which persona found it]
SEVERITY: P0-CRITICAL | P1-BROKEN | P2-ANNOYING | P3-COSMETIC
STEPS: [exact reproduction steps, numbered]
EVIDENCE-VISUAL: [screenshot description — what's wrong in the image]
EVIDENCE-CONSOLE: [exact error text from console, or "clean"]
EXPECTED: [what should have happened]
ACTUAL: [what actually happened]
```

### Local Dev vs. Production — Evidence Differences

Puppeteer captures screenshots and client-side console errors identically for both.
The differences are:

| Evidence Source | Local Dev | Production |
|----------------|-----------|------------|
| Screenshots (Puppeteer) | ✅ Available | ✅ Available |
| Client-side JS errors (`page.on('console')`) | ✅ Available | ✅ Available |
| Server-side stderr (dev process) | ✅ Available — capture with `[dev-command] 2>&1` | ❌ Not available |
| Network request failures | ✅ Capture with `page.on('requestfailed')` | ✅ Capture with `page.on('requestfailed')` |
| HTTP status codes | ✅ Capture with `page.on('response')` | ✅ Capture with `page.on('response')` |

**For production testing**, add these Puppeteer listeners to compensate for missing server stderr:

```javascript
// Capture failed network requests (production substitute for server stderr)
page.on('requestfailed', req => {
  FINDINGS.push({
    description: `Network request failed: ${req.url()}`,
    severity: 'P1-BROKEN',
    actual: req.failure()?.errorText || 'unknown',
  });
});

// Capture non-2xx responses
page.on('response', res => {
  if (res.status() >= 400) {
    CONSOLE_ERRORS.push({type: 'http-error', text: `${res.status()} ${res.url()}`});
  }
});
```

Note in the consensus report: `Evidence: browser-only (production)` or `Evidence: full stack (local dev)`.

### Severity Definitions (use these — no judgment calls)

| Severity | Definition | Threshold |
|----------|-----------|-----------|
| P0-CRITICAL | App crashes, data loss, security hole, or infinite loop | App becomes unusable or user loses work |
| P1-BROKEN | Feature doesn't work as intended, blocks user flow | User cannot complete a task they attempted |
| P2-ANNOYING | Works but confusing, misleading, or requires workaround | User can complete task but with frustration |
| P3-COSMETIC | Visual glitch, minor layout issue, non-blocking | User probably wouldn't notice or wouldn't care |

### Interaction Budget

Each sub-agent gets exactly 8-12 interactions per session. An "interaction" is one
user action (click, type, navigate, submit). This prevents agents from getting stuck
in infinite loops or testing the same thing repeatedly.

If an agent exhausts their budget without finding issues, that's a valid result —
it means the tested area is resilient.

---

## Phase 2: Evidence Collection & Deduplication

After all sub-agents complete their sessions:

### Step 2a: Collect All Findings

Gather findings from all 3 agents into a single list. Expected: 5-25 raw findings.

### Step 2b: Deduplicate

Two findings are duplicates if they describe the same root cause, even if found
by different personas or through different interaction paths.

Merge rules:
- Same root cause → keep the finding with better reproduction steps
- Same UI element, different failure modes → keep both (they're separate bugs)
- Same error message from different triggers → keep both triggers, merge into one finding

### Step 2c: Assign Preliminary Severities

Each finding gets an initial severity. If 2+ agents found the same issue,
severity automatically upgrades one level (P3→P2, P2→P1) — multiple discovery
paths mean real users will hit it too.

---

## Phase 3: Consensus Protocol

This is what makes billy reliable. No finding ships without consensus.

### Step 3a: Independent Verification

For each deduplicated finding, spawn a NEW sub-agent (not one of the original testers).
This agent:

1. Reads ONLY the reproduction steps (not the severity or description)
2. Attempts to reproduce the finding exactly as described
3. Takes a screenshot at the failure point
4. Reports: `CONFIRMED` or `NOT REPRODUCED` with their own screenshot evidence

### Step 3b: Consensus Rules

| Original Agents | Verifier | Decision |
|----------------|----------|----------|
| 2+ found it | CONFIRMED | ✅ Ship it — high confidence |
| 1 found it | CONFIRMED | ✅ Ship it — verified |
| 2+ found it | NOT REPRODUCED | ⚠️ Intermittent — ship with note, label "FLAKY" |
| 1 found it | NOT REPRODUCED | ❌ Drop it — likely false positive or environment-specific |

### Step 3c: Final Severity Review

After consensus, review severities against the threshold table in Phase 1.
Upgrade any P2 that blocks a core user flow to P1.
Downgrade any P1 to P2 if the user can complete the task in ≤2 extra steps.

### Step 3d: Consensus Report

Produce the consensus report as a structured summary:

```
BILLY CONSENSUS REPORT — [App Name]
Date: [timestamp]
App: [URL or project path]
Runtime: [local dev | production]
Personas tested: [which 3 of 5]
Total interactions: [sum across agents]
Raw findings: [count]
After dedup: [count]
After consensus: [count confirmed]
Dropped (false positive): [count]

CONFIRMED FINDINGS (sorted by severity):

#1 [P0-CRITICAL] [Title]
   Steps: [numbered reproduction]
   Evidence: [screenshot + console]
   Found by: [persona(s)]
   Verified by: [independent agent]

#2 [P1-BROKEN] [Title]
   ...
```

Present this report to the user. Wait for acknowledgment before proceeding
to Phase 3e.

### Step 3e: Discovery Interview

After the user has read the consensus report, conduct this structured interview
BEFORE generating any remediation prompt. Do not skip this — it prevents billy
from generating fixes for intentional behaviors or deprioritized issues.

**Ask these 5 questions in order. Accept short answers.**

| # | Question | Why | What to do with the answer |
|---|----------|-----|---------------------------|
| 1 | "Are any of these findings actually intentional behavior?" | Chaos testing can flag defensive designs (e.g., deliberately disabled buttons, intentional input limits) as bugs | Mark as `WONTFIX` — remove from remediation scope |
| 2 | "Do you want to override any severity ratings?" | The user knows their app's critical path better than billy does | Adjust severities per user input. Document overrides in the report. |
| 3 | "What's your fix budget — all P0+P1, top N items, or specific findings only?" | Prevents generating a 20-item remediation prompt when the user wants to fix 3 things | Scope the remediation to exactly what the user wants. Default if not specified: all P0 + all P1. |
| 4 | "Any codebase context I should know? Architecture patterns, existing utilities, areas that are fragile?" | The user has tacit knowledge about their codebase that no tool can discover | Feed directly into the from-prompter handoff as Constraints or Context. |
| 5 | "Should the remediation agent fix each issue independently (safer, more context per fix) or batch them (faster, one pass)?" | Independent fixes are easier to verify but cost more tokens. Batching risks cascading regressions. | Set the from-prompter handoff's Implementation Approach accordingly. |

**If the user says "just go" or "fix everything":**
- Default scope: all P0 + all P1 findings
- Default approach: independent fixes, severity order
- Note `[USER: no interview — using defaults]` in the handoff

**Exit condition**: User has answered or explicitly skipped all 5 questions.
Update the consensus report with any WONTFIX/severity changes. Then proceed to Phase 4.

---

## Phase 4: Remediation Prompt Generation

### Step 4a: Codebase Recon for Findings

Before translating findings to requirements, locate the actual source files
responsible for each confirmed finding. This gives from-prompter concrete
file paths instead of generic descriptions.

**If `codebase_*` tools are available (desktop connector or Claude Code):**

For EACH confirmed finding still in scope (not WONTFIX'd):

1. **Identify the UI element** — from the finding's reproduction steps, determine which
   component/page/route contains the failing element (button, form, input, etc.)
2. **Search for it** — use `codebase_search_code` with the element's text label, CSS class,
   or component name:
   ```
   codebase_search_code(path=project_root, query="Submit", file_pattern="\\.tsx?$")
   ```
3. **Read the file** — use `codebase_read_file` on the match to confirm it's the right
   component and understand the current implementation
4. **Find related files** — for each finding, note up to 3 related files:
   - The component file (where the UI element lives)
   - The handler/API route (where the submission goes)
   - The validation/utility (if any validation exists)

**Record as a structured map:**

```
FINDING → SOURCE MAP:
#1 "Empty form submits" →
   Component: src/components/OrderForm.tsx (line 45-89)
   Handler:   src/routes/api/orders.ts (line 12-34)
   Validation: NONE — no validation file exists (this IS the bug)

#2 "Double-click creates duplicates" →
   Component: src/components/SubmitButton.tsx (line 8-22)
   Handler:   src/routes/api/orders.ts (line 12-34)  [same handler]
   Guard:     NONE — no debounce or idempotency key
```

**If codebase tools are NOT available:**
Skip this step. Note `[CODEBASE RECON: skipped — no desktop connector]` in the
handoff. The from-prompter agent will need to discover file locations itself.

**Budget**: ≤3 `codebase_search_code` + ≤3 `codebase_read_file` per finding.
For >8 findings, search only P0 and P1 items to stay under tool budget.

### Step 4b: Translate Findings to Requirements

Convert each confirmed finding into a remediation requirement:

| Finding | Requirement |
|---------|------------|
| "Empty form submits successfully" | "Add client-side validation preventing submission when required fields are empty. Show inline error messages per field." |
| "Double-click submit creates duplicate entries" | "Disable submit button on first click. Show loading indicator. Prevent duplicate submissions server-side via idempotency key." |
| "Pasting 10K chars crashes the input" | "Add maxLength to input fields. Truncate with user notification if input exceeds limit. Test with 10,000-char paste." |

### Step 4c: Gather Context from Memory + Conversation

Before generating the handoff, assemble all available project context. This is what
makes the remediation prompt surgically specific rather than generic.

**Context sources (check all, use what's available):**

| Source | How to access | What to extract |
|--------|--------------|-----------------|
| **Memory** (userMemories) | Already in context window | Project stack, architecture, database IDs, deployment URLs, known patterns, past issues |
| **Conversation history** | Current chat context | What the user said about the app, what they care about, constraints mentioned earlier |
| **Discovery interview** (Phase 3e) | Answers from Step 3e | WONTFIX items, severity overrides, fix budget, user-provided codebase context, batch vs independent preference |
| **Codebase recon** (Step 4a) | Source maps from Step 4a | Exact file paths, line numbers, existing patterns, missing validations |
| **Project structure** (Phase 0) | From `codebase_get_project_structure` | Framework, dependencies, config files, entry points |

**Assemble into a context block** for the handoff:

```
PROJECT CONTEXT (from memory + conversation + recon):
- Stack: [framework + runtime + UI + database — from memory or recon]
- Architecture: [key patterns — SSR/CSR, API layer, state management]
- Deployment: [where it runs — from memory or user]
- Key files: [from Step 4a source maps]
- Known constraints: [from user interview, memory, or conversation]
- Related history: [any past work on this app mentioned in memory]
```

If memory contains specific project details (database IDs, deployment URLs,
architectural decisions), include them verbatim — the remediation agent needs
concrete values, not summaries.

### Step 4d: Generate the From-Prompter Input

Billy does NOT write the remediation prompt directly. Billy prepares the structured
input for `from-prompter`, which handles prompt engineering and optimization.

Produce this handoff document:

```markdown
# Billy → From-Prompter Handoff

## Prompt Category
Bug Investigation & Fix (multi-bug remediation)

## Objective
Fix [N] confirmed issues found during chaos user-testing of [app name].
Every fix must be verified by re-running the exact reproduction steps
from the billy consensus report.

## Context
- **Project**: [name — from memory or user]
- **Stack**: [framework, runtime, UI library, database, key deps — from memory/recon]
- **Deployment**: [URL or local path — from Phase 0]
- **Architecture**: [key patterns from codebase recon]
- **Known constraints**: [from discovery interview + memory]
- **Past relevant work**: [from memory — e.g., "completed production audit", "1,322 tests passing"]

## Current State
[App name] at [path/URL] has [N] confirmed issues ranging from
[highest severity] to [lowest severity].
[Include any relevant context from memory about the app's current state,
recent changes, or known tech debt.]

## Source Map (from codebase recon)
[Paste the FINDING → SOURCE MAP from Step 4a here — exact file paths
and line numbers for each finding. If codebase recon was skipped,
note that the remediation agent must discover these.]

## Requirements (from billy findings)
[Numbered list — one per confirmed finding still in scope (after WONTFIX removal).
Each requirement includes:
- What to fix (from the finding description)
- Where to fix it (from the source map)
- How to verify it's fixed (from the reproduction steps)
- Acceptance criteria from the finding's EXPECTED field]

## User Preferences (from discovery interview)
- Fix scope: [all P0+P1 | top N | specific items — from Q3]
- Fix approach: [independent | batched — from Q5]
- User-provided context: [anything from Q4]
- Severity overrides: [any from Q2]

## Constraints
- Every fix MUST be verified by re-running billy's reproduction steps
- No fix should break existing functionality — run full test suite after each fix
- Fix in severity order: P0 first, then P1, then P2
- P3 items are optional — fix only if trivial
[Add any constraints from memory — e.g., "do not modify production database",
"all changes must pass 1,322 existing tests"]

## Verification Protocol
After ALL fixes are applied:
1. Re-run each reproduction step from the consensus report using the billy Puppeteer harness
2. Confirm the expected behavior now occurs (screenshot comparison)
3. Run the project's existing test suite
4. Check server console for new errors: [dev-command] 2>&1 | grep -ciE "error|warn" — must be 0 new
5. Check client-side console via Puppeteer page.on('console') — must be 0 new errors

## Definition of Done
- All in-scope findings are fixed and verified
- No new console errors or warnings introduced
- Existing test suite passes
- Each fix has a before/after screenshot comparison
```

### Step 4e: Execute From-Prompter

Pass the handoff document to `from-prompter` for prompt optimization. From-prompter
will run its autoresearch loop with sub-agents to harden the remediation prompt
before delivering it.

### Step 4f: Deliver the CLI Command

After from-prompter produces the optimized prompt, present the user with:

```
Here's your remediation prompt. To execute:

cd [project-path]
claude -p "$(cat [path-to-optimized-prompt])"

Or paste the prompt directly into Claude Code.
```

---

## Anti-Patterns (Do NOT)

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Report findings without screenshot evidence | Every finding gets a screenshot at the failure point | Unverified claims waste developer time on phantom bugs |
| Skip consensus and ship raw agent findings | Always run the independent verification step (Phase 3) | Sub-agents hallucinate failures ~15% of the time — consensus eliminates this |
| Write the remediation prompt yourself | Chain to from-prompter for prompt engineering | billy is a tester, not a prompt engineer — separation of concerns |
| Test against a dead or partially-loaded app | Verify HTTP 200 + screenshot baseline before any testing | Testing against a broken deployment produces garbage findings |
| Run >12 interactions per agent per session | Hard cap at 12 — spawn a new session for more coverage | Long sessions cause agent drift and repetitive testing |
| Rate everything P0-CRITICAL | Use the severity threshold table — P0 means the app is unusable | Severity inflation makes the report useless |
| Assume production and local dev behave the same | Note the runtime environment on every finding | Environment-specific bugs are real but must be labeled |

---

## Edge Cases

| Situation | Action |
|-----------|--------|
| App requires authentication | Ask user for test credentials. If none available, test only unauthenticated flows. Note "auth-gated flows not tested" in report. |
| App has no interactive elements (static site) | Test navigation, links, responsive behavior, image loading, 404 handling. Reduce persona count to 2 (Backwards Bob + Copy-Paste Carol for search/forms if any). |
| Dev server crashes during testing | Capture the crash output. Log as P0-CRITICAL finding. Restart and continue testing remaining areas. |
| All 3 agents find zero issues | Valid result. Report "✅ No issues found across [N] interactions with [3] personas." Skip Phases 3-4. |
| User wants to test specific flows only | Constrain all personas to the specified flows. Note "scope-limited test" in report. |
| App is behind a VPN or firewall | Cannot test from Claude Code. Ask user to provide screenshots or use local dev instead. |

---

## Reference Files

- **`references/persona-scripts.md`** — Detailed interaction scripts per persona with
  example commands, input payloads, and navigation patterns. Read before spawning sub-agents.
