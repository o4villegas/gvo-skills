# Skill Anatomy Reference

## Directory Structure

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description — both required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/      Executable code for deterministic/repetitive tasks
    ├── references/   Docs loaded into context as needed
    └── assets/       Files used in output (templates, icons, fonts)
```

## Progressive Disclosure (Three Levels)

| Level | What | When loaded | Size target |
|-------|------|-------------|-------------|
| Metadata | name + description | Always in context | ~100 words |
| SKILL.md body | Full instructions | When skill triggers | <500 lines |
| Bundled resources | Scripts, references, assets | On demand via `view` or execution | Unlimited |

If SKILL.md approaches 500 lines, push supplementary content into `references/` with
clear pointers: "Read `references/X.md` before starting Phase N."

For reference files >300 lines, include a table of contents at the top.

## Domain Organization

When a skill supports multiple variants (frameworks, platforms, modes), organize by variant:

```
cloud-deploy/
├── SKILL.md (workflow + selection logic)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

Claude reads only the relevant reference file. The SKILL.md contains the selection logic
(decision table or conditional) that routes to the right reference.

## YAML Frontmatter

```yaml
---
name: skill-name
description: >
  What the skill does + when to trigger it. This is the PRIMARY triggering
  mechanism. Include:
  - Core capability in one sentence
  - Explicit trigger phrases ("use when the user says X, Y, Z")
  - Category-level triggers ("any request involving...")
  - Near-miss exclusions ("distinct from X which handles Y")
  - Be pushy — Claude under-triggers. Better to over-describe than under-describe.
---
```

**Description anti-patterns to avoid:**
- Too short: "Creates documents." (won't trigger on anything specific)
- Too generic: "Helps with files." (triggers on everything, useful for nothing)
- Missing exclusions: competing skills will fight for the same inputs

## Writing Patterns

### Imperative Form
Write instructions as commands, not descriptions.

| Instead of | Write |
|------------|-------|
| "The skill should read the file" | "Read the file" |
| "It would be helpful to check" | "Check X before proceeding" |
| "Consider verifying" | "Verify with `grep -c 'pattern' file`" |

### Output Format Definitions

When specifying output structure, provide the exact template:

```markdown
## Report Structure
Use this exact template:

# [Title]
## Executive Summary
[2-3 sentences: what was found, what it means]
## Findings
[Ranked by impact, each with evidence]
## Recommendations
[Specific, actionable, with priority]
```

### Examples Pattern

Include examples showing both the input AND the expected output:

```markdown
## Commit Message Format
**Example 1:**
Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication

**Example 2:**
Input: Fixed crash when uploading files over 10MB
Output: fix(upload): handle files exceeding 10MB size limit
```

### Decision Logic

Use tables for branching logic, not nested prose:

| Condition | Action |
|-----------|--------|
| File is CSV with headers | Parse with pandas, validate column names |
| File is CSV without headers | Reject — ask user to confirm column mapping |
| File is XLSX | Convert to CSV first, then parse |
| File is unknown format | Stop and ask user for format details |

## Explain the Why

Today's LLMs have strong theory of mind. When you explain WHY a rule exists,
the model can generalize beyond the literal instruction.

| Weak (just the rule) | Strong (rule + why) |
|---------------------|---------------------|
| "ALWAYS check file encoding" | "Check file encoding before parsing — non-UTF-8 files produce silent corruption in string comparisons, which surfaces as mysterious data mismatches later" |
| "NEVER modify the original file" | "Work on a copy, not the original — if the skill crashes mid-operation, the user still has their data intact" |

Avoid `ALWAYS` and `NEVER` in all-caps when possible. Reframe as reasoning instead.
The model follows well-explained reasoning more reliably than shouted prohibitions.

## Security

Skills must not contain malware, exploit code, or any content that could compromise
system security. A skill's intent should not surprise the user if described plainly.
Do not create skills designed to facilitate unauthorized access, data exfiltration,
or misleading behavior.

## Bundled Scripts

Bundle a script when you observe the same helper code being written independently
across multiple test runs. If 3 out of 3 test cases produce a similar `build_chart.py`,
that script should live in `scripts/` and the skill should reference it.

Scripts in `scripts/` can be executed without loading them into context — reference
them by path and the model will run them directly.

## Environment Detection

When a skill works differently across environments (Claude.ai vs Claude Code),
state the primary environment first and handle the secondary as a conditional:

```markdown
## Environment

**Primary**: Claude.ai with computer tools.
**If Claude Code**: Sub-agents are available — use them for parallel test execution.
```

Never write the primary path as an afterthought. The first-described path should be
the one used most often.
