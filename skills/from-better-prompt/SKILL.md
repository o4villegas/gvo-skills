---
name: from-better-prompt
description: >
  Diagnostic skill that scans the .claude directory (CLAUDE.md files, memory/,
  skills/) to extract evidence-backed patterns from user-AI exchanges and
  distill them into a personal prompt-writing guide. Use when the user says
  "from-better-prompt", "better prompt", "improve my prompts", "prompt rules",
  "what have I learned", "extract prompt lessons", "what patterns do I repeat",
  "scan my history", "derive guardrails", "learn from past sessions", "build
  prompt rules", "analyze my prompt patterns", "what works in my prompts",
  "extract my rules", or any request to mine past Claude interactions for
  reusable prompt-writing principles. Also trigger when the user asks to build
  a personal prompt guide, review their accumulated AI interaction patterns, or
  derive agent instructions from their history. Distinct from from-prompter
  which WRITES new prompts — this skill ANALYZES past exchanges to extract
  rules. Distinct from from-skill-forge which creates/optimizes skills — this
  skill produces a rules guide, not a skill.
---

# From Better Prompt — Personal Prompt Rules Extractor

You are a diagnostic agent that mines the user's `.claude` directory for evidence-backed
patterns in their AI interactions, then distills those patterns into a personal
prompt-writing guide. Every rule you produce must cite specific evidence from the
user's actual history. Generic advice is a failure mode.

## Prerequisites

- **Environment**: Claude Code only (requires filesystem access to `.claude`)
- **Required tools**: Read, Glob, Grep (for scanning files)
- **Read-only**: This skill NEVER modifies any file it scans. It only creates new output files.
- **Distinct from**: `from-prompter` (writes new prompts), `from-skill-forge` (creates/optimizes skills)

---

## Phase 1: Source Discovery

Locate and catalog all evidence sources in the `.claude` directory.

### Step 1a: Scan Directory Structure

```bash
find ~/.claude -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" \) | head -100
```

Build a source inventory table:

| Source Type | Path Pattern | What It Contains |
|-------------|-------------|------------------|
| Global instructions | `~/.claude/CLAUDE.md` | Accumulated guardrails and behavior rules |
| Project instructions | `<project>/.claude/CLAUDE.md` or `<project>/CLAUDE.md` | Project-specific conventions |
| Memory index | `~/.claude/projects/*/memory/MEMORY.md` | Index of stored memories |
| Memory files | `~/.claude/projects/*/memory/*.md` | Individual feedback, user, project, reference memories |
| Skills | `~/.claude/skills/*/SKILL.md` | Skill definitions with embedded patterns |
| Skill references | `~/.claude/skills/*/references/*.md` | Supplementary skill documentation |
| Settings | `~/.claude/settings.json` | Configuration and hooks |

### Step 1b: Read All Sources

Read every file discovered in Step 1a. For each file, extract:

1. **Explicit rules** — direct instructions ("always do X", "never do Y", "use Z")
2. **Corrections** — evidence of past mistakes being addressed ("this was wrong because...", "changed from X to Y")
3. **Patterns** — recurring structural choices (how skills are organized, what sections repeat, naming conventions)
4. **Guardrails** — protective constraints ("do not modify", "read-only", "verify before")

Track the source file for every extracted item. An item without a source citation is garbage — discard it.

### Step 1c: Scan for Optimization Artifacts

Search for autoresearch changelogs, round logs, and optimization history:

```bash
find ~ -maxdepth 5 -type f \( -name "changelog.md" -o -name "round-*.json" -o -name "*optimization*" -o -name "*changelog*" \) 2>/dev/null | head -50
```

If optimization artifacts exist, they are the highest-value evidence source — they contain
empirical data on what worked and what didn't, with before/after scores.

### Step 1d: Source Quality Assessment

Before analysis, rate each source's evidence quality:

| Quality Tier | Criteria | Example |
|-------------|----------|---------|
| **Tier 1 — Empirical** | Has before/after data, scores, or keep/revert decisions | Optimization changelogs, round logs |
| **Tier 2 — Corrective** | Records a specific mistake and its fix | Memory feedback files, CLAUDE.md corrections |
| **Tier 3 — Declarative** | States a rule without showing what prompted it | CLAUDE.md instructions, skill guardrails |
| **Tier 4 — Structural** | Reveals patterns through repetition, not explicit statement | Skill organization, naming conventions |

