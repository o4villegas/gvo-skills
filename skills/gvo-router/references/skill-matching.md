# Skill Matching — From User Request to Loaded Skills

This file defines how the Director matches a user request against `registry.json` and
hands matched skills' content to the appropriate Lead.

## Inputs

- The user's literal request text (verbatim — do not paraphrase before matching)
- `registry.json` from the gvo-skills repo root (read in §2 of SKILL.md)

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
- Cap: top 3 skills above threshold
- Ties broken by name length (longer name = more specific = preferred)

If zero skills above threshold → no skill match → route through default plan/build/test
pipeline with stack defaults from §7 of SKILL.md.

### Step 4: Read Matched Skills' Content

For each matched skill, run `codebase_read_file` on its `path` field. Embed the FULL
content into the relevant Lead's prompt — do not summarize, do not pass just the path.

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

### Multiple Registries (Repo Root vs nexus/)
The repo has two registries: `/registry.json` and `/skills/nexus/registry.json`.

- Use `/registry.json` (root) as the primary source — it's the global index.
- The nexus copy is for nexus's own bundled sub-skills.
- If a skill appears in only one, use that one.
- If a skill appears in both with different content, root wins, log an assumption:
  `A_N: Skill X has divergent registry entries; used root copy.`

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
