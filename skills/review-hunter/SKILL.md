---
name: review-hunter
description: Dynamically pull, aggregate, and analyze customer reviews for any restaurant chain across Google, Yelp, TripAdvisor, and other sources. Trigger on "pull reviews", "review analysis", "review hunter", "what are people saying about [restaurant]", "sentiment analysis for [chain]", "customer feedback for [brand]", "reputation check", "review audit", "reputation dashboard", "review dashboard", "how are our reviews", "how's [chain] doing on Google reviews", "check Yelp for [brand]", "are people happy with [chain]", "what's our rating", "build me a review report". Also trigger when the user names a restaurant and asks about complaints, praise, competitive positioning, response rates, or review trends. Single-location and multi-location both. Do NOT trigger for product reviews, app store reviews, or non-food/beverage businesses.
---

# Review Hunter

Pull and analyze customer reviews for any restaurant chain across Google, Yelp, TripAdvisor, and the wider web. Deliver results as an **interactive glassmorphism React artifact** with sentiment analysis, drift detection, competitive positioning, reputation anchors, and response gap analysis — a reputation intelligence dashboard, not a static report.

## How It Works

Review Hunter operates as a **sequential agent team** — six focused passes executed in order: Location Discovery → Google → Yelp → TripAdvisor → Wild Card Sources → Analyst Synthesis. Each pass feeds the next, culminating in an interactive React artifact.

### Step-by-Step Execution

#### Step 1: Intake

Ask the user (if not already clear from context):
- **Chain name** — the restaurant/bar/café brand to investigate
- **Scope** — all locations, a specific region, or specific addresses
- **Focus areas** — any particular aspects to pay attention to (food quality, service, ambiance, value, cleanliness, wait times, etc.), or "general sweep"

If the user already provided the chain name in their message, skip straight to execution. Don't over-interview — default to "all findable locations" and "general sweep" unless they narrowed it.

#### Step 2: Location Discovery (Scout 1)

**Preferred method — use `places_search` tool if available:**
```
places_search: { queries: [{ query: "[chain name] [region]", max_results: 10 }] }
```
This returns exact addresses, coordinates, ratings, and place_ids directly — far more reliable than scraping web results. If `places_search` is available, use it as the primary location discovery method and skip the web search fallback below.

**Fallback — web search:**
```
Search: "[chain name] locations"
Search: "[chain name] all locations [region if specified]"
Search: "[chain name] store locator"
```

Build a location manifest:
```
LOCATION MANIFEST
=================
Chain: [name]
Locations found: [count]

1. [Address] — [City, State]
2. [Address] — [City, State]
...
```

If the chain has more than 10 locations and no region filter was given, tell the user how many you found and ask if they want all of them or a subset. For chains with 5 or fewer locations, just do them all.

#### Step 3: Source Sweeps (Scouts 2–5)

For each location in the manifest, run sequential source-specific searches. Capture everything into a structured internal format before moving to analysis.

**Flow control:**
- **Search budget:** 2 `web_search` calls per source per location. If the first search returns a direct listing URL, use `web_fetch` on it — that's worth more than a second search.
- **web_fetch decision:** Only fetch if the URL is a direct business listing page (Yelp biz page, Google Maps listing, TripAdvisor page). Don't fetch generic search result pages, listicles, or aggregator sites — snippets are enough for those.
- **"Done" per source:** A source pass is complete when you have: (a) a rating, (b) a review count, (c) at least 2 representative snippets with dates, and (d) any enhancement data visible (response rates, named anchors). If you can't get (a) after both searches, mark the source as "No data" and move on.
- **Total search ceiling:** For a typical 3-location chain, expect ~30 total web_search + web_fetch calls. For 10+ locations, stay under 80. If you're approaching the ceiling, prioritize depth on outlier locations over completeness on average ones.

**Google Reviews (Scout 2):**
```
Search: "[chain name] [city] reviews"
Search: "[chain name] [address] rating"
```
Use `web_fetch` on any Google Maps business listing URLs that surface to capture detailed review data. If a direct listing URL appears, always fetch it — snippets alone miss rating counts and response data.

Capture per location:
- Overall star rating
- Number of reviews
- 3–5 representative review snippets (mix of positive, negative, recent) — **note approximate dates when visible**
- Common praise keywords
- Common complaint keywords
- **Named staff, menu items, or experiences** mentioned in reviews (reputation anchors)
- **Owner response presence** — are reviews being replied to? Estimate percentage, especially on negatives

