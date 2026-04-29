---
name: everything-data
description: >
  Run a complete data + financial analysis pass on any business or dataset.
  Source-agnostic — SQL warehouse, CSV, XLSX, JSON, or pasted tables. Discovers
  schema, profiles quality, builds P&L with variance, applies the appropriate
  unit-economics lens (retail / SaaS / transaction / PE), runs Bull/Base/Bear
  sensitivity, scans statistical pitfalls and QA defects, cites every claim,
  and optionally renders a self-contained Chart.js dashboard. Designed for
  the user's kava bar (KC) and its BBCO retail product line as canonical
  case; equally usable on any other dataset. Replaces 11 chained skills with
  one ordered pass under a single master-check. Trigger on "/everything-data",
  "everything data on [X]", "KC P&L", "KC variance report", "BBCO mix",
  "scorecard deep dive", "full data audit", "unit economics for [X]",
  "data report on [X]", "BBCO product line review".
origin: gvo-skills (merge of 3-statements, earnings-analysis, returns-analysis, unit-economics, data-exploration, data-validation, interactive-dashboard-builder, statistical-analysis, data-visualization, sql-queries, csv-data-summarizer)
---

# Everything Data — Source-Agnostic Financial + Data Analysis

One ordered pass that profiles data, builds a P&L with variance, applies the right unit-economics lens for the business, runs sensitivity, scans for statistical and QA pitfalls, and ships a sourced markdown report (and optionally a self-contained Chart.js dashboard). Built for KC + BBCO as the canonical case; works on any business or dataset.

## When to use this skill

Use when:
- The user asks for a "full" / "everything" / "complete" / "deep dive" analysis of a business or dataset.
- The user names a period and a target ("April KC P&L", "BBCO mix last quarter", "this customer.csv").
- The question would otherwise require chaining 4+ analysis skills (profile → variance → cohorts → sensitivity → report → dashboard).
- The user wants a dashboard rendered alongside the numerical analysis.

Don't use when:
- The user wants a single narrow metric ("just give me April revenue") — answer directly.
- The user wants pure ETL ("load the new Toast CSV") — defer to `/from-kc-records` or equivalent.
- The user wants only a dashboard and the numbers are already trusted — call the existing dashboard pipeline directly.

## Deliverables (always)

1. **Markdown analysis report** with: question, executive summary, KPI scorecard, variance commentary, business-model-specific deep-dive, cohort/repeat patterns, sensitivity, action items, statistical caveats, QA pitfalls scanned, data sources, definitions, methodology, full citations.
2. **Optional self-contained Chart.js HTML dashboard** when scope justifies — a single `.html` file with embedded JSON, KPI cards, line/bar/doughnut/heatmap, dropdown + date filters, sortable table.

## Phase 1 — Intake & Scope

Before running any query or computation, lock these:

- **The question**: what is the user actually trying to decide or learn? Period, scope, decision support, or general audit?
- **The target**: which business / entity / dataset? (KC overall? BBCO product line? a customer.csv?)
- **The data sources**: every input that's been provided or should be queried. SQL connection details, file paths, pasted tables, prior analyses. **Do not assume any specific schema or table** — discover at runtime.
- **Output format**: markdown report (default), HTML dashboard (when requested), both.

### Entity disambiguation (critical)

Ambiguous nouns silently break cohort math. Confirm exactly which entity the user means:

- "Customer" — is that an individual buyer? A loyalty member? An account? A household?
- "User" vs "account" vs "organization" — which one is the unit of analysis?
- "Order" vs "transaction" vs "ticket" vs "check" — same thing? Different?
- "Active" — purchased in last N days? Logged in? Paid the bill?

When the data has multiple entity types, surface the choice and pick one explicitly.

### Terminology + acronyms

Capture company-specific terms upfront and put them in the report's Definitions section:

- BBCO at KC = bottled beverage SKU class (cans, 4-packs).
- "Shift" vs "daypart" — different in some POS systems.
- "Substance" at KC = kava / kratom / mixed / delta9 / none.
- Any other proprietary metric names.

### Metric definitions

Every contested metric gets an exact definition pinned in the report:

- "Revenue" — gross / net / recognized / cash-collected?
- "Tickets" — voids included? Open tickets? Comp'd?
- "Active customer" — any purchase in last 30 / 60 / 90 days?
- "Cost" — landed / FOB / fully-loaded with labor + overhead?

If the user shrugs, propose a default and state it as an assumption.

### Business-model classification (drives Phase 4)

The skill picks one lens (or asks). Each lens has a canonical metrics set:

| Lens | Trigger signals | Metrics |
|---|---|---|
| **Retail / hospitality** | POS data, tickets, dayparts, products, labor by shift | AUR, prime cost %, attach rate, daypart cohorts, product-line velocity |
| **SaaS / subscription** | MRR/ARR, customer-IDs with start/cancel dates, recurring | ARR bridge, NDR/GRR, vintage cohorts, LTV/CAC, CAC payback |
| **Transactional / marketplace** | GMV, take rate, buyer/seller IDs, order tables | GMV trend, buyer cohort retention, frequency × order-size, take rate |
| **PE deal review** | Entry EBITDA, leverage, exit assumptions, hold period | IRR, MOIC, returns waterfall, sensitivity by entry/exit/growth/leverage |

If signals are mixed (e.g., a kava bar with a subscription tier), apply two lenses side by side.

### Posture: just analyze, don't stall

