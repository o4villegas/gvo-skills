# Sources

All URLs verified against live web data during v2 build. Brittleness notes flag what to watch for as sources evolve.

## Tier 1 — Aggregators (high coverage, single fetch)

### ilovetheburg.com/events/
- **Catches:** St. Pete events across MFA, Mahaffey, Tropicana, Greenlight Cinema, Bayboro Brewing, Imagine Museum, Hollander Hotel, Boyd Hill Nature Preserve
- **Format:** WordPress + The Events Calendar plugin, structured HTML
- **Reliability:** High — well-maintained, weekly updates
- **Brittleness:** If they switch off The Events Calendar plugin, parsing breaks. Check page structure if a sweep returns ~0 events.

### ilovetheburg.com/st-pete-weekend-events/
- **Catches:** Curated weekly digest with editorial voice
- **Reliability:** High — editorially filtered, less noise than raw archive
- **Brittleness:** Editorial cadence depends on the publication continuing. If Lando notices the digest is stale (>2 weeks old), drop this source for the run.

### dunedin.love/things-to-do-in-dunedin-florida
- **Catches:** Dunedin wellness, yoga, sound baths, indie events, listening parties
- **Reliability:** High — hyperlocal editorial, weekly cadence
- **Brittleness:** Single-author blog. If the author stops posting, source degrades.

### patch.com/florida/clearwater/calendar
- **Catches:** Clearwater + Largo + Safety Harbor, mix of community + commercial submissions
- **Reliability:** Medium — user-submitted, heavy spam (estate sales, faith events, tribute bands)
- **Brittleness:** Stable platform, but signal-to-noise is poor. Expect ~80% drop rate after filtering.

### patch.com/florida/dunedin/calendar
- **Catches:** Dunedin + East Lake suburbs
- **Reliability:** Medium — slightly better signal than Clearwater Patch due to Dunedin's cultural mix

## Tier 2 — Venue + tour intelligence

The skill scores by **act type** (see SKILL.md), not venue. Venue tendencies below are useful heuristics for prioritizing fetches and reading tour routing data, but treat them as drift-prone.

### jannuslive.com/shows/list/
- **Tendency:** Mixed — historically books across rock, reggae, hip-hop, electronic, alternative, indie. Mostly Type 2 with occasional Type 1 and Type 3.
- **Format:** WordPress + The Events Calendar plugin
- **Reliability:** High — venue-direct
- **Brittleness:** Same as ilovetheburg — depends on TEC plugin staying in place

### bayborobrewing.com/upcoming-events
- **Tendency:** Strongest Type 1 signal in Tampa Bay — DIY/indie listening room programming. Closest structural analog to KCC.
- **Reliability:** High — venue-direct, smaller event volume
- **Brittleness:** Smaller venue means fewer events; sometimes a sweep returns sparse results legitimately.

### rutheckerdhall.com/events
- **Tendency:** Mostly Type 3-4 (major-label tours, tributes, legacy acts, country, comedy). Capitol Theatre (within REH umbrella) is walkable from KCC and occasionally hosts Type 2 folk/comedy that *could* support side-dates — don't auto-rule-out, check act type per item.
- **Reliability:** High — institutional venue, stable site
- **Brittleness:** Custom CMS (carbonhouse). Less likely to change but harder to debug if it does.

### bandsintown.com/v/[venue-id] (3 venues)
Tour routing intelligence. Click into artist pages from venue listings to see full tour routes — off-nights between two cities are the strongest intercept signals.

- `bandsintown.com/v/10001649-jannus-live`
- `bandsintown.com/v/10192042-bayboro-brewing-co.`
- `bandsintown.com/v/10000614-ruth-eckerd-hall`

**Reliability:** High. **Brittleness:** Bandsintown URL structure has been stable for years but they could change their public HTML at any time. If a fetch returns no tour data, fall back to Songkick venue pages as backup (`songkick.com/venues/[id]-[slug]`).

## Tier 3 — Trending + niche

### Reddit (via scripts/parse_reddit.py)
- **Catches:** Trending local topics, viral moments, local creator buzz, Reddit-organized meetups
- **Subreddits:** r/tampa (251K members), r/StPetersburgFL (active)
- **Note:** r/ClearwaterFlorida exists but only ~850 members — basically dead, not worth the fetch
- **Reliability:** Medium — high noise floor, requires aggressive filtering (handled by script)

### eventbrite.com/d/fl--clearwater/events/ + /d/fl--dunedin/events/
- **Catches:** Workshops, niche meetups, fitness/wellness, networking, classes
- **Reliability:** Medium — heavy commercial spam (CPR classes, sales workshops). Filter aggressively.
- **Brittleness:** Eventbrite frequently A/B tests their public pages. Watch for layout changes.

## Sources NOT used (and why)

- **Ticketmaster, AXS, LiveNation** — mostly redirect to venues already covered
- **Pinellas Film Commission permits** — not publicly listed (FOIA only). Actor/filming detection stays a gap.
- **Visit St Pete-Clearwater official events** — large festivals already in Patch/iLoveTheBurg
- **Direct Tombolo Books / Haslam's / Inkwood** — covered by ilovetheburg aggregation
- **JamBase, concertlands** — secondary aggregators with no signal Bandsintown lacks
- **patch.com/florida/southtampa/calendar** — different audience radius; only sweep if user specifically asks
- **r/ClearwaterFlorida** — too small to yield reliable signal
- **setlist.fm** — requires API key; Bandsintown covers same data better
- **tampa.dev** — tech meetups rarely fit KCC's venue play

## Known gaps (always include in output)

- **IG/TikTok geo-trending:** no clean source without paid social APIs. Reddit is the proxy.
- **Private/invite-only events:** invisible to web scraping
- **Last-minute pop-ups:** events booked <14 days out often don't hit aggregators
- **Filming/celebrity-in-town:** no public permit feed
- **Corporate retreats / large group bookings:** no public signal; this is inbound only
- **Author tour signal:** Tombolo/Haslam's/Inkwood aren't directly fetched — relies on ilovetheburg aggregation. Worth a dedicated probe if author signal seems sparse.
