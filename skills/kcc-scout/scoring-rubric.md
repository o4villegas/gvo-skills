# Scoring Rubric

Each opportunity scored 0-3 on four dimensions. Total 0-12. Threshold: surface only items scoring ≥7 (provisional — recalibrate via `score_calibrator.py`).

## Fit (0-3) — Audience overlap with KCC

KCC's core audience: 21-35, alternative nightlife seekers, sober-curious, electronic/indie music fans, wellness-oriented, creative/artistic, kava-curious, festival/burner-adjacent.

- **3 — Bullseye:** Indie/electronic/alt music; sober-curious wellness; queer/inclusive scenes; underground/DIY culture; psychedelic-adjacent (cannabis or mushroom-friendly); creative/maker community. The act or event would feel at home at KCC even if it weren't booked there.
- **2 — Strong overlap:** Singer-songwriters; alt-leaning comedy; literary fiction authors; yoga/movement teachers; podcasters with engaged Tampa Bay following; themed dance nights with culture-fan appeal.
- **1 — Partial overlap:** Tribute bands; classic rock; mainstream comedians; generic wellness; mass-market authors. Some KCC audience would attend but it's not a natural fit.
- **0 — Mismatch:** Country (broadly); Christian rock; kids' shows; sports; corporate/networking; religious events; mainstream pop; anything where KCC vibe would clash. Most Patch listings score 0 here.

## Proximity (0-3) — Date proximity, INVERTED

Counterintuitive but correct: closer = harder to coordinate, lower score.

- **3 — Sweet spot:** 4-8 weeks out. Lead time to coordinate, schedule still flexible.
- **2 — Workable:** 2-4 weeks OR 8-12 weeks out.
- **1 — Tight or distant:** 1-2 weeks out OR 12+ weeks out.
- **0 — Unworkable:** <1 week out.

## Reachability (0-3) — Found contact path?

After targeted enrichment search:

- **3 — Direct contact:** Publicist, manager, or booking agent named with email or contact form.
- **2 — Indirect contact:** Agency/management company found (no individual); active social DM viable; or local promoter associated with the act is reachable.
- **1 — Public-only:** Only fan-facing channels (artist's general contact form, bookstore's events email).
- **0 — No path:** Cold social DM is the only option.

## Angle Clarity (0-3) — How obvious is the KCC hook?

This dimension is **act-type-aware**. Read the "Core principle" section in SKILL.md before scoring this.

### For Type 1 acts (DIY / self-booked indie tour):

The intercept play is real here. Score on how obvious it is.

- **3:** Off-night intercept with clear routing (artist plays Tampa Friday, off Saturday, Orlando Sunday — KCC pitch is for Saturday). Hook writes itself.
- **2:** Tour routing is plausible for an intercept but not perfectly aligned (e.g., off-day exists but is a Tuesday and the artist's audience may not show up midweek).
- **1:** No off-night nearby; weak intercept angle.
- **0:** No bookable angle — drop or move to "host them" framing if possible.

### For Type 2 acts (mid-tier with management):

Side-date intercepts are harder but not impossible. Mid-tier tours sometimes accept off-night supporting slots if the venue offers something the main venue doesn't (e.g., booze-free option for sober-touring artists, intimate room for stripped-down sets).

- **3:** Strong fit reason exists (artist is publicly sober, tour has acoustic side-element, etc.) AND off-night routing works.
- **2:** One of the above conditions met.
- **1:** Neither condition strongly met.
- **0:** Drop.

### For Type 3 acts (major-label tour):

**Side-date intercepts are not realistic for this tier.** Score Angle Clarity for the afterparty / meet-and-greet angle instead:

- **3:** Show is at a venue *immediately walkable* from KCC (e.g., Capitol Theatre at 405 Cleveland St, ~5 min walk) AND audience fits KCC. Walkable proximity is the key — afterparty plays only work when foot traffic is obvious to attendees.
- **2:** Show creates spillover audience near KCC but the hook needs framing.
- **1:** Show is geographically close but audience mismatch makes afterparty thin.
- **0:** Drop.

### For Type 4 acts (tribute / legacy / cover):

Almost always 0. Drop unless something unusual fits (e.g., a synth-wave tribute night that overlaps with KCC's electronic crowd).

### For local creators / no-event "host them" plays:

- **3:** Local creator with engaged following, no event scheduled — KCC could host a listening party / Q&A / workshop.
- **2:** Clear residency/recurring play (e.g., wellness instructor, daytime slot fits).
- **1:** One-off only.
- **0:** Mismatch.

### For festivals / multi-venue events:

- **3:** Official off-site / afterparty pitch is obvious.
- **2:** Adjacent programming pitch (workshops, listening sessions).
- **1:** Spillover only, no formal connection.
- **0:** No connection to KCC audience.

## Threshold

- **≥10/12** — Top tier, lead with these
- **7-9/12** — Solid, surface in main table
- **5-6/12** — Miss list (mention but don't lead with)
- **<5/12** — Drop entirely

After scoring, run `score_calibrator.py` — it analyzes distribution and recommends raising the threshold (if too many items scored ≥7) or lowering (if too few).

## Calibration archetypes

These are deliberately generic so they age well as specific bands rotate.

**Indie singer-songwriter, ~20K Spotify monthlies, Type 1 tour, playing Bayboro 6 weeks out, manager email findable:**
Fit 3 (indie listening room) + Proximity 3 (6 weeks) + Reach 3 (manager) + Angle 3 (off-night intercept, Bayboro is closest analog to KCC) = **12/12** — lead with this.

**Mid-tier indie alt-rock band, ~200K monthlies, Type 2, playing Jannus 4 weeks out, off-night between Tampa and Orlando:**
Fit 3 + Proximity 3 + Reach 2 (label/management findable, no individual) + Angle 3 (clear off-night intercept) = **11/12** — lead with this.

**UK shoegaze act, Type 1-2, playing Jannus 3 weeks out, no clear off-night, US tour contact unclear:**
Fit 3 + Proximity 2 + Reach 1 + Angle 1 (no off-night intercept) = **7/12** — borderline surface.

**Major-label country act, Type 3, playing REH 6 weeks out:**
Fit 0 → drop without further scoring.

**Bee Gees tribute band, Type 4, playing REH 3 weeks out:**
Fit 1 + Proximity 2 + Reach 0 (tribute bands rarely have findable contacts) + Angle 0 = **3/12** — drop.

**Comedy act with alt audience, Type 3, playing Capitol Theatre 5 weeks out:**
Fit 2 + Proximity 3 + Reach 1 (theater-only contact, agent unreachable for this scale) + Angle 2 (afterparty 200ft away, KCC fits the demo) = **8/12** — surface as afterparty/M&G play.

**Local sound bath instructor, ~12K IG, no scheduled events, recurring Dunedin events:**
Fit 3 + Proximity (treat "anytime" as 2) + Reach 2 (IG DM) + Angle 3 (host them at KCC) = **10/12** — lead with this as a "host them" play.

**Picture-book author, Type 2 author tour, 5 weeks out at Tombolo Books, publicist listed:**
Fit 2 + Proximity 3 + Reach 3 + Angle 2 (afterparty Q&A at KCC for adult lit-fic crowd) = **10/12** — lead with this.

**Faith-based festival at Coachman Park:**
Fit 0 → drop without continuing.

**Cultural/religious community festival:**
Fit 0 → drop.

**Improv comedy at a winery, mainstream demographic:**
Fit 1 + Proximity (varies) + Reach (varies) + Angle 1 — typically lands 5-6/12, miss list.