If the user has provided data and a question, **start working**. Do not list options ("would you like X, Y, or Z?"). Reserve clarifying questions for genuine ambiguity that materially changes the answer (e.g., "two CSVs were attached — which is the source of truth?", "is 'voided' included in the ticket count?"). Never offer analysis flavors as a multiple choice.

## Phase 2 — Data Foundation

Profile every input before analyzing.

### Profiling protocol

**Structural pass:**
- Row count, column count.
- Grain (one row per what?).
- Primary key — present and unique?
- Date range covered — earliest to latest.
- Update cadence — when was this last refreshed?

**Column-level pass.** Classify each column as one of:
- Identifier (unique keys, foreign keys)
- Dimension (categorical for grouping/filtering)
- Metric (quantitative)
- Temporal (dates, timestamps)
- Text (free-form)
- Boolean (true/false)
- Structural (JSON, arrays)

For each column compute: null rate, distinct count + cardinality ratio, top-5 values, bottom-5 values. Then per type:
- Numeric → min/max/mean/median, p1/p5/p25/p75/p95/p99, stdev, zero count, negative count.
- String → min/max/avg length, empty count, pattern check, case consistency, leading/trailing whitespace.
- Date → min/max, future-dated count (if unexpected), distribution by month/week, gaps in series.
- Boolean → true/false/null counts, true rate.

**Relationship pass:**
- Foreign-key candidates (ID columns that match other tables).
- Hierarchies (country > state > city; category > subgroup > item).
- Correlations (numeric pairs that move together — flag |r| > 0.7 for investigation, not causation).
- Derived columns (computed from others — e.g., `net_price = gross_price - discount`).
- Redundant columns (identical or near-identical info).

### Quality assessment rubric

| Dimension | Green | Yellow | Orange | Red |
|---|---|---|---|---|
| Completeness | >99% non-null | 95-99% | 80-95% | <80% |
| Consistency | Format / type / referential / business rules / cross-column all clean | One small issue | Multiple issues | Systematic |
| Accuracy | No placeholders, no impossible values, no round-number bias | Rare | Some | Pervasive |
| Timeliness | Within expected cadence | One cycle late | Multiple cycles late | Stale, unclear |

Any column scoring Yellow or worse becomes a caveat in the report. Red columns block the analysis until addressed.

### Multi-dialect SQL reference

Pick the dialect from the connection. Universal patterns:

```sql
-- CTE chain for readability
WITH base AS (
  SELECT user_id, created_at, plan_type FROM users WHERE status = 'active'
),
metrics AS (
  SELECT b.user_id, b.plan_type, COUNT(DISTINCT e.session_id) AS sessions
  FROM base b LEFT JOIN events e ON b.user_id = e.user_id
  GROUP BY b.user_id, b.plan_type
)
SELECT plan_type, AVG(sessions) AS avg_sessions FROM metrics GROUP BY plan_type;

-- Window functions: running total, lag, percent of total
SELECT date, revenue,
  SUM(revenue) OVER (ORDER BY date ROWS UNBOUNDED PRECEDING) AS running_total,
  LAG(revenue, 1) OVER (ORDER BY date) AS prev_day,
  revenue / SUM(revenue) OVER () AS pct_of_total
FROM daily_sales;

-- Cohort retention skeleton
WITH cohorts AS (
  SELECT user_id, DATE_TRUNC('month', first_activity) AS cohort
  FROM users
)
SELECT c.cohort,
  COUNT(DISTINCT c.user_id) AS size,
  COUNT(DISTINCT CASE WHEN a.month = c.cohort + INTERVAL '1 month' THEN a.user_id END) AS m1
FROM cohorts c LEFT JOIN activity a ON c.user_id = a.user_id
GROUP BY c.cohort;

-- Dedupe: keep latest per key
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY entity_id ORDER BY updated_at DESC) AS rn
  FROM source
) WHERE rn = 1;
```

Dialect notes (when relevant): PostgreSQL uses `||`/`ILIKE`/`DATE_TRUNC`. Snowflake uses `DATEADD`/`DATEDIFF`/`VARIANT` paths (`col:key::TYPE`). BigQuery uses `DATE_ADD(d, INTERVAL n DAY)`/`REGEXP_CONTAINS`/`UNNEST`. Redshift uses `LISTAGG`/`SPLIT_PART`. Databricks uses Delta Lake time travel (`TIMESTAMP AS OF`).

### CSV / XLSX intake

Detect column types automatically. Handle missing data gracefully. Infer business domain from columns (a column named `cohort_month` + `arr` signals SaaS; `daypart` + `prime_cost` signals retail). Adapt analyses to what's actually present.

### Multi-source synthesis *(from `knowledge-synthesis`)*

When inputs span multiple data sources — D1 + CSV + prior analysis + manual entry — combine them deliberately:

- **Cross-source deduplication.** The same fact often appears in multiple inputs. Merge when text matches, authors/timestamps cluster, the same entity is referenced, or one source cites another. Keep the most complete version; cite all sources.
- **Authority ranking** (when sources conflict on the same fact, prefer in this order): production database → finalized report → shared spreadsheet → email → meeting notes → chat thread conclusion → chat mid-thread → draft document.
- **Freshness scoring.** Today/this week → high confidence for current state. This month → moderate; things may have changed. Older than a month → flag as potentially outdated. Status queries weight freshness heavily; policy/factual queries weight it less.
- **Conflict surfacing.** When sources disagree on the same fact, **surface all viewpoints with dates** — do not silently pick one. Format: "Source A (date): X. Source B (date): Y. Latest source indicates Y; A may be stale."
- **Summarization by result-set size.** Small (1-5 sources): present each with context. Medium (5-15): group by theme, summarize each. Large (15+): high-level synthesis with drill-down option.
- **Anti-pattern.** Never list source-by-source ("From D1: … From CSV: …"). Lead with the answer; group by topic; attribute inline.

