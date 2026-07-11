# Build patterns & seam traps

> Vendored, self-contained copy for the `fable-flow` skill. Adapted faithfully from the
> `build-patterns` skill in [jjilli/fable-flow](https://github.com/jjilli/fable-flow) (MIT).
> `fable-prompting.md` covers *how to prompt*; this covers *what tends to break and what tends
> to work* when the plan turns into code. None of this overrides the plan's Contracts — it's the
> judgment to apply within them. The architect, implementer, and reviewer prompts each point here.

## The core failure mode: green per track, broken at the seam

The single most common real bug that survives per-track testing lives where a track meets
something its own unit tests don't exercise: another track's code, or the live runtime. A round
can show every track's suite green and still be broken. Prove each round with **one real
end-to-end run through the actual runtime path**, not only the unit suite. Seams unit tests
routinely miss:

- **Background threads, queues, event loops.** The pure function is tested; the wiring that feeds it from the drain thread / worker / async loop is not. Test the dispatch, not just the callee.
- **Non-HTTP request scopes.** A gate built on an HTTP-only base (e.g. Starlette `BaseHTTPMiddleware`) silently skips WebSocket and other scopes — an auth or rate-limit middleware that looks complete can leave the live event socket wide open. Test the socket/stream path explicitly, not just `GET /`.
- **Real timing and sampling.** A loop gated by wall-clock fps/interval behaves differently under a tight test loop than in production. Make the seam deterministic (inject the clock, feed a fixed frame/event sequence) so the test actually pins the wiring instead of passing by luck.

The architect should name the round's riskiest seam and require a concrete end-to-end check of
it; the integration reviewer should assume the seam is the bug until a real run says otherwise.

## Reusable patterns (each earned, each made later rounds cheaper)

- **Provider-adapter, never-raises.** For any optional capability (an AI model, an external service, a hardware backend): a `make_X(config)` factory that NEVER raises when the optional dependency is absent, a single typed error that wraps *every* failure mode, a lazy `import` inside the method, and a zero-dependency default that CI actually exercises. Optional providers degrade to the default; they never crash the pipeline.
- **Enqueue-only worker.** Push heavy or optional work onto a bounded-queue daemon thread off the hot path. `submit()` never blocks and never raises (log-and-drop when full); the stop flag is named so it can't shadow a base-class attribute (`_stop_event`, not `_stop`); every failure is logged, never propagated to the caller.
- **Guarded schema migration.** `CREATE TABLE IF NOT EXISTS` never adds a column to a table that already exists. Add new columns at startup with `PRAGMA table_info` + `ALTER TABLE ADD COLUMN`. When you extend a prune/cascade routine, keep its signature and return type stable so callers and their exact-shape tests don't move.
- **Invariant validators that don't break existing input.** A newly-added required-invariant check can reject a config that was valid yesterday. Distinguish an *explicit* misconfiguration from a *defaulted* value the user never set (e.g. pydantic `model_fields_set`): reject the former, clamp/upgrade the latter. Ship compatibility by default, not a startup crash on upgrade.
- **Contract expansion is additive.** When a wire/dict/DB shape gains a field, exact-equality tests (`set(obj) == KEYS`) will break by design. Add the key to the expected set — don't loosen the assertion to `>=` — and fix the fixtures in the same change. Expect this whenever a track widens a shared shape.
- **Record everything, rate-limit the noise.** Persist every event/hit; gate the user-facing notification behind a per-source cooldown so a lingering condition can't storm the user. The record is complete; the interruptions are bounded.

## Verification discipline (a green suite is necessary, not sufficient)

- **One real roundtrip per round.** Drive the feature through the real runtime and show the concrete result: a request is 401 without a token and 200 with it; a matching appearance on a second camera fires exactly one hit; an unreachable stream fails within its timeout rather than hanging. This catches seam bugs the unit suite structurally cannot.
- **Visual check for UI work.** Build-clean and tests-green still ship layout regressions — an unconstrained thumbnail, a bar that overflows its track. A headless-browser screenshot against seeded data is cheap and catches what assertions miss. Worth doing for any user-facing surface. (See `frontend-aesthetics.md`.)
- **Deterministic tests for time/IO seams.** Fake the clock, the capture, the socket. A test that depends on wall-clock timing or real network is flaky, and a flaky seam test is worse than none because it trains everyone to ignore it.

## Reviewer traps (don't manufacture false positives)

- Before reporting a **missing test**, grep for the *symbol under test* across all test files, not just for a `<Name>.test` file — coverage frequently lives in a sibling. A confidently-wrong "no coverage" finding costs the pipeline a round.
- Don't trust a capability claim from a comment or a track report; verify the behavior on the actual runtime before building a finding on it.
