# Skill Interview Questions by Category

Use the relevant section during Phase 1d. Ask universal questions first (in SKILL.md),
then category-specific ones from here. Don't badger — if the user gives a short answer,
move on and note gaps as assumptions to verify during Phase 3 scoring.

## Data Pipeline Skills
(Examples: from-kc-records, ETL extractors, CSV parsers, API ingestors)

5. **Data sources** — What systems/files/APIs does this skill read from? Get exact names,
   formats, and access methods. "Gmail" is not enough — which labels, which senders,
   which attachment types?
6. **Schema** — What does the output data look like? Column names, types, units.
   If writing to a database, which database ID, which tables, which columns?
7. **Deduplication** — How should the skill handle records it's already seen?
   What makes a record "the same"? (Order number? Date + vendor + amount?)
8. **Malformed input** — What happens when input doesn't match the expected format?
   Skip it? Flag it? Attempt partial extraction? This is where most data skills fail.
9. **Volume** — How many records per run? 5? 500? 5000? This changes the approach.

## Diagnostic / Audit Skills
(Examples: ux-diagnostic, code reviewers, compliance checkers)

5. **Scoring dimensions** — What specific things are being evaluated?
   Get the actual rubric, not "quality." Each dimension needs a name and a scale.
6. **Evidence requirements** — Must findings cite specific lines/files/data?
   Or is pattern-level assessment sufficient?
7. **Severity classification** — How are findings ranked? Binary (pass/fail)?
   Tiered (critical/high/medium/low)? Scored (0-10)?
8. **Remediation output** — Does the skill just diagnose, or also produce fix instructions?
   If fixes, what format? (Inline suggestions, CLI prompt, PR diff?)
9. **Baseline comparison** — Should the audit compare against a previous audit?
   Against a standard? Against a reference implementation?

## Workflow Orchestrator Skills
(Examples: from-prompter, skill-forge, multi-phase build workflows)

5. **Phase dependencies** — Which phases require output from previous phases?
   Which can be entered independently? Draw the dependency graph.
6. **Human checkpoints** — Where must the user approve before proceeding?
   Where is autonomous execution safe? Default to more checkpoints, not fewer.
7. **Failure recovery** — If the skill fails mid-workflow, where does the user resume?
   Can partial progress be saved? What state needs to persist between phases?
8. **Customization points** — Which parts of the workflow should the user be able to
   skip, reorder, or configure? Which parts are fixed?
9. **Chaining** — Does this skill's output feed into another skill? (e.g., ux-diagnostic →
   from-prompter). If so, what's the handoff format?

## Content Generator Skills
(Examples: kc-pulse, report generators, artifact builders)

5. **Data sources for content** — Where does the content's data come from?
   Databases, APIs, user input, conversation history?
6. **Template vs. dynamic** — Is the output structure fixed (same sections every time)
   or does it vary based on input? If fixed, provide the exact template.
7. **Update vs. create** — Is this always a fresh creation, or does it update an
   existing artifact? If update, how is the previous version located and diffed?
8. **Audience** — Who reads the output? Technical users, executives, customers?
   This determines vocabulary, detail level, and formatting.
9. **Delivery format** — JSX artifact, Markdown file, DOCX, HTML? Does it need to
   render in Claude.ai's artifact viewer?

## Closing Questions (All Categories)

10. **What should this skill explicitly NOT do?** — Get concrete anti-scope.
    Not "don't be slow" but "don't modify the production database" or
    "don't generate code, only generate the prompt."
11. **What's the worst failure mode?** — What would make the user lose trust?
    Data loss? Wrong calculations? Triggering on the wrong input? Silent errors?
    Build guardrails against the worst failure first.
12. **Priority ranking** — If the skill has to make tradeoffs, what matters most?
    (e.g., "accuracy over speed" or "comprehensive over concise")