## Phase 3 — Financial Statement Pass

Build the income statement in whatever revenue categorization the data supports. **Do not preprogram categories.** If categories aren't obvious, profile and ask.

### Standard P&L structure

```
Revenue (by segment / category / SKU as data allows)
  - COGS (by category if available, else aggregate)
= Gross Profit
  Gross margin %
  - Operating Expenses (by line as available)
= Operating Profit / Contribution Margin
  + non-operating items
= EBITDA
  - D&A
  - Interest
  - Tax
= Net Income

(Retail/hospitality only:)
  Prime cost % = (COGS + labor) / revenue
```

### Variance pass — 4-column shape

| Line | Actual | Prior | Budget | Forecast | Var $ | Var % |
|---|---|---|---|---|---|---|

Skip columns absent from data; note their absence in the report.

### Materiality thresholds (auto-scaled)

- Revenue line: variance >5% OR >0.5% of total revenue → material.
- Margin line: variance >2% absolute OR >scale-appropriate dollar floor → material.
- Any single line that changes the bottom-line conclusion → material regardless of size.
- COGS line: >3% OR >$X scale-appropriate → material.
- Labor line: >2% OR >$X scale-appropriate → material.

Only material variances enter the report's Variance Commentary. Noise variances are filtered out.

### Variance decomposition

Decompose every material variance into its drivers:

- **Volume** — units / tickets / transactions changed.
- **Price** — average revenue per unit changed.
- **Mix** — composition of the basket shifted between high/low margin.
- **Timing** — period boundary effects, accruals, deferrals.
- **FX** — only if multi-currency data detected.

State the decomposition explicitly: "Revenue down $X = Volume −$A + Price +$B + Mix −$C + Timing +$D".

### Cross-statement integrity checks

When the data supports them:

- Subtotals add to totals (margin lines, OpEx, EBITDA roll-up).
- Period-over-period roll-forward of locked balances.
- Cash tie-out: CF ending cash = BS cash (full statements).
- NI link: CF top-of-CFO = IS NI (full statements).
- RE roll-forward: Prior RE + NI − Dividends = Ending RE.
- Whatever cross-references the partial data supports.

### Master check formula

At the end of the analysis, aggregate every integrity check:

```
✓ ALL CHECKS PASS    → report is ready to ship
✗ ERRORS DETECTED    → list the failing items with location
```

Always render this. The user reads it first.

### Scenario hierarchy validation

When Bull/Base/Bear scenarios are presented, verify:
- Absolute metrics: Bull > Base > Bear (revenue, GP, EBITDA).
- Cost-as-% metrics: Bull < Base < Bear (prime cost %, OpEx %).
- Credit metrics: Bull < Base < Bear for leverage; Bull > Base > Bear for coverage.

A scenario set that violates this hierarchy is a modeling error.

GAAP/ASC framing kept light — surfaced when the user asks for audit-grade output; skipped otherwise.

## Phase 4 — Unit Economics (Multi-Framing)

Pick the lens from Phase 1 classification. Apply the right metrics; **do not bleed framings across lenses** (no IRR in a retail run, no NDR in a PE run).

### Translation table

| Concept | SaaS | Retail / hospitality | Marketplace | PE |
|---|---|---|---|---|
| Recurring revenue | ARR / MRR | Run-rate revenue (rolling 30/90d) | GMV × take rate | Recurring EBITDA |
| Cohorts | ARR by signup vintage | Daypart × DOW; first-visit by month | Buyer cohort by acquisition | Hold-period vintages |
| Retention | NDR | Repeat-visit rate; same-store YoY | Buyer repeat rate | Customer churn |
| Acquisition cost | CAC | Marketing $ / new customers | CAC per buyer | N/A |
| Lifetime value | LTV = ARPU × GM / churn | Avg ticket × revisit × tenure | Avg order × frequency × tenure | Exit-equity attribution |
| Payback | CAC payback (months) | Marketing-to-revisit (months) | CAC / order contribution | N/A |
| Quality ratio | LTV : CAC ≥ 3 | LTV : CAC ≥ 3 | LTV : CAC ≥ 3 | N/A |
| Don't apply | — | Magic Number, Rule of 40, ARR cohort | NDR (strict) | NDR / ARR |

### Per-lens deliverables

**SaaS:**
- ARR bridge: Beg → New → Expansion → Contraction → Churn → End.
- Cohort vintage matrix (absolute $ and indexed to Year 0 = 100).
- GRR + NDR + logo churn + dollar churn.
- LTV / CAC blended and segmented (enterprise vs SMB vs mid-market).
- Margin waterfall by stream (subscription vs services vs other).
- Benchmarks: Rule of 40 (>40), Magic Number (>0.75), NDR (>120 best / >110 good / <100 concerning), LTV:CAC (>5/3/<2), GRR (>95/90/<85), CAC payback (<12/18/>24).

