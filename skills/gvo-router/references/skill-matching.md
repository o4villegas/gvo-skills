# Skill Matching — From User Request to Loaded Skills

This file defines how the Director matches a user request against `registry.json` and
hands matched skills' content to the appropriate Lead.

## Inputs

- The user's literal request text (verbatim — do not paraphrase before matching)
- `skills/nexus/registry.json` from the gvo-skills repo — the canonical skill index (read in §2 of SKILL.md). Paths in entries are relative to `skills/nexus/`: nested skills use `skills/<name>/SKILL.md`, top-level siblings use `../<name>/SKILL.md`.

## Output

- A ranked list of matched skills (top 3 above threshold)
- Each match has: skill name, path, score, why-matched, content (full SKILL.md text)

The Director never sends just a path to a Lead — it embeds the full SKILL.md content
into the Lead's prompt as read-only context.

## Algorithm

### Step 1: Tokenize Request

Lowercase, strip punctuation, split on whitespace. Drop common stop words ("the", "a",
"is", "to", "for"). Keep verbs and nouns.

```
"build me a Cloudflare Worker that processes PDF receipts"
  →  ["build", "me", "cloudflare", "worker", "processes", "pdf", "receipts"]
  →  ["build", "cloudflare", "worker", "processes", "pdf", "receipts"]  (after stop-word drop)
```

Also extract named entities (proper nouns, identifiers):
- Project names: "DocuDamage", "PurfPulse", "kc-actuals"
- Frameworks/libraries: "Cloudflare", "React", "Hono", "shadcn", "Vitest"
- File scopes: "src/api/auth.ts", "the auth module"
- Domain terms: "PDF", "invoice", "receipt", "trivia"

### Step 2: Score Each Skill

For each skill in `registry.json`:

```
score = 0
for token in request_tokens:
    if token == skill.name (or skill.name contains token as substring of length ≥4):
        score += 5
    if token in skill.triggers:
        score += 3
    if token in skill.tags:
        score += 2
    if token in skill.description (case-insensitive):
        score += 1
```

Also boost `category` matches:
- If request looks like build/create/implement → `category: implementation` skills get +2
- If request looks like plan/design/architect → `category: planning` skills get +2
- If request looks like fix/debug/troubleshoot → `category: debugging` skills get +2
- If request looks like review/audit/check → `category: review` skills get +2
- If request looks like research/lookup/find → `category: research` skills get +2

### Step 3: Apply Threshold + Cap

- Threshold: 5 — below this, the match is too weak to use
- Cap: **top 5 above threshold** (was top 3). The wider candidate pool feeds Step
  4.5's content-aware re-rank, which then narrows back to top 3. If Step 4.5 will
  be skipped (skip condition: any skill scored ≥ 15), the Director can short-circuit
  back to top 3 at this step.
- Ties broken by name length (longer name = more specific = preferred)

If zero skills above threshold → no skill match → route through default plan/build/test
pipeline with stack defaults from §7 of SKILL.md.

### Step 4: Read Matched Skills' Content

