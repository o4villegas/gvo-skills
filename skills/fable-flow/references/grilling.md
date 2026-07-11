# Grilling — opt-in deep plan interrogation

> Vendored for the `fable-flow` skill. Adapted from the `grilling` skill in
> [jjilli/fable-flow](https://github.com/jjilli/fable-flow) (MIT), itself adapted from Matt
> Pocock's `grilling` skill (https://github.com/mattpocock/skills).

Invoke this **only when the user explicitly asks to be grilled** (or to grill the plan/design) —
they say "grill me", "grill the plan", "grilling", or otherwise ask to pressure-test the design.
Do **not** auto-invoke it for ordinary planning or clarification; the default clarify step
(card-based multiple-choice questions via `AskUserQuestion`) is a separate, lighter thing.

When they have asked for it:

Interview the user relentlessly about every aspect of the plan until you reach a shared
understanding. Walk down each branch of the design tree, resolving dependencies between decisions
one by one. For each question, provide your recommended answer.

Ask the questions **one at a time**, waiting for feedback on each before continuing. Asking
multiple questions at once is bewildering.

If a *fact* can be found by exploring the codebase, look it up rather than asking — spend the
user's attention only on decisions. The *decisions* are theirs: put each one to them and wait for
the answer.

Do not enact the plan until the user confirms you have reached a shared understanding.

In this pipeline, grilling sits **before** the Plan phase — it hardens the task and its design
decisions so the architect plans against a settled intent rather than guesses. Once grilling ends
in a shared understanding, fold the resolved decisions into `.fable-flow/task.md` and proceed to
planning.