**Retail / hospitality:**
- AUR (avg revenue per ticket), tickets/day, units/ticket.
- Prime cost % = (COGS + labor) / revenue.
- Beverage cost %, food cost %, labor as % revenue.
- Modifier attach rate, void rate.
- Daypart × day-of-week heatmap.
- Repeat-visit rate (loyalty join when available; else cohort proxy).
- **Product-line lens** (BBCO-style — generalizable): for the named product line, compute SKU velocity (units/day, trailing 7d/28d), substance/category mix, attach rate (% of tickets including the line), contribution to category GP $ and GP %, trailing slope vs other lines.
- Reference ranges (industry-typical, not hardcoded targets): gross margin 60-75%, prime cost ≤60% good / 65% caution / >70% red, labor 25-32%, beverage cost 20-25%. State these are reference ranges, not the user's targets.

**Transaction / marketplace:**
- GMV trend; take rate trend.
- Buyer cohort retention.
- Frequency × order-size grid.
- Contribution per transaction.
- Reference ranges: take rate 5-30% (varies by category), repeat-buyer rate target ≥40%.

**PE:**
- Returns waterfall: EBITDA growth contribution, multiple expansion/contraction, debt paydown, fee/expense drag.
- IRR + MOIC (gross + net of fees if relevant).
- Sensitivity (Phase 5 detail).

### Revenue quality scoring (6-dim, 1-5 scale)

Universal across lenses; retranslated:

| Factor | SaaS | Retail / hospitality |
|---|---|---|
| Recurring share | Recurring % of revenue | Repeat customer % |
| Retention | NDR | Repeat-visit rate |
| Concentration | Top 10% customers % of ARR | Top 10% SKUs/customers % of revenue |
| Cohort stability | Cohort retention slope | Daypart stability across weeks |
| Growth durability | YoY growth multi-period | Same-store growth |
| Margin profile | GM by stream | GM by category |

Score each 1-5; sum for an overall quality grade.

## Phase 5 — Sensitivity & Scenarios

### 2-way sensitivity (5×5 universal structure)

Pick drivers per lens. Show both metrics in each cell when relevant (e.g., IRR / MOIC for PE).

**Retail examples:**
- Traffic % × ticket-size % → revenue impact.
- Labor rate × shift coverage → labor cost impact.
- Price × volume → GP impact (for a product line decision).
- Cost % × menu mix → COGS impact.

**SaaS examples:**
- NDR × new-logo growth → ARR end-of-year.
- Gross-margin × CAC payback → cash burn.

**PE examples:**
- Entry-multiple × exit-multiple → IRR / MOIC.
- EBITDA growth × exit-multiple → IRR.
- Leverage × exit-multiple → IRR.
- Hold-period × exit-multiple → IRR.

**Marketplace examples:**
- Take-rate × volume → revenue.
- CAC × LTV → unit profitability.

### Scenarios — Bull / Base / Bear

Always state assumptions explicitly. **Never present scenarios as forecasts.**

| Driver | Bull | Base | Bear |
|---|---|---|---|
| (named drivers per lens) | | | |

Verify hierarchy (Phase 3) before reporting.

### Decision-support template

```
"If {variable} changes by {amount}, at {assumption-set-1, set-2, set-3},
how does {outcome metric} move?"
```

Apply to the actual decision the user is staring at. Skip generic sensitivities.

### Returns attribution

For deal/outcome lenses (PE + select SaaS): decompose into Growth × Multiple × Leverage × Fees.

For operating businesses: decompose Performance into Volume × Price × Mix × Margin × One-Offs.

### Sensitivity table mechanics *(from `dcf-model`)*

A sensitivity table is a **simple grid with formulas in every cell** — *not* Excel's "Data Table" feature (which can't be automated programmatically and requires manual user steps). For an Excel deliverable, write each cell explicitly via openpyxl loops; a 5×5 grid = 25 formulas. Three tables = 75 formulas. This is required, not optional. For a markdown / HTML deliverable, pre-compute the grid in code and embed the result.

### INDEX consolidation pattern *(from `dcf-model`, replaces nested-IF anti-pattern)*

When scenarios drive multiple downstream calculations, use a **consolidation column** with INDEX/OFFSET, not nested IFs scattered through projections:

```
✓ =INDEX(B10:D10, 1, $B$6)            (case selector at $B$6: 1=Bear, 2=Base, 3=Bull)
✗ =IF($B$6=1, B10, IF($B$6=2, C10, D10))  (scattered IFs — fragile, hard to audit)
```

Centralizes scenario logic; makes audits clean.

### Terminal value sanity check *(from `dcf-model`)*

When a DCF or valuation result is presented, terminal value (PV of perpetuity) should be **50-70% of enterprise value**. Outside this band:
- **>75%**: model is over-reliant on terminal assumptions; tighten near-term projections or shorten the explicit period.
- **<40%**: terminal assumptions may be too conservative; cross-check against industry comparables.

### Mid-year convention *(from `dcf-model`)*

For DCF or any periodic-cash-flow discounting, assume cash flows occur mid-period: discount periods are 0.5, 1.5, 2.5, … instead of 1, 2, 3. Discount factor = 1 / (1+r)^period. Mirrors when revenue actually arrives during a year. Required terminal-growth constraint: **terminal growth < WACC** (otherwise infinite value).

## Phase 6 — Statistical Caveats

Apply during analysis and verification. Universal, source-agnostic. State at least one applicable caveat per report.

