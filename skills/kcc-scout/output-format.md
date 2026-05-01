# Output Format

## Run summary line (one line, top of output)

```
Swept [N] sources, [N] events found, [N] passed filtering, [N] scored ≥ threshold. Date window: [start] to [end]. Threshold: [X/12] ([provisional | calibrated to N/12 because of distribution]).
```

If `score_calibrator.py` recommends adjustment, mention it here:
- "First run yielded [too many] items at ≥7 — raised threshold to 8 for this output."
- "First run yielded [too few] items at ≥7 — lowered threshold to 6, treat output as exploratory."

## Main table

Markdown table, sorted by total score descending. Columns:

| # | Opportunity | Type | Date | Venue | Score | Hook | Source |

- **#** — row number
- **Opportunity** — Artist/author/event name + 1-line context (e.g., "Indie folk, ~12K Spotify monthlies, debut album tour")
- **Type** — Act type (1, 2, 3, 4) for bands; Author / Local / Festival / Wellness / DJ / Meetup for non-bands. Tells the reader how to interpret the hook.
- **Date** — exact date or window
- **Venue** — where the underlying event is happening (NOT KCC)
- **Score** — `Total/12 (F·P·R·A)` — e.g., `10/12 (3·3·2·2)`
- **Hook** — one-line outreach angle from `outreach-hooks.md`, matched to type
- **Source** — clickable URL to where the opportunity was discovered

Cap main table at top 10 rows. If more than 10 score ≥ threshold, mention count below table: "+ N more scoring 7-8/12 — ask if you want them."

## Tour routing callout (if applicable)

Below main table, separate section if any Type 1 or Type 2 intercept opportunities found:

```
**Tour routing intercepts:**
- [Artist] plays [city A] [date], [city B] [date+2] — KCC pitch is for [date+1]
- [Artist] plays [city] [date], [city] [date+1] — no off-night, lower priority
```

## Just-below-threshold miss list

Items scoring 5-6/12 that user might want to override:

```
**Just below threshold:**
- [Artist] (5/12) — strong fit but no contact path. Worth a social DM?
- [Author] (6/12) — date is in 4 days, too tight to coordinate
```

3-5 items max. Skip section if nothing notable.

## Gaps callout

Always include — this protects against false confidence in completeness:

```
**What we couldn't see this run:**
- Influencer geo-trending (no clean source without paid social APIs)
- Private/Eventbrite-internal events
- [Specific source X failed to load — retry next run]
- [Any other notable gaps from this specific sweep]
```

## Threshold-tuning note (when calibrator recommends)

```
**Threshold note:** This run used [X/12] threshold. Distribution: [N] items at 10-12, [N] at 8-9, [N] at 7. [Recommendation from score_calibrator.py.]
```

## Example output (illustrative — placeholders shown so the example doesn't go stale)

The structure below is the actual format you should produce. Replace `[bracketed]` items with real values from your run, and use real numbers in the summary line (`14 sources, 89 events found, 18 passed filtering, 6 scored ≥7`).

```
Swept [N_sources] sources, [N_events] events found, [N_passed] passed filtering, [N_scored] scored ≥7. Date window: [start_date] to [end_date]. Threshold: provisional 7/12.

| # | Opportunity | Type | Date | Venue | Score | Hook | Source |
|---|---|---|---|---|---|---|---|
| 1 | [Indie folk artist] — DIY tour, ~20K monthlies | 1 | [date] | Bayboro | 11/12 (3·3·3·2) | Off-night [date+1] between [city] and [city] — booze-free 100-cap room | bandsintown.com/... |
| 2 | [Mid-tier indie band] — Type 2, off-night routing | 2 | [date] | Jannus | 10/12 (3·3·2·2) | Booze-free off-night option, intimate listening room format | jannuslive.com/... |
| 3 | [Author] — picture book tour, [genre] | Author | [date] | Tombolo | 9/12 (2·3·3·1) | Add daytime Q&A + tea pairing at KCC | ilovetheburg.com/... |
| 4 | [Local sound bath instructor] — ~12K IG | Wellness | recurring | n/a (host at KCC) | 8/12 (3·2·2·1) | Sound bath residency at booze-free Clearwater venue | dunedin.love/... |

**Tour routing intercepts:**
- [Indie folk artist]: [city] [date-1] → [city] [date+2]. Off-night [date+1] = prime KCC pitch.

**Just below threshold:**
- [Comedy act] at Capitol Theatre (6/12) — afterparty angle, reachability is hard at this venue tier
- [Themed dance night] (5/12) — wrong format for KCC, could pitch own version instead

**What we couldn't see this run:**
- Influencer geo-trending (no clean source without paid social APIs)
- Private events / corporate retreats
- Any source failures noted

**Threshold note:** This run used 7/12. Distribution: 2 items at 10-12, 2 at 8-9, 0 at 7. Density looks right; keep 7/12 for next run.
```

## Tone

- Direct, not breathless. No "amazing opportunity!" language.
- Honest about weak signals. If something scored 7 just barely, say so in the row context.
- Don't oversell. The user reads many of these — efficiency > enthusiasm.
- Type labels are non-negotiable — they tell user how to read the hook.
- The example above uses placeholders intentionally so it doesn't go stale as specific bands rotate through Tampa Bay.