Prioritize Tier 1-2 evidence. Tier 3-4 evidence supports but does not independently justify a rule.

**Exit condition**: All sources read, items extracted with citations, quality tiers assigned.
Present a summary to the user: "[N] sources scanned, [M] items extracted. Highest-quality
sources: [list Tier 1-2 sources]. Ready to analyze."

---

## Phase 2: Pattern Extraction

### Step 2a: Kept Change Patterns

From optimization artifacts and corrective evidence, identify what consistently improved outputs:

For each pattern found, record:

```
PATTERN: [short name]
EVIDENCE: [specific source file + what it shows]
FREQUENCY: [how many sources support this pattern]
EFFECT: [what improved when this pattern was applied]
```

Look for these pattern categories:

| Category | What to look for | Where to find it |
|----------|-----------------|------------------|
| **Structure** | Section ordering, phase gates, progressive disclosure | Skill SKILL.md files |
| **Specificity** | Concrete vs vague instructions, thresholds vs adjectives | CLAUDE.md rules, skill instructions |
| **Verification** | How outputs are validated, what checks are required | Skill verification steps, CLAUDE.md mandates |
| **Scope control** | Anti-scope definitions, boundary enforcement | Skill anti-patterns sections, CLAUDE.md constraints |
| **Evidence requirements** | When citations/proof are required vs optional | Memory feedback files, skill evidence rules |
| **Error handling** | How failures are detected and recovered from | Skill edge case tables, CLAUDE.md error rules |

### Step 2b: Reverted Change Patterns (Anti-Patterns)

From optimization artifacts and corrective evidence, identify what consistently hurt outputs:

For each anti-pattern found, record:

```
ANTI-PATTERN: [short name]
EVIDENCE: [specific source file + what went wrong]
FREQUENCY: [how many sources show this failing]
EFFECT: [what degraded when this pattern was present]
```

Common anti-pattern categories:

| Category | What to look for |
|----------|-----------------|
| **Vagueness** | Rules that say "appropriately", "as needed", "if necessary" without thresholds |
| **Overreach** | Skills or rules that try to do too much, crossing domain boundaries |
| **Missing alternatives** | "Don't do X" without specifying what to do instead |
| **Assumed context** | Instructions that assume knowledge not in the prompt |
| **Untestable criteria** | Quality checks that can't be mechanically verified |

### Step 2c: Cross-Reference Validation

For every pattern and anti-pattern, verify it appears in 2+ independent sources before
promoting it to a rule candidate. Single-source patterns are flagged as `[LOW CONFIDENCE]`
and presented separately.

**Exit condition**: Pattern and anti-pattern lists complete with evidence citations.
Present counts: "[X] kept patterns, [Y] anti-patterns, [Z] low-confidence items."

---

## Phase 3: Rule Synthesis

### Step 3a: Draft Rules

Convert validated patterns into actionable rules. Each rule follows this template:

```
RULE [N]: [Imperative statement — what to do]

WHY: [What goes wrong without this rule — cite specific evidence]
SOURCE: [File path(s) where this pattern was observed]
EXAMPLE:
  BEFORE: [What the prompt/skill looked like without this rule]
  AFTER:  [What it looked like with this rule applied]
APPLIES TO: [Universal | Specific skill types]
```

**Rule writing constraints:**
- Every rule MUST include a specific BEFORE/AFTER example from the user's actual files
- Rules must be imperative ("Do X", "Use Y") not descriptive ("It's good to X")
- Rules must be testable — a reader should be able to check yes/no whether a prompt follows the rule
- Target 5-10 rules. Fewer than 5 means the analysis was too shallow. More than 10 means rules overlap — merge them.

### Step 3b: Classify Rules

Separate rules into two buckets:

| Bucket | Definition | How to determine |
|--------|-----------|-----------------|
| **Universal** | Applies to any prompt or skill regardless of domain | Pattern appears across 3+ unrelated skills or in global CLAUDE.md |
| **Domain-specific** | Applies only to certain types of prompts or skills | Pattern appears only in skills of one category (data pipeline, audit, etc.) |

### Step 3c: Rank by Impact

Order rules by how frequently the underlying pattern appears AND how severe the
consequences are when violated:

```
Impact = frequency_of_pattern × severity_when_violated
```

Where:
- Frequency: count of sources where the pattern appears (1-N)
- Severity: 3 = output is wrong, 2 = output is incomplete, 1 = output is cosmetically off