- **Correlation ≠ causation.** When correlation grounds a recommendation, name the alternatives: reverse causation, confounders, coincidence.
- **Multiple comparisons.** Twenty hypotheses at p=0.05 produce ~1 false positive. Note the count; apply Bonferroni when stakes warrant.
- **Simpson's Paradox.** Aggregate trend can reverse at segment level. Always verify trends across key segments (daypart, weekday, location, segment).
- **Survivorship bias.** Analyzing surviving entities ignores churned/failed ones. Ask "who is missing from this dataset?"
- **Anchoring / false precision.** "4-6%" beats "4.73%". Report ranges when warranted.
- **Practical vs statistical significance.** State dollar/operational impact alongside any percent change.
- **Round-number bias.** Distributions concentrated on values ending in 0 or 5 suggest estimation, not measurement.
- **Ecological fallacy.** Group-level findings may not apply to individuals.
- **Selection bias.** Defining segments by the outcome being measured is circular ("power users have higher revenue" — they became power users by generating revenue).

## Phase 7 — QA Pitfalls Catalogue

Scan every analysis before declaring it done. State which were checked and the result.

- **Join explosion.** Many-to-many joins silently inflate counts. Verify row count before/after each join. Use `COUNT(DISTINCT key)` through joins. Fix: investigate the relationship cardinality.
- **Survivorship bias.** As Phase 6.
- **Incomplete period comparison.** Comparing a partial period to a full period inflates the gap. Filter to complete periods or compare same-day-of-month.
- **Denominator shifting.** Definition of denominator changed between periods, making rates incomparable. Use consistent definitions; note any change.
- **Average of averages.** Wrong when group sizes differ. Always aggregate from raw data, never average pre-aggregated averages.
- **Timezone mismatches.** Different sources use different timezones. Standardize to one (UTC); document the choice.
- **Selection bias in segmentation.** Segments defined by the outcome are circular. Use pre-treatment characteristics.

### Sanity checks (run on every key number)

- Magnitude: order of magnitude correct vs known external benchmarks?
- Range: percentages in [0, 100], counts ≥ 0, no impossible values?
- Trend continuity: any unexplained jumps or drops?
- No exact-round-numbers (suggests filter or default-value issue)?
- Results don't *perfectly* confirm the hypothesis (reality is messier)?

### Cross-validation

- Compute the same metric two different ways; verify they match.
- Spot-check 3-5 individual records — trace their data manually.
- Compare to known external benchmarks (existing dashboards, prior reports, finance figures).
- Boundary checks — what happens at a single day, single user, single category?

## Phase 8 — Reporting & Dashboard Output

### A. Markdown report (always)

```markdown
# [Target] Data Report: [Period] [Scope]
*Generated: [timestamp] | Sources: [N inputs, M rows] | Confidence: [overall %]*

## Question
[The specific question being answered, in one sentence.]

## Executive Summary
[3-5 sentences: headline number, biggest variance/movement, top 1-2 insights, top action.]

## KPI Scorecard
| Metric | Actual | Prior | Budget | Var $ | Var % |
|---|---|---|---|---|---|
| (metrics that matter to this lens) | | | | | |

## Variance Commentary
[Material variances only, with volume × price × mix × timing decomposition.]

## [Business-Model Deep-Dive]
[Retail: product line + daypart + category. SaaS: cohort + NDR + CAC. PE: returns waterfall.]

## Cohort & Repeat Patterns
[As data supports.]

## Sensitivity & Scenarios
[Bull/Base/Bear; 1-2 relevant 2-way tables for the decision at hand.]

## Action Items
1. [Recommendation] — confidence X% — based on [data citation].
2. ...

## Statistical Caveats
[Which Phase 6 caveats apply; one sentence each.]

## QA Pitfalls Scanned
- Join explosion: ✓ checked / N/A.
- Incomplete period: ✓ checked.
- ...

## Data Sources
| Source | Format | As of | Rows | Transformations |
|---|---|---|---|---|

## Definitions
- [Metric]: [Exact computation.]
- [Segment]: [Exact membership rule.]

## Methodology
1. [Step 1.]
2. [Step 2.]
…
**Assumptions**: [list with rationale]
**Limitations**: [list with potential impact on conclusions]

## Sources & Citations
[Every quantitative claim → source pointer + row count + query timestamp.]

---
**Master Check: ✓ ALL CHECKS PASS**
*(or)* **Master Check: ✗ ERRORS DETECTED**
- [Failing item 1 with location]
```

### Citation discipline

Every quantitative claim cites: source pointer (`table.column`, `file.sheet`, API endpoint) + row count + query/load timestamp. **No claim without a source.**

### Confidence per finding

Mark every non-trivial claim with `confidence X%`. Pair with `to raise confidence: ...` when the gap is material — name the specific further investigation that would close it.

### Chart selection

| What you're showing | Best chart | Notes |
|---|---|---|
| Trend over time | Line chart | Wide aspect; YoY overlay if monthly |
| Category comparison | Vertical bar (sorted) | Avoid pie |
| Composition (≤6 cats) | Doughnut OR horizontal stacked bar | |
| Composition over time | Stacked area OR 100% stacked bar | |
| Distribution | Histogram + mean/median lines | |
| Distribution comparison | Box plot OR violin | |
| Correlation (2 vars) | Scatter + r + trend line | |
| Correlation matrix | Heatmap (RdBu_r) | |
| Cohort retention | Heatmap vintage matrix (sequential) | |
| 2-way sensitivity | Heatmap (RdBu_r) | |
| Variance waterfall | Horizontal bar, one per driver | |
| Performance vs target | Bullet chart | |
| Multi-metric KPIs | Small multiples | |