**Yelp Reviews (Scout 3):**
```
Search: "[chain name] [city] Yelp reviews"
Search: "Yelp [chain name] [state]"
```
Use `web_fetch` on any Yelp listing URLs to capture full review pages. Yelp pages contain rich data: star distribution, price tier, response activity, and "not recommended" review counts.

Capture per location:
- Star rating
- Review count
- Price tier
- 3–5 representative snippets — **note dates when visible**
- Any "not recommended" review themes if visible
- **Owner response presence** on negative reviews
- **Named staff or menu items** mentioned

**TripAdvisor Reviews (Scout 4):**
```
Search: "[chain name] [city] TripAdvisor"
Search: "TripAdvisor [chain name] reviews [state]"
```
Use `web_fetch` on TripAdvisor listing URLs — they contain ranking in city, traveler type breakdown, and date-stamped reviews useful for drift detection.

Capture per location:
- Rating (out of 5)
- Ranking in city
- Traveler type breakdown if available
- 3–5 representative snippets — **note dates and any recent-vs-historical rating shifts**

**Wild Card Sources (Scout 5):**
```
Search: "[chain name] Reddit review"
Search: "[chain name] [city] blog review"
Search: "[chain name] customer experience 2025 OR 2026"
```
For niche verticals, add domain-specific searches:
- Bars/breweries: `"[chain name] Untappd"` or `"[chain name] BeerAdvocate"`
- Botanical/kava bars: `"[chain name] kava review"` or `"[chain name] kratom review"`
- Coffee shops: `"[chain name] specialty coffee review"`

Use `web_fetch` on any Reddit threads, blog posts, or niche platform pages that surface.

Capture any additional reviews from:
- Reddit threads
- Facebook page reviews
- Local food blogs
- News articles / features
- Niche platforms (e.g., Untappd for bars, Leafedout for botanical bars)

For each source discovered, note the platform and capture 2–3 relevant snippets.

#### Step 4: Sentiment Analysis (Analyst Pass)

Once all scout data is collected, perform the analysis pass. **Enhancement features are best-effort** — execute each one when data supports it, skip gracefully when it doesn't. A missing enhancement is fine; fabricated data is not.

**Per-Location Analysis:**
- Overall sentiment score: Positive / Mixed / Negative
- Weighted average rating across sources (weight by review count)
- Top 3 praise themes (with example quotes, paraphrased)
- Top 3 complaint themes (with example quotes, paraphrased)
- Trend signal: Improving / Stable / Declining (based on recency of reviews)
- **Sentiment drift detection**: Compare last-3-month reviews to historical average. Flag any location where recent sentiment diverges significantly (e.g., ratings dropped 0.5+ in recent reviews). This catches operational problems and wins early.
- **Review velocity**: Estimate reviews-per-month from available date data. Flag anomalies — sudden drops (losing mindshare) or spikes (viral moment, good or bad).
- **Reputation anchors**: Extract specific staff names, menu items, or experiences reviewers mention by name ("Ask for Mike", "the kava flight is incredible", "parking is terrible"). These are operational gold.
- **Owner response rate**: On Google and Yelp, check if the business responds to reviews. Estimate reply percentage, especially on negative reviews. Low response rates → recommendation.
- Standout observations (anything unusual or noteworthy)

**Chain-Wide Analysis:**
- Overall chain sentiment: Positive / Mixed / Negative
- Chain average rating (weighted by location review volume)
- Consistent strengths across locations
- Consistent weaknesses across locations
- Location outliers (any location significantly better or worse)
- **Competitive positioning matrix**: When competitor names surface in reviews ("better than X", "used to go to Y"), build a positioning comparison on the dimensions reviewers actually mention (price, quality, atmosphere, service). Render as a comparison table in the artifact.
- Actionable recommendations (3–5 concrete suggestions based on patterns, including response strategy if response gaps detected)

#### Step 5: Generate the Interactive Report Artifact

Deliver the report as a **React (.jsx) artifact** with a polished, dark-themed glassmorphism aesthetic. Before writing the artifact, read `/mnt/skills/public/frontend-design/SKILL.md` for design tokens and styling guidance.