Present rules in impact-ranked order, highest first.

**Exit condition**: 5-10 rules drafted, classified, and ranked. Present to user for review.

---

## Phase 4: Guide Assembly

### Step 4a: Build the Personal Prompt-Writing Guide

Assemble the final guide using this exact structure:

```markdown
# Personal Prompt-Writing Guide
Generated: [date]
Sources analyzed: [count]
Evidence quality: [breakdown by tier]

## How to Use This Guide
Read this before writing any new skill or prompt. Takes <2 minutes.
Check each rule against your draft before delivering it.

## Universal Rules (apply to every prompt)

### Rule 1: [Title]
**Do**: [imperative instruction]
**Why**: [consequence of violating — with evidence citation]
**Example**:
- Before: [actual text from user's files]
- After: [actual text from user's files]
**Quick check**: [yes/no question to verify compliance]

### Rule 2: [Title]
...

## Domain-Specific Rules

### [Category Name] (e.g., Data Pipeline Skills)

#### Rule N: [Title]
...

## Anti-Patterns (never do these)

| Anti-Pattern | What Goes Wrong | Do This Instead |
|-------------|----------------|-----------------|
| [name] | [evidence-backed consequence] | [concrete alternative] |

## Evidence Appendix
| Rule | Source File(s) | Tier |
|------|---------------|------|
| Rule 1 | [paths] | [tier] |
| Rule 2 | [paths] | [tier] |
```

### Step 4b: Self-Audit the Guide

Before delivering, verify:

1. **Evidence check**: Does every rule cite a specific source file? If not, remove the rule.
2. **Example check**: Does every rule have a BEFORE/AFTER from the user's actual files? If not, add one or remove the rule.
3. **Testability check**: Does every "Quick check" question have a clear yes/no answer? If not, rewrite it.
4. **Overlap check**: Do any two rules say the same thing? If so, merge them.
5. **Actionability check**: Can the user apply this guide in <2 minutes? If the guide is >3 pages, cut the lowest-impact rules.

### Step 4c: Deliver

1. **Present the guide** in the conversation as formatted output
2. **Save the guide** to the `.claude` directory:
   - Path: `~/.claude/prompt-rules.md`
   - If the file exists, ask the user: "A prompt-rules.md already exists. Overwrite, merge, or save as prompt-rules-[date].md?"
3. **Present a summary**: "[N] universal rules, [M] domain-specific rules, [K] anti-patterns extracted from [S] sources"

---

## Anti-Patterns (Do NOT)

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Include generic prompt advice ("be specific", "provide context") | Every rule must cite evidence from the user's actual `.claude` files | Generic advice is available everywhere — the value here is personalized, evidence-backed rules |
| Modify any file you scan | Create only new files (the guide output) | Read-only scanning prevents accidental corruption of the user's configuration |
| Present a rule backed by only one low-tier source | Require 2+ sources or flag as `[LOW CONFIDENCE]` | Single-source rules may be anomalies, not patterns |
| Produce >10 rules | Merge overlapping rules until you have 5-10 | More rules = less compliance. A focused set beats an exhaustive list. |
| Skip the BEFORE/AFTER examples | Every rule needs a concrete example from the user's files | Rules without examples are abstract — examples make rules memorable and applicable |
| State rules as descriptions ("It's helpful to...") | Use imperatives ("Do X", "Use Y", "Verify with Z") | Imperative rules are clearer and more likely to be followed |

---

## Edge Cases

| Situation | Action |
|-----------|--------|
| `.claude` directory has minimal content (<5 files) | Produce what you can, but flag: "Limited evidence — [N] sources found. Rules are lower confidence. Re-run after more Claude sessions to improve." |
| No optimization artifacts found (no changelogs) | Rely on Tier 2-4 evidence. Flag: "No optimization history found. Rules are derived from declarative patterns only — empirical validation would strengthen them." |
| User has multiple project directories with separate `.claude` folders | Scan all of them. Note which rules are project-specific vs cross-project. |
| Existing `prompt-rules.md` found | Ask user: overwrite, merge, or save separately. If merging, diff the old and new rules and present changes. |
| Contradictory patterns found (file A says "do X", file B says "don't X") | Present both with sources. Ask the user which is current. Do not resolve contradictions silently. |
| User provides an optimization changelog directly (not from files) | Accept it as a Tier 1 source. Proceed with analysis. Skip Step 1c file scanning for changelogs. |
