---
name: kcc-scout
description: Surface and rank Tampa Bay area events that KC Clearwater (a booze-free venue in Clearwater, FL) can piggyback on. Trigger when the user asks to find bookable acts or events for KCC, surface nearby touring artists, identify festivals to piggyback, or hunt for venue programming. Common phrasings include "what's coming to clearwater", "any bands touring through tampa bay", "who's in town", "find me an act for KCC", "find me an artist", "what authors are touring", "festivals we could leverage", "we should book someone", "kcc-scout", "scout opportunities" — even if the user does not say "kcc-scout" explicitly. Do not trigger for drafting outreach (use message_compose_v1), ad copy, social posts, past-event lookups, or events outside Tampa Bay. Outputs a scored, ranked markdown table with one outreach hook per opportunity, tour routing callout, miss list, and gaps callout. Reads public web sources only — does not write, post, or send anything.
---

# kcc-scout

## What this skill does

Surface upcoming Tampa Bay events that KC Clearwater (KCC) — a 100-cap booze-free venue in Clearwater, FL — can leverage for bookings, intercepts, or activations. Score each opportunity on Fit, Proximity, Reachability, and Angle Clarity. Return a ranked markdown table with outreach hooks.

**This is signal detection, not outreach.** Outputs are leads, not messages. After this skill surfaces opportunities, drafting actual outreach is a separate task — use the `message_compose_v1` tool or hand the lead to `from-prompter` for outreach prompt crafting.

## Core principle: act type, not venue

The single most important calibration in this skill is recognizing that **an act's bookability for a side-date depends on its tour type, not the venue it's playing.** Venue is a heuristic, not a rule.

- **Type 1 — DIY / self-booked indie tour.** No major label, no national booking agency, route-flexible, often opens for bigger acts on touring legs they self-organize. Side-dates *possible*. Examples of signals: tour announced via the artist's own social, plays 100-500 cap rooms, 5K-50K Spotify monthlies, no UTA/CAA/WME mention.
- **Type 2 — Mid-tier with management.** Booking agent at a smaller agency (Ground Control, Ground Up Music, Paradigm-adjacent), tours 500-2000 cap rooms. Side-dates *sometimes possible*, depends on tour structure.
- **Type 3 — Major-label tour.** UTA / CAA / WME booked, full crew tour, label tour support. Side-dates *almost always blocked* by exclusivity clauses in the tour rider.
- **Type 4 — Tribute / legacy / cover.** Mass-appeal nostalgia acts. No real "side-date" play. Drop unless an unusually strong KCC-fit angle exists.

Venue lineups today happen to cluster — Bayboro Brewing skews Type 1, Jannus Live skews Type 2, Ruth Eckerd Hall / Capitol Theatre skew Type 3-4 — but this can shift quarter to quarter. Score by act type when the data supports it; fall back to venue heuristic only when act-type signals are absent.

## When NOT to use this skill

- User wants to draft outreach to a specific person/act → that's a downstream task; this skill only surfaces opportunities
- User wants ad copy, social posts, or marketing creative → wrong skill
- User asks about past events or historical analysis → this skill is forward-looking
- User wants events outside Tampa Bay (~30mi from 33756) → out of scope

## Prerequisites

Before running, confirm with user (skip if user says "go" or "run it"):

1. **Date window** — default: next 14-60 days
2. **Pursued list** — acts/authors/events already contacted or passed on. Excluded from output. If user has none, proceed without dedup and note it.

## Run sequence

### Phase 1: Sweep aggregators (parallel web_fetch)

Fetch all of these in a single batch — they cover ~70% of hyperlocal signal in 5 calls:

1. `https://ilovetheburg.com/events/` — St. Pete venue aggregator (40+ venues)
2. `https://ilovetheburg.com/st-pete-weekend-events/` — curated weekly digest, higher signal
3. `https://www.dunedin.love/things-to-do-in-dunedin-florida` — Dunedin wellness/indie
4. `https://patch.com/florida/clearwater/calendar` — high noise floor, filter aggressively
5. `https://patch.com/florida/dunedin/calendar` — same caveat

