# Prompting Claude Fable 5 — the working reference

> Vendored, self-contained copy for the `fable-flow` skill. Adapted faithfully from
> the `fable-prompting` skill in [jjilli/fable-flow](https://github.com/jjilli/fable-flow)
> (MIT), itself distilled from the official guide:
> https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5
> Consult the official guide for updates; this file is the working reference the pipeline follows.

## The one-line summary

Fable 5 is steered with **brief goal-and-constraint instructions**, not step-by-step
scaffolding. Prompts written for Opus/Sonnet-era models are usually **too prescriptive**
for Fable 5 and actively degrade its output. State the goal, the constraints, and the
boundaries — then let it work.

## How Fable prompting differs from past models

1. **De-prescribe.** Enumerated step lists, "CRITICAL: YOU MUST" language, and forced-cadence scaffolding ("summarize after every 3 tool calls") that older models needed now reduce quality. Prefer stating the goal and constraints over enumerating the steps. Review inherited prompts and delete instructions whose default behavior is already good.
2. **One brief instruction beats an enumerated list.** Instruction-following is strong enough that a single sentence steers a whole class of behavior. You do not need to name every bad pattern.
3. **Give the full task specification up front.** Fable 5 excels at long-horizon work when the first turn carries the complete spec — goal, constraints, definition of done. Ambiguous, drip-fed specs waste tokens and reduce quality.
4. **Give the reason, not only the request.** Template: `I'm working on [the larger task] for [who it's for]. They need [what the output enables]. With that in mind: [request].`
5. **Expect longer turns.** Single requests on hard tasks can run many minutes; autonomous runs for hours. Design harnesses to check in asynchronously rather than blocking, and set timeouts accordingly.
6. **Delegate freely — asynchronously.** Fable 5 dispatches and manages parallel subagents dependably. Don't suppress delegation (a prior-model guardrail); instead say *when* delegation is appropriate. Prefer long-lived subagents that keep context over spawn-and-block.
7. **Fresh-context verifiers beat self-critique.** For verification, spawn separate verifier subagents with clean context rather than asking the worker to critique its own output.
8. **Give it a memory surface.** Even a plain Markdown file. Fable 5 performs notably better when it can record and consult lessons across runs.
9. **Never ask it to echo its reasoning in the response.** "Show your thinking / explain your reasoning verbatim" instructions can trigger the `reasoning_extraction` refusal category. Read `thinking` blocks (API) instead, or have it report conclusions.
10. **Don't surface context-budget countdowns.** Remaining-token counters trigger premature wrap-up behavior. If unavoidable, add the ample-context reassurance snippet.

## Effort levels (the primary quality/latency/cost control)

API: `output_config.effort` — `low | medium | high | xhigh | max`. In Claude Code, effort
follows the session/agent configuration rather than a per-prompt parameter, so encode intent
by role: give planning/review roles harder, wider-scope prompts and implementation roles
tightly-scoped tracks.

| Level | Use for |
|---|---|
| `max` | Extremely hard, latency-insensitive problems; prone to overthinking on routine work |
| `xhigh` | Most capability-sensitive coding/agentic work (Claude Code's default tier) |
| `high` | Default for most tasks; excellent verification behavior |
| `medium` | Routine implementation of a well-specified plan |
| `low` | Short, scoped, latency-sensitive tasks; still strong on Fable 5 — often exceeds prior models' `xhigh` |

The roles in this pipeline map as: **planning = xhigh** (one agent whose output gates
everything downstream — worth the ceiling), **implementation = medium** (narrow, pre-planned
track), **review = high** (adversarial verification).

> **Harness note for this skill.** The Agent tool available in Claude Code Desktop sets
> `model` (`sonnet | opus | haiku | fable`) and `isolation` per call, but does **not** expose a
> per-call `effort` parameter — effort follows the session/agent config. So the pipeline realizes
> effort intent three ways: (a) **model choice** per role (the larger lever — Sonnet recon / Fable
> build / Opus review), (b) **prompt scope** (planning/review prompts are wide and adversarial;
> implementer prompts are tightly scoped to one pre-planned track), and (c) an optional path for
> users who want literal per-role effort — install role subagents with `effort:` frontmatter and
> spawn them by `subagent_type`, or set `CLAUDE_CODE_SUBAGENT_MODEL`. The default single-skill path
> does not require that.

## Verbatim steering snippets

Copy these exactly; they are tested wordings from the official guide. When the orchestrator
or a spawned agent needs one of these behaviors, paste the snippet verbatim into that prompt —
do not paraphrase.

**Anti-overplanning** (ambiguous tasks):
> When you have enough information to act, act. Do not re-derive facts already established in the conversation, re-litigate a decision the user has already made, or narrate options you will not pursue in user-facing messages. If you are weighing a choice, give a recommendation, not an exhaustive survey. This does not apply to thinking blocks.

**No unrequested tidying** (higher effort):
> Don't add features, refactor, or introduce abstractions beyond what the task requires. A bug fix doesn't need surrounding cleanup and a one-shot operation usually doesn't need a helper. Don't design for hypothetical future requirements: do the simplest thing that works well. Avoid premature abstraction and half-finished implementations. Don't add error handling, fallbacks, or validation for scenarios that cannot happen. Trust internal code and framework guarantees. Only validate at system boundaries (user input, external APIs). Don't use feature flags or backwards-compatibility shims when you can just change the code.

**Brevity / lead with the outcome:**
> Lead with the outcome. Your first sentence after finishing should answer "what happened" or "what did you find": the thing the user would ask for if they said "just give me the TLDR." Supporting detail and reasoning come after. Being readable and being concise are different things, and readability matters more. The way to keep output short is to be selective about what you include (drop details that don't change what the reader would do next), not to compress the writing into fragments, abbreviations, arrow chains like A → B → fails, or jargon.

**Checkpoints — pause only when genuinely needed:**
> Pause for the user only when the work genuinely requires them: a destructive or irreversible action, a real scope change, or input that only they can provide. If you hit one of these, ask and end the turn, rather than ending on a promise.

**Grounded progress claims** (long runs — nearly eliminates fabricated status reports):
> Before reporting progress, audit each claim against a tool result from this session. Only report work you can point to evidence for; if something is not yet verified, say so explicitly. Report outcomes faithfully: if tests fail, say so with the output; if a step was skipped, say that; when something is done and verified, state it plainly without hedging.

**Boundaries** (prevents unrequested actions):
> When the user is describing a problem, asking a question, or thinking out loud rather than requesting a change, the deliverable is your assessment. Report your findings and stop. Don't apply a fix until they ask for one. Before running a command that changes system state (restarts, deletes, config edits), check that the evidence actually supports that specific action. A signal that pattern-matches to a known failure may have a different cause.

**Subagent delegation:**
> Delegate independent subtasks to subagents and keep working while they run. Intervene if a subagent goes off track or is missing relevant context.

**Memory discipline:**
> Store one lesson per file with a one-line summary at the top. Record corrections and confirmed approaches alike, including why they mattered. Don't save what the repo or chat history already records; update an existing note rather than creating a duplicate; delete notes that turn out to be wrong.

**Autonomous pipeline reminder** (prevents rare early stopping):
> You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking "Want me to…?" or "Shall I…?" will block the work. For reversible actions that follow from the original request, proceed without asking. Offering follow-ups after the task is done is fine; asking permission after already discussing with the user before doing the work is not. Before ending your turn, check your last paragraph. If it is a plan, an analysis, a question, a list of next steps, or a promise about work you have not done ("I'll…", "let me know when…"), do that work now with tool calls. End your turn only when the task is complete or you are blocked on input only the user can provide.

**Context reassurance** (only if a token countdown is visible):
> You have ample context remaining. Do not stop, summarize, or suggest a new session on account of context limits. Continue the work.

**Self-verification cadence** (long builds):
> Establish a method for checking your own work at an interval of [X] as you build. Run this every [X interval], verifying your work with subagents against the specification.

**Long-run communication style** (final summaries after many tool calls):
> Terse shorthand is fine between tool calls (that's you thinking out loud, and brevity there is good). Your final summary is different: it's for a reader who didn't see any of that. Write it as a re-grounding, not a continuation of your working thread: the outcome first, then the one or two things you need from them, each explained as if new. Write complete sentences. Spell out terms. Don't use arrow chains, hyphen-stacked compounds, or labels you made up earlier. If you have to choose between short and clear, choose clear.

## Anti-patterns checklist (audit inherited prompts for these)

- [ ] Step-by-step procedures where a goal + constraints would do
- [ ] "CRITICAL / YOU MUST / If in doubt, do X" pressure language
- [ ] Forced progress-update cadence ("after every N tool calls…")
- [ ] Instructions to reproduce/echo internal reasoning in the response (`reasoning_extraction` refusal risk)
- [ ] Subagent-suppression guardrails from prior models
- [ ] Visible context/token countdowns
- [ ] Verbosity hacks (fragments, abbreviations) instead of selectivity
- [ ] Drip-fed specs across many turns instead of one complete first turn

## Safety note (why this skill carries an Opus fallback)

Fable 5 runs safety classifiers targeting offensive cybersecurity, biology/life-sciences
methods, and reasoning extraction. Benign adjacent work (security tooling, life sciences) can
occasionally trip them — on the API this surfaces as `stop_reason: "refusal"`; configure fallback
to `claude-opus-4-8`. In Claude Code, if a Fable subagent declines a benign task, re-run that
stage with the agent's `model` set to `opus`.