**Design Direction:**
- Dark background (`bg-gray-950` or `bg-slate-950`) with glassmorphic card panels (`bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl`)
- Accent color derived from the chain's brand if known, otherwise electric teal (`text-teal-400`, `bg-teal-500/20`)
- Sentiment colors: positive = `text-emerald-400`, mixed = `text-amber-400`, negative = `text-rose-400`
- Smooth transitions (`transition-all duration-300`), subtle hover states (`hover:bg-white/10`), clean type hierarchy
- Responsive: stack cards vertically on mobile (`flex flex-col md:flex-row`), comparison grid collapses to single-column
- Animated score ring: use SVG `<circle>` with `stroke-dasharray`/`stroke-dashoffset` for the sentiment gauge
- The vibe: "reputation mission control"

**Required Sections & Interactions:**

1. **Hero Header** — Chain name, generation date, animated sentiment score ring (overall rating), stats bar (locations analyzed, reviews sampled, sentiment badge)

2. **Executive Summary Card** — 2–3 sentence AI narrative, trend indicator (↑/→/↓) with color treatment

3. **Location Selector & Comparison** — Tabbed/dropdown location picker to view detail cards. "Compare All" toggle for side-by-side grid. Each card: source ratings, review volume, sentiment, **response rate badge**, **velocity indicator**, **drift alert** (if detected). Click to expand.

4. **Source Breakdown** — Interactive tabs: Google | Yelp | TripAdvisor | Other. Selecting a source filters data chain-wide. Rating distribution visualization.

5. **Sentiment Dashboard** — Top praise vs. complaint themes as ranked lists or visual cloud. Per-location sentiment heatmap or comparison bars. "Love vs. Hate" toggle with paraphrased examples. **Sentiment drift alerts** highlighted with colored badges for locations diverging from historical norms.

6. **Reputation Anchors** — Staff names, menu items, and experiences customers mention by name. Show with frequency counts and positive/negative classification. This is operational gold for the owner.

7. **Competitive Matrix** — If competitor mentions were found, render a comparison table or positioning visual showing how the chain stacks up on dimensions reviewers mention (price, quality, atmosphere, service).

8. **Pattern & Outlier Detection** — Chain strengths/weaknesses cards. Outlier callouts with visual highlighting. **Review velocity anomalies** flagged.

9. **Recommendations Panel** — 3–5 prioritized action cards, each with title, data-backed rationale, and impact tag (High/Medium/Low). **Include response strategy recommendation** if response gaps detected.

10. **Sources Drawer** — Collapsible footer listing all URLs by source type.

**Technical Notes:**
- Use `useState` for all state (active tab, selected location, expanded cards, comparison toggle). No localStorage.
- Build a single `reportData` object at component top with all collected data, render reactively.
- Use Tailwind core utilities only. Use recharts for any charts. Use lucide-react for icons.
- Single-file .jsx artifact — everything in one component with default export.

**Data Structure for reportData:**
```javascript
const reportData = {
  chain: "Chain Name",
  generatedDate: "YYYY-MM-DD",
  overallRating: 4.2,
  overallSentiment: "Positive",
  trend: "Improving",
  totalReviews: 847,
  locations: [
    {
      name: "City, State",
      address: "Full address",
      sources: {
        google: { rating: 4.3, count: 234, sentiment: "Positive" },
        yelp: { rating: 4.0, count: 156, sentiment: "Mixed" },
        tripadvisor: { rating: 4.5, count: 89, sentiment: "Positive" },
        other: { platforms: ["Reddit"], count: 45, sentiment: "Mixed" }
      },
      praiseThemes: ["theme1", "theme2", "theme3"],
      complaintThemes: ["theme1", "theme2"],
      snippets: { positive: ["paraphrased..."], negative: ["paraphrased..."] },
      notable: "Standout observation",
      trend: "Stable",
      sentimentDrift: { detected: true, direction: "declining", detail: "Recent 3-month avg 3.8 vs historical 4.3" },
      reviewVelocity: { perMonth: 12, trend: "declining", anomaly: false },
      responseRate: { google: 0.15, yelp: 0.0, note: "Only 15% of Google reviews answered, zero on Yelp" },
      reputationAnchors: [
        { text: "the kava flight", type: "positive", mentions: 8 },
        { text: "parking lot", type: "negative", mentions: 5 }
      ]
    }
  ],
  chainStrengths: ["strength1", "strength2"],
  chainWeaknesses: ["weakness1", "weakness2"],
  outliers: [{ location: "City", direction: "above", detail: "why" }],
  competitorMentions: [{ name: "Competitor", context: "paraphrased" }],
  competitiveMatrix: {
    dimensions: ["price", "quality", "atmosphere", "service"],
    competitors: [
      { name: "Competitor A", positioning: { price: "cheaper", quality: "lower", atmosphere: "similar", service: "worse" } }
    ]
  },
  recommendations: [
    { title: "Action", rationale: "Data-backed why", impact: "High" }
  ],
  sources: ["url1", "url2"]
};
```