For each of the top 5 (or top 3 in the short-circuit case), run `codebase_read_file`
on its `path` field. Embed the FULL content into the Step 4.5 input (or directly
into the relevant Lead's prompt if Step 4.5 is skipped) — do not summarize, do not
pass just the path.

### Step 4.5: Content-Aware Re-Rank

**When to run:** when no Step 2 score hit ≥ 15. Skip otherwise — the clear winner
won't change under re-ranking.

**Why:** Step 2 scores against registry metadata only. As of 2026-05-17 the registry
has 91% empty `tags` arrays and 17% empty `triggers` arrays, so metadata-only
scoring systematically under-ranks skills with weak metadata even when their
SKILL.md body is the correct fit. Step 4.5 corrects this by re-ranking on the
actual skill body.

**Algorithm:**

1. Take the 5 SKILL.md bodies loaded in Step 4. Strip YAML frontmatter from each.
2. Issue ONE opus call (Agent tool, model: "opus", subagent_type: "general-purpose")
   with this prompt shape:
   ```
   Request: "<user's literal request>"

   For each of these 5 skills, score 0-10 on how well its full instructions match
   the request. Reply with JSON only, no prose around it:
     [{"name": "X", "score": N, "why": "<≤80 chars>"}, ...]

   Skills:
   ## skill-1-name
   <body, frontmatter stripped>

   ## skill-2-name
   <body>
   ...
   ```
3. Parse the JSON reply. Top 3 by `score` field become the final matched skills.
4. Any of the 5 candidates that scored well in Step 2 but dropped in Step 4.5 gets
   logged to the Director's assumption ledger as:
   `A0_dropped_match: <name> (Step 2 score: X, Step 4.5 content score: Y, why: <reason>)`
   The user can override post-hoc with "also use <name>".

**Cost:** 5 parallel reads (already done in Step 4) + 1 opus call. The opus call's
input size is dominated by the 5 SKILL.md bodies — typically 5K-25K input tokens,
small JSON output.

**Why ONE batched call, not five per-skill calls:** the per-skill call would be 5×
cheaper individually but loses cross-skill calibration. The batched call lets the
scorer see all 5 simultaneously and produce calibrated relative scores. Batch wins.

**Failure handling:** if the opus call returns malformed JSON or non-JSON prose,
fall back to the Step 2 top 3 and log
`A0_step_4.5_parse_failed: opus reply was <first 200 chars>` to the ledger. Do not
retry — that just adds cost without changing the underlying issue. The Step 2
fallback is acceptable.

## Worked Examples

### Example 1: "build me a Cloudflare Worker that processes PDF receipts"

Tokens: build, cloudflare, worker, processes, pdf, receipts

Top scoring (illustrative, not exact):

| Skill | Score breakdown | Total |
|-------|-----------------|-------|
| cloudflare-deploy | name match "cloudflare" (5) + tags "cloudflare,worker" (4) + desc "Worker" (1) | 10 |
| pdf | name match "pdf" (5) + tags "pdf" (2) | 7 |
| nexus | desc "build" (1) + category implementation (2) | 3 |

Matched: `cloudflare-deploy`, `pdf`. (nexus below threshold)

Director embeds full content of `cloudflare-deploy/SKILL.md` and `pdf/SKILL.md` into
Lead-Plan's prompt as context for "use these skills' patterns when planning."

### Example 2: "fix the auth bug where session tokens expire too early"

Tokens: fix, auth, bug, session, tokens, expire

| Skill | Score | Notes |
|-------|-------|-------|
| focused-fix | name "focused-fix" (5 substring) + triggers "fix" (3) | 8 |
| security-review | tag "security" (2) + desc "auth" (1) | 3 |

Matched: `focused-fix`. Below threshold for others → use default pipeline with
focused-fix skill embedded.

### Example 3: "what does git status do"

Tokens: git, status

No high-scoring matches. Below threshold → `Class: quick`. Skip the org structure,
answer directly from training knowledge.

## Edge Cases

### Multi-Domain Requests
"build me an auth flow with tests"
- Likely matches: cloudflare-deploy (if project context indicates CF) + tdd-workflow
- Lead-Plan receives both
- Lead-Build uses cloudflare-deploy patterns
- Lead-Test uses tdd-workflow patterns

### Skill Name in Request (Direct Invocation)
"use the pdf skill to extract receipts from this folder"
- The token "pdf" is a direct skill name → score 5 from name match
- Boost: explicit invocation patterns ("use the X skill", "run X", "call X") add +5 to
  the named skill
- Override: if confidence is high (request maps almost entirely to one skill), call
  that skill directly via its trigger pattern and skip 3-tier org

### No Match (Unknown Domain)
"help me understand what my dog is dreaming about"
- No skills match
- Tokens don't match implementation/planning/etc. categories
- `Class: other` — handle conversationally, no org

### Skill Disabled (`isActive: false`)
- Filter these out at Step 2 (do not score)
- If a disabled skill would have matched, log to assumption ledger:
  `A_N: Skill X would match but is disabled in registry. Did not use it.`

### Registry Location (single source of truth)
The canonical registry is `/skills/nexus/registry.json`. A root-level `/registry.json` previously existed as a subset mirror but was removed — paths in it had drifted and gvo-router was the only consumer. Always read `skills/nexus/registry.json`.

Path resolution from nexus registry entries:
- Nested skills (under `skills/nexus/skills/<name>/`): path is `skills/<name>/SKILL.md`
- Top-level siblings (under `skills/<name>/`): path is `../<name>/SKILL.md`

## Loading Skills' Content

After matching:

1. For each matched skill, run `codebase_read_file path="<skill.path>"`.
2. Verify the returned content has a `name:` field in frontmatter matching the skill
   name. If mismatch, the registry is out of sync — log assumption + use the file.
3. Strip the YAML frontmatter from the content before embedding (the Lead doesn't need
   the metadata, only the instructions).
4. Embed in the Lead's prompt under a `## Skill Context (from registry match)` heading
   with the skill name as a sub-heading.

```
## Skill Context (from registry match)

### cloudflare-deploy
<full SKILL.md body, frontmatter stripped>

### pdf
<full SKILL.md body, frontmatter stripped>
```

## Director's Skill-Match Output Format

After matching, the Director writes a one-block summary into the audit trail:

```
[Skill Match]
Request: "build me a Cloudflare Worker that processes PDF receipts"
Tokens: build, cloudflare, worker, processes, pdf, receipts
Matched (above threshold 5):
  1. cloudflare-deploy (10)  — skills/cloudflare-deploy/SKILL.md (412 bytes content)
  2. pdf (7)                 — skills/pdf/SKILL.md (1834 bytes content)
Below threshold (informational):
  3. nexus (3)
Action: embed (1) and (2) into Lead-Plan + Lead-Build prompts
```

This goes into the assumption ledger if any skill was a close miss — the user can
override with "also use X."

## What This Algorithm Doesn't Do

- **No semantic search**. Pure token + tag + name matching. Good enough for the current
  registry size; revisit if registry > 200 skills.
- **No learning**. The algorithm is deterministic per registry version. Track skill
  effectiveness via the skill-evolution Worker API (mentioned in nexus §4) for future
  weight adjustment, not in this skill.
- **No fuzzy matching**. "cloudflair" won't match "cloudflare". Spelling matters.
  If the user types something close-but-wrong, surface "did you mean X?" as part of the
  Class: quick path.