### Phase 2: Sweep venues + tour intelligence (parallel)

6. `https://jannuslive.com/shows/list/` — Jannus Live direct
7. `https://www.bayborobrewing.com/upcoming-events` — Bayboro listening room
8. `https://www.rutheckerdhall.com/events` — REH / Capitol / BayCare Sound / Murray
9. `https://www.bandsintown.com/v/10001649-jannus-live` — Jannus tour routing
10. `https://www.bandsintown.com/v/10192042-bayboro-brewing-co.` — Bayboro tour routing
11. `https://www.bandsintown.com/v/10000614-ruth-eckerd-hall` — REH tour routing

For each artist, check Bandsintown for tour routing — what city plays before/after Tampa Bay. Off-night between two cities is the strongest intercept signal.

**Fallback if a Bandsintown venue page fails:** the IDs above are hardcoded and could break if Bandsintown restructures. If a fetch returns nothing parseable, try (a) `https://www.bandsintown.com/?came_from=257&venue=[venue+name]` search, or (b) the corresponding Songkick venue page. Note any failure in the gaps callout so the skill maintainer can refresh the IDs.

### Phase 3: Sweep trending + niche (parallel)

12. Run `python scripts/parse_reddit.py r/tampa r/StPetersburgFL` — handles fetch + filtering deterministically
13. `https://www.eventbrite.com/d/fl--clearwater/events/`
14. `https://www.eventbrite.com/d/fl--dunedin/events/`

### Phase 4: Dedup + filter

Run `python scripts/dedup_events.py <events.json>` to dedup across sources by normalized (artist, date, venue) tuple. The script is more reliable than LLM-parsed fuzzy matching.

After dedup, drop:
- Outside date window
- On user's pursued list
- Obvious mismatch (sports, kids-only, religious-only, weddings, corporate-only, faith festivals, tribute bands at wineries, anything that won't draw KCC's audience)

### Phase 5: Enrich + classify act type

For surviving items, classify each band/artist by act type (1-4 above). Signal sources:
- Spotify monthly listeners (search the artist; <50K → likely Type 1; >500K → likely Type 3)
- Booking agent mention (search "[artist] booking agent OR management"; UTA/CAA/WME → Type 3)
- Recent venue history (Songkick / Bandsintown past dates; routinely 1000+ rooms → Type 2-3)

Cap enrichment at top 15 candidates by initial Fit score — web_search budget is real, don't enrich every event. Use one targeted search per item to find a contact path:
- Bands: `[artist name] booking agent OR publicist OR management`
- Authors: `[author name] tour manager OR publicist OR speaking agent`
- Local creators: `[name] tampa bay contact OR booking`

If search returns nothing usable, mark "no direct contact found" — don't fabricate.

### Phase 6: Score

Read `scoring-rubric.md` before scoring. Each opportunity gets 0-3 on Fit, Proximity, Reachability, Angle Clarity. Total 0-12.

**Threshold: surface only items scoring ≥7.** This threshold is provisional — after scoring, run `python scripts/score_calibrator.py <scored.json>` to check distribution. The script recommends raising or lowering the threshold based on whether the run yielded too few or too many items at ≥7.

### Phase 7: Output