### Design principles

- Title states the insight, not the metric ("Revenue grew 23% YoY" beats "Revenue by Month").
- Axis labels with units. Date ranges noted.
- Bar charts start at zero. Always.
- Reduce chart junk — drop gridlines, borders, backgrounds that don't carry information.
- Colorblind-safe palette by default. Never rely on color alone — add patterns / line styles / direct labels.
- Print-friendly when relevant.
- Accessibility: alt text describing the insight, contrast, no info conveyed only by spatial position.

### B. KPI structure & decision rules *(from `kpi-dashboard`)*

Before rendering any dashboard, decide the tier and pick the KPIs.

**Tiered dashboard architecture:**

| Tier | Audience | Length | Cadence | Content |
|---|---|---|---|---|
| 1 | CEO / C-suite | 1 page | Daily or weekly | 5-8 company KPIs, status indicators, top risks/opportunities, action items |
| 2 | Functional VP | 1 page each | Daily or weekly | Sales / Marketing / Product / CS / Finance / Ops — KPI sets specific to the function |
| 3 | Operational team | Detailed, multi-section | Daily | Drivers behind Tier 2 KPIs, line-level detail |

The skill picks a tier from the user's intake. Default for a monthly board-style review: Tier 1. Default for an analyst's deep-dive: Tier 3.

**KPI documentation** — for each KPI surfaced in a dashboard, capture:

| Field | Example (retail) | Example (SaaS) |
|---|---|---|
| Name | Prime cost % | Net Revenue Retention |
| Owner | GM | VP Sales |
| Definition | (COGS + labor) / revenue | (End ARR from beg cohort − churn − contraction + expansion) / Beg ARR |
| Target | ≤60% | >110% |
| Threshold (yellow) | 60-65% | 100-110% |
| Alert (red) | >65% | <100% |
| Data source | `daily_order_items` + `time_entries` | `revenue.cohort_arr` + `revenue.churn` |
| Update frequency | Weekly | Monthly |
| Strategic link | Sustain margin while growing | Sustain efficient growth |
| Decision rules | >65% → escalate; cut prep waste; renegotiate vendor pricing | <100% → escalate; launch retention initiative |

**Leading vs lagging indicators** — surface both per dashboard:

- **Leading** (predictive): pipeline coverage, feature adoption, support-ticket volume, BBCO attach trend, daypart slot fill rate.
- **Lagging** (outcome): revenue, EBITDA, customer count, churn rate, BBCO retail GP.

Always pair the predictive chain. *"Declining feature adoption (Week 1-2) → predicts churn (Week 4-6)."* When a leading indicator turns yellow/red, the report's Action Items section names the predicted lagging consequence.

**Status indicators** — apply to every KPI:

| Symbol | Meaning |
|---|---|
| ✓ (green) | On track or exceeding target |
| ⚠ (yellow) | Slightly off track — monitor |
| ✗ (red) | Significantly off track — action required |
| ↑ / → / ↓ | Trend direction |

**Executive scorecard** (Tier 1 deliverable when scope is monthly review):

```
EXECUTIVE SCORECARD — [Period]

[KPI 1]: [value]
  Month: [actual]   Target: [target]   Status: ✓/⚠/✗
  YTD:   [ytd]      Target: [ytd target]   Trend: ↑/→/↓
  YoY:   [growth %]

[KPI 2-8 in same shape]

Key Risks & Opportunities
• [risk 1 with mitigation owner + date]
• [opportunity 1 with action]

Narrative (200-250 words)
[Lead sentence on the period's headline. What drove the variance. One concern with the active mitigation. Next-month priorities (max 3).]
```

Always pair the scorecard with the narrative — that's where the analyst translates the numbers into a story leadership can act on.

### C. Interactive HTML dashboard (when scope justifies)

Generate a single self-contained `.html` file using the Chart.js patterns from `interactive-dashboard-builder`. Structure:

```html
<!DOCTYPE html>
<html><head>
  <meta charset="UTF-8">
  <title>{Target} Dashboard — {Period}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1" integrity="..." crossorigin="anonymous"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0" integrity="..." crossorigin="anonymous"></script>
  <style>{full CSS color system + KPI cards + chart containers + filters + table + responsive + print}</style>
</head><body>
  <div class="dashboard-container">
    <header><h1>...</h1><div class="filters">...</div></header>
    <section class="kpi-row">...</section>
    <section class="chart-row">...</section>
    <section class="table-section">...</section>
    <footer>Data as of: <span id="data-date"></span></footer>
  </div>
  <script>
    const DATA = { /* pre-aggregated JSON; never embed >100k rows */ };
    class Dashboard { /* applyFilters → renderKPIs → updateCharts → renderTable */ }
    new Dashboard(DATA);
  </script>
</body></html>
```

Required elements:
- KPI card row with `formatValue` helpers (currency/percent/number; M/K abbreviation).
- Chart row with line / bar / doughnut / heatmap as the data dictates (per chart selection table).
- Filter row: dropdowns for categorical dimensions, date-range inputs, combined filter logic.
- Sortable table; pagination if rows > 200.
- Full CSS: color system, layout grids, KPI cards, chart containers, filters, table, responsive breakpoints (≤768 stacks columns), print styles.

### Data-size handling

| Rows | Approach |
|---|---|
| <1,000 | Embed raw, full interactivity. |
| 1,000-10,000 | Embed raw; pre-aggregate for charts. |
| 10,000-100,000 | Pre-aggregate server-side; embed only aggregates. |
| >100,000 | Not suitable for client-side dashboard — paginate or use a BI tool. |