### Important Behaviors

- **Paraphrase, never quote verbatim.** When citing review content, always restate in your own words. Copyright rules apply to review content too.
- **Be honest about coverage gaps.** If a source has no results for a location, say so. Don't invent data.
- **Prioritize recency.** Recent reviews (last 6 months) matter more than old ones. Flag if most reviews are stale.
- **Note review volume.** A 4.8 rating from 12 reviews means something very different than a 4.8 from 1,200. Always contextualize.
- **Watch for fake review signals.** If you notice patterns suggesting fake reviews (all 5-star, generic language, posted in clusters), flag it.
- **Respect rate limits.** Space out web_fetch calls. If a site blocks or returns errors, note it and move on.
- **Scale effort to chain size.** A 2-location chain gets deep dives. A 50-location chain gets representative sampling with outlier spotting.

### Edge Cases & Fallback Behaviors

**Chain name ambiguity:** If the chain name is common or shared by multiple brands (e.g., "The Coffee House"), confirm with the user which one before proceeding. Include city/state or website in search queries to disambiguate.

**No results from a source:** If a source returns zero results for a location, record it as `{ rating: null, count: 0, sentiment: "No data" }` in the data. Don't skip the location — partial data is still valuable. Note the gap in the report.

**Web fetch failures:** If `web_fetch` fails (403, timeout, bot detection), log the failure and move on. Never retry more than once. Note in the Sources Drawer which URLs were unreachable. Fall back to search snippet data only.

**Very large chains (50+ locations):** Don't attempt all locations. Ask the user to narrow by region, or auto-select a representative sample: top 5 by review volume, bottom 3 by rating, plus any the user specifically names. State the sampling strategy in the report header.

**New or obscure chains:** If the chain has very few reviews across all sources (< 20 total), note this prominently. Shift focus from statistical analysis to qualitative deep-read of every available review. A thin data set makes patterns unreliable — say so.

**International chains:** If the chain operates internationally, default to the user's region unless told otherwise. Note that review platforms vary by country (e.g., TripAdvisor strong in Europe, Google dominant in US, Tabelog in Japan). Adjust scout strategy accordingly.

**Single-location businesses:** If the "chain" turns out to be a single location, skip the chain-wide analysis sections and competitive matrix. Deliver a deep-dive single-location report with all enhancement features.

**Rebranded or acquired chains:** If reviews mention a previous name or ownership ("this used to be X", "ever since new management"), capture both the old and new brand sentiment separately. This is critical for drift detection — a rebrand can create a false "decline" signal when the old reviews drag down the new brand's trajectory. Note the transition in the executive summary.

### Adapting to User Context

Detect the user's relationship to the chain from context clues and adjust tone, depth, and emphasis:

**Owner/Operator** (e.g., "pull reviews for my bar", mentions of their own locations): Shift from "external audit" to "operations intelligence." Emphasize actionable insights, reputation anchors (staff and menu items to protect/promote), response gap urgency, and competitive positioning. Recommendations should be concrete operational changes, not abstract strategy.

**Competitor Research** (e.g., "how's [competitor] doing", "compare us to them"): Lean into weaknesses, vulnerability signals, and gaps the user could exploit. Highlight what customers wish the competitor would fix — those are the user's opportunities.

**Franchise/Investment Evaluation** (e.g., "thinking about opening a [chain]", "evaluating this franchise"): Focus on consistency across locations (high variance = risky franchise system), velocity trends (growing or shrinking mindshare), and whether complaints are systemic (brand-level) or local (operator-level). Frame recommendations as risk factors.

**Marketing/Agency** (e.g., "client needs a reputation audit", professional framing): Deliver a polished, presentation-ready artifact. Emphasize data visualization, clean metrics, and quotable executive summary. Recommendations should be strategically framed with estimated impact levels.

**General Curiosity** (e.g., "what do people think of [chain]", casual phrasing): Keep it concise and engaging. Lead with the most interesting findings. Skip operational depth. Make it fun to explore.