Read `output-format.md` for the exact table format. Output:
- Run summary line (sources swept, items found, threshold used)
- Main table (top 10 opportunities, with Tier and Type labels)
- Tour routing callout (if any intercepts found)
- Just-below-threshold miss list (3-5 items)
- Gaps callout (what we couldn't see)

## Anti-patterns

These come up repeatedly. Each one explains why the failure mode happens and what to do instead.

**Don't enrich every event.** Web_search budget is real. With 50+ events surviving filtering, one search each blows the budget on noise. Instead: rank by raw Fit score from sweep data alone, then enrich only the top 15.

**Don't fabricate contact info.** If a search returns no publicist or agent, the right answer is to mark the contact path as missing — the user can decide whether a social DM is worth it. Inventing names creates downstream errors when the user actually tries to reach out.

**Don't pitch Type 3 acts as intercepts.** Major-label tours typically have exclusivity clauses that block side-dates within a radius of the contracted show. The realistic exception is when the artist themselves cares about the angle (e.g., publicly sober artist on a sober-touring leg), but those exceptions are rare enough that the default should be afterparty/M&G framing. Instead: route Type 3 acts to "afterparty / meet-and-greet at booze-free venue near stage door" angle, or drop them entirely if the audience doesn't fit KCC.

**Don't surface uncertain items.** If a date or venue is ambiguous in the source, surfacing it forces the user to do verification work the skill should have done. Move ambiguous items to the gaps callout instead.

**Don't pad the table.** A 5-row table of strong opportunities beats a 25-row padded one. The user reads many of these — every weak row degrades the signal.

## Verification before output

The checklist below maps to specific failure modes seen in earlier iterations. Each check is a guardrail against a real way this skill has produced bad output.

```
[ ] Every row has all 4 score components (F·P·R·A)
    — without these, the user can't tell why a row was surfaced
[ ] Every row's total ≥ threshold (provisional 7/12 or calibrated)
    — ranking matters less than ruthless filtering
[ ] Every row has a clickable source URL
    — claims without sources can't be verified or actioned
[ ] Every row has a one-line outreach hook matched to its act type
    — wrong-type hooks make the lead useless to downstream tools
[ ] No duplicates across sources (script-verified)
    — same event from 3 aggregators counted as 3 looks like padding
[ ] Tour routing noted for any Type 1-2 artist with off-night
    — this is the key bookable signal; missing it is a missed opportunity
[ ] Type 3 acts framed as afterparty/M&G, not intercepts
    — wrong framing wastes the user's outreach effort
[ ] Pursued list items excluded
    — re-surfacing already-pursued leads is a respect-for-time issue
[ ] Date window respected
    — out-of-window items are noise
[ ] Threshold-tuning note included from score_calibrator output
    — surfaces calibration drift before it becomes a habit
```

## Reference files

- `sources.md` — full source inventory with reliability notes and brittleness warnings
- `scoring-rubric.md` — exact 0-3 definitions with archetypal calibration examples
- `outreach-hooks.md` — one-line hook templates by act type and opportunity category
- `output-format.md` — exact markdown table format and miss-list structure
- `scripts/dedup_events.py` — deterministic event deduplication
- `scripts/parse_reddit.py` — Reddit JSON fetch + filter
- `scripts/score_calibrator.py` — distribution analysis and threshold recommendation

## Operational notes

- **Runtime:** ~3-5 min per full sweep with parallel fetches
- **Cadence:** Designed for weekly run. More frequent = mostly the same events.
- **No persistence:** Skill doesn't write to D1. User maintains the pursued list.
- **Source brittleness:** If a venue site redesigns its HTML, fetches degrade silently. Watch for unusually empty sweeps as a signal.
- **Downstream:** Pass surfaced opportunities to `message_compose_v1` (for direct outreach drafting) or `from-prompter` (to craft a Claude Code agent prompt for batched outreach).

## Concrete handoff example

After kcc-scout outputs a ranked table, a typical follow-up flow:

> User: "Draft a cold email for row 1 (the indie folk artist)"
>
> Claude: [recognizes outreach drafting, switches to message_compose_v1 with context: "kcc-scout surfaced [artist] — Type 1 DIY tour, off-night [date+1] between [city A] and [city B], manager email [contact] from publicist search. Hook: 'Off-night intercept, KCC is a 100-cap booze-free room in Clearwater that fits a stripped-down set.' Generate 2-3 strategic variants — one direct/transactional, one warmer relationship-builder, one more pitch-y with KCC's positioning."]

Or for batched outreach:

> User: "Take all 8 surfaced acts and draft outreach prompts for me to run via Claude Code"
>
> Claude: [hands rows to from-prompter] "Build a Claude Code prompt that takes this kcc-scout output as input and drafts personalized outreach for each row, respecting act-type framing (Type 1/2 = intercept hooks, Type 3 = afterparty/M&G, etc.)."

The kcc-scout output is designed to feed directly into either path — the Type column and Hook column carry the framing context that downstream tools need.