Limit line charts to <500 points per series. Limit bar charts to <50 categories. Disable chart animations when many charts on one page.

### D. Excel data pack — audit-grade option *(from `datapack-builder`)*

When the user requests audit-grade output, IC-ready material, or "give me the underlying spreadsheet" — generate a structured Excel data pack alongside the markdown report. Defer Excel file creation to the `xlsx` skill (it owns the recalc validation pass).

**Standard 8-tab structure** (skip tabs the data doesn't support; note their absence):

1. Executive Summary — one-page overview, financial snapshot table, 3-5 highlights
2. Historical Financials (Income Statement) — 3-5 years actuals, revenue breakdown, margins
3. Balance Sheet — assets / liabilities / equity (when full statements available)
4. Cash Flow Statement — operating / investing / financing (when full statements available)
5. Operating Metrics — non-financial KPIs (units, customers, locations) — **no $ signs on counts**
6. Property/Segment Performance — breakdown by location / product line / business unit
7. Market Analysis — industry context, competitive positioning, peer benchmarks
8. Investment Highlights / Action Items — narrative summary

**Format-detection rules** (apply to every cell based on column/row label):

| Trigger words | Format | Example |
|---|---|---|
| Revenue, Sales, Income, EBITDA, Profit, Cost, Cash, Debt, CapEx (financial) | Currency `$#,##0.0` (millions) or `$#,##0`; negatives in parentheses `$(123)` | $50.0, $(15.0) |
| Units, Stores, Customers, Employees, Headcount (counts) | Number `#,##0` — **no $** | 1,250 stores |
| Margin, Growth, Rate, Yield, Return, Utilization, Occupancy | Percentage `0.0%` (display 15.0% not 0.15) | 15.0% |
| Year columns (2024, 2025E) | Text — prevents comma insertion | 2024, 2025E |

**Font color = semantic role** (mandatory, not decoration):

- **Blue** (RGB 0,0,255) — every hardcoded input (historical actuals, assumptions).
- **Black** (RGB 0,0,0) — every formula or calculation.
- **Green** (RGB 0,128,0) — links to other sheets / cross-tab references.

Layer 2 fill colors (optional unless brand specified): dark-blue section headers + white text; light-blue sub-headers; light-green input cells; white calculated cells. **Font color says WHAT it is. Fill color says WHERE it sits.**

**Discipline rules:**

- **Every calculated number is formula-based** — no hardcoded subtotals, totals, ratios, or derived metrics.
- **Cell comments cite source** — every blue input has a comment in this format: `Source: [System/Document], [Date], [Reference], [URL if applicable]`.
- **Adjustment schedule on every normalization** — restructuring add-backs, SBC treatment, acquisition costs, related-party normalization. Document what was adjusted, why, dollar impact, and recurrence assessment.
- **Industry adaptations** for Tab 5 (when the lens detects a specific industry):
  - **Tech / SaaS** — ARR, NDR, CAC, LTV, Rule of 40, Magic Number.
  - **Manufacturing / industrial** — capacity utilization %, units produced, inventory turns, gross margin by product line, order backlog.
  - **Real estate / hospitality** — properties / rooms / square footage, occupancy %, ADR, RevPAR (currency), NOI, cap rate %.
  - **Hospitality (kava bar / restaurant / retail)** — covers/day, AUR, prime cost %, beverage cost %, attach rate (matches the retail lens above).
  - **Healthcare / services** — locations, providers, visits (volume), revenue per visit (currency), payor mix %, same-store growth %.

**Filename convention:** `[Target]_DataPack_YYYY-MM-DD.xlsx`. Run the `xlsx` recalc validation pass before delivery; zero formula errors required (`#REF!`, `#DIV/0!`, `#VALUE!`, etc.).

## Phase 9 — Workflow

| Phase | Goal | Inputs | Exit criterion |
|---|---|---|---|
| 1 | Intake & scope | user prompt, provided data | scope, period, target, output, lens, definitions confirmed |
| 2 | Data foundation | data sources | shape mapped, quality rubric scored, gaps flagged |
| 3 | Financial pass | profiled data | numbers computed, materiality applied, integrity checks pass |
| 4 | Unit economics | data + lens | core metrics + cohorts + quality score for the lens |
| 5 | Sensitivity & scenarios | analysis output | Bull/Base/Bear computed; key 2-way tables built |
| 6 | Statistical caveats | analysis output | applicable caveats stated |
| 7 | QA pitfalls | analysis output | each pitfall checked or noted N/A |
| 8 | Compose & verify | all above | report drafted; optional dashboard rendered; verification checklist passes |

Move forward only when the exit criterion holds. If a phase fails, stop and surface the failure — never paper over it.

## Sub-skill invocation map

**Inline (default)** — embed the framework content from all 11 source skills directly in this SKILL.md so the merge runs as one self-contained skill. No skill-tool calls during runtime.

**Optional skill calls** — invoked only when the user's environment supports them, never auto-invoked:
- `/from-kc-records` — Toast ETL refresh when KC's `kc-actuals` D1 is stale.
- `/kc-pulse` — live-ops snapshot for KC.
- `/scorecard-sync` — Toast → Google Sheet alignment for monthly close.
- `/deep-research` — external benchmarks for non-KC businesses.
- `/from-prompter` — prompt optimization (skill-author tool, not runtime).

The skill detects when these are applicable from the user's intake and asks before invoking.

## Output Verification Checklist

Run at the end of every analysis. Render the result as the master check.

- [ ] **Source verification**: every data input named with "as of" date and row count.
- [ ] **Profile pass**: completeness rubric scored; any column <95% complete called out as caveat.
- [ ] **Calculation checks**: aggregation grain, denominators, joins, deduplication all verified.
- [ ] **Reasonableness**: every key number passes the smell test (magnitude, range, trend continuity).
- [ ] **Materiality applied**: no noise variances reported.
- [ ] **Cross-statement integrity**: subtotals add, period roll-forwards tie, cross-references match.
- [ ] **Business-model lens declared**: §4 lens and reasoning stated up front.
- [ ] **Translation discipline**: no framings bled across lenses (no IRR in retail; no NDR in PE; no Magic Number in marketplace).
- [ ] **Confidence per finding**: every non-trivial claim has %, with "to raise confidence" when material.
- [ ] **Citation per claim**: source pointer + row count + timestamp on every quantitative statement.
- [ ] **Statistical caveats**: at least one applicable Phase 6 caveat stated.
- [ ] **Pitfalls scanned**: each Phase 7 pitfall checked or noted N/A with reason.
- [ ] **Reproducibility**: definitions, methodology, assumptions, limitations documented.
- [ ] **Scenarios validate**: hierarchy holds (Bull > Base > Bear absolute; inverted for cost %).
- [ ] **If dashboard generated**: file path, sections list, data-size class noted.
- [ ] **Master check rendered**: ✓ or ✗ with failing items identified.

## Anti-patterns (do not do these)

- **Asking the user "what would you like me to analyze?"** when they've provided data and a question. Just analyze it.
- **Claiming a metric without citing a source.** Every quantitative statement gets a source pointer + row count + timestamp.
- **Bleeding framings across lenses.** Don't use NDR for a PE deal. Don't use IRR for a kava bar's monthly review. Don't use Rule of 40 for a marketplace.
- **Reporting noise variances.** Apply materiality before commentary.
- **Asserting causation from correlation.** State the correlation; name the alternatives; recommend the controlled comparison.
- **Skipping the master check.** It's the final answer to "is this analysis trustworthy?"
- **Hardcoding KC tables / BBCO substance / build_interactive.py paths into the analysis.** The skill discovers structure at runtime.
- **Stalling with offers ("I could do X, Y, or Z")** instead of just running the pass.

## Examples

### Example 1 — KC retail, BBCO product-line review

User: "everything-data: April KC P&L variance with BBCO mix"

Skill behavior:
1. Lens = Retail/hospitality (KC POS data signals).
2. Profiles the data sources (likely `kc-actuals.daily_order_items` + `monthly_actuals` + `bbco_flavor_substance` + `time_entries` as the user has them connected).
3. Builds April P&L with category breakdown (Kava* / Kratom* / Taps* / Mixed Drinks* / Food* / Retail* / Apparel*).
4. Variance: April actual vs March prior vs budget, with volume × price × mix × timing decomposition for material variances.
5. Prime cost % calculated.
6. **BBCO product-line section** as the deep-dive: SKU velocity, substance mix, attach rate, contribution to retail GP.
7. Daypart × DOW heatmap.
8. Sensitivity: BBCO 4-pack price × volume lift; traffic × ticket size.
9. Statistical caveats stated; QA pitfalls scanned.
10. Markdown report + optional self-contained dashboard.
11. Master check.

### Example 2 — Generic SaaS CSV

User: "everything-data: analyze the SaaS metrics in this customer.csv"

Skill behavior:
1. Lens = SaaS (customer-IDs with start/cancel dates signal it).
2. Profiles the CSV.
3. Builds revenue (ARR) waterfall: Beg → New → Expansion → Contraction → Churn → End.
4. Cohort vintage matrix.
5. NDR / GRR / logo churn / dollar churn.
6. LTV / CAC blended + segmented.
7. Benchmarks vs Rule of 40, Magic Number, NDR bands, LTV:CAC, GRR, CAC payback.
8. Sensitivity: NDR × new-logo growth.
9. **No KC references. No BBCO. No retail framings.**
10. Statistical caveats; QA pitfalls.
11. Markdown report.
12. Master check.

### Example 3 — PE-style returns review

User: "everything-data: returns sensitivity for this deal at 6/8/10x exit"

Skill behavior:
1. Lens = PE.
2. Gathers / confirms entry / financing / operating / exit assumptions.
3. Base case returns: MOIC, IRR, returns waterfall (growth, multiple, leverage, fees).
4. 2-way sensitivities: Entry × Exit; Growth × Exit; Leverage × Exit; Hold × Exit.
5. Bull / Base / Bear scenarios.
6. Returns attribution decomposition.
7. **No NDR. No retail metrics. No SaaS cohort lingo.**
8. Statistical caveats (relevant ones); QA pitfalls.
9. Markdown report; optional Excel-shaped output if requested.
10. Master check.

<!--
Maintainer notes (do not surface to runtime users):
- Framework only; runtime data shapes specifics. No business-specific tables preprogrammed.
- KC + BBCO are the canonical case. When KC detected, prefer retail/hospitality lens; when BBCO mentioned, run product-line section as the deep-dive.
- Re-run /from-prompter when framework changes materially.
- Do not call the 11 source skills at runtime — content already merged.
- Do not auto-call /from-kc-records. Surface option when KC data looks stale; let the user decide.
-->

