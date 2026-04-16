---
name: from-kc-records
description: >
  Extract KC Clearwater financial records from Gmail and CSV uploads into the
  kc-actuals D1 database. Trigger on "from-kc-records", "catch up the database",
  "pull new records", "sync financials", "extract new expenses", "get latest Toast data",
  "what invoices came in", "update kc-actuals", "OCR receipts", "scan attachments",
  "read receipt photos", or any mention of extracting KC Clearwater expenses, invoices,
  receipts, Toast sales, COGS, or vendor orders. Handles revenue (Toast daily/weekly emails),
  expenses (17+ vendors via Gmail), CSV uploads, and receipt image OCR. Always use instead
  of ad-hoc Gmail searching for KC Clearwater financial data.
---

# from-kc-records

Load Toast POS CSV/XLSX exports into the KC Clearwater D1 databases. This skill covers the full ETL pipeline: parsing, normalization, classification, insertion, and validation.

---

## Step 0: Database Context

Before loading any data, query the current state of reference tables to understand what exists:

```sql
-- ACTUALS_DB: Current monthly coverage
SELECT year, month, revenue, units_sold, is_locked FROM monthly_actuals ORDER BY year, month;

-- ACTUALS_DB: Existing sales_items date ranges
SELECT DISTINCT source, period_start, period_end FROM sales_items ORDER BY period_start;

-- ACTUALS_DB: Existing modifier date ranges
SELECT DISTINCT source_month, COUNT(*) as rows FROM item_modifier_selections GROUP BY source_month;

-- ACTUALS_DB: Existing daily_order_items date ranges
SELECT MIN(date) as earliest, MAX(date) as latest, COUNT(*) as rows FROM daily_order_items;

-- ACTUALS_DB: Existing time_entries date ranges
SELECT MIN(business_date) as earliest, MAX(business_date) as latest, COUNT(*) as rows FROM time_entries;

-- ACTUALS_DB: Settings
SELECT key, value FROM settings ORDER BY key;

-- ACTUALS_DB: Scraper health
SELECT * FROM scraper_log ORDER BY run_date DESC LIMIT 10;

-- ACTUALS_DB: Employee roster
SELECT canonical_name, is_active FROM employees ORDER BY is_active DESC, last_seen DESC;

-- ACTUALS_DB: Employee aliases
SELECT raw_name, canonical_name FROM employee_aliases;

-- ACTUALS_DB: BBCO flavor-substance mapping
SELECT flavor, substance FROM bbco_flavor_substance;
```

---

## Step 1: Identify Input Files

Toast exports come in several CSV/XLSX formats. Identify which type(s) you have:

| File Pattern | Type | Target Table | Tier |
|---|---|---|---|
| `ItemSelectionDetails_YYYY_MM_DD-YYYY_MM_DD.csv` | Item Selection Details | `daily_order_items` | TIER 1 |
| `ItemModifierSelectionDetails_YYYY_MM_DD-YYYY_MM_DD.csv` | Modifier Selections | `item_modifier_selections` | TIER 1 |
| `ProductMix_YYYY-MM-DD_YYYY-MM-DD.xlsx` | Product Mix | `sales_items` | TIER 1 |
| `TimeEntryDetail_*.csv` | Time Entries | `time_entries` | TIER 1 |
| Expense/invoice CSVs | Expense Orders | `expense_orders` + `expense_line_items` | TIER 1 |

**Priority:** Load in order: Item Selection Details first (order-level data), then Modifiers (substance attribution), then Product Mix (monthly aggregates), then Time Entries (labor).

---

## Step 2: Date Range & Deduplication Check

Before loading, verify what already exists for the target date range:

```sql
-- For Item Selection Details
SELECT date, COUNT(*) FROM daily_order_items
WHERE date BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'
GROUP BY date ORDER BY date;

-- For Modifiers
SELECT source_month, COUNT(*) FROM item_modifier_selections
WHERE source_month = 'YYYY-MM'
GROUP BY source_month;

-- For Product Mix
SELECT year, month, COUNT(*) FROM sales_items
WHERE year = YYYY AND month = MM
GROUP BY year, month;

-- For Time Entries
SELECT business_date, COUNT(*) FROM time_entries
WHERE business_date BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'
GROUP BY business_date ORDER BY business_date;
```

**If data exists:** Use DELETE + re-insert for the target period (idempotent pattern). Do NOT append blindly.

---

## Step 3: File Encoding & Header Detection

All Toast CSV exports may use different encodings. Try in order:
1. `utf-8-sig` (BOM-prefixed UTF-8, most common)
2. `cp1252` (Windows)
3. `latin-1` (fallback)

**Header detection:** Toast changes column names between versions. Use flexible aliasing:

| Standard Name | Known Aliases |
|---|---|
| `order_number` | `Order #`, `Order Number`, `Order Id` |
| `sent_date` | `Sent Date`, `Date`, `Transaction Date` |
| `server` | `Server`, `Employee`, `Staff` |
| `menu_item` | `Menu Item`, `Item`, `Menu Selection` |
| `menu_group` | `Menu Group`, `Group` |
| `sales_category` | `Sales Category`, `Category` |
| `qty` | `Qty`, `Quantity`, `Qty Sold` |
| `gross_price` | `Gross Price`, `Gross Sales`, `Price` |
| `net_price` | `Net Price`, `Net Sales` |
| `discount` | `Discount`, `Discount Amount` |
| `void` | `Void?`, `Voided`, `Is Void` |
| `item_selection_id` | `Item Selection Id`, `Selection ID` |

---

## Step 4: Parse & Transform

### 4a: Item Selection Details CSV (TIER 1 — ORDER-LEVEL DATA)

**Target table:** `daily_order_items`

**Columns:** Order #, Date, Server, Shift, Dining Option, Menu Item, Menu Subgroup, Menu Group, Sales Category, Gross Price, Discount, Net Price, Qty, Tax, Void?, Tab Name, Item Selection ID

**Parsing rules:**
- **Date normalization:** `M/D/YY H:MM AM/PM` or `MM/DD/YYYY` → `YYYY-MM-DD`
- **Shift normalization:** 16-way map:
  - `breakfast`, `am shift`, `am` → `AM`
  - `lunch`, `mid shift`, `mid` → `MID`
  - `dinner`, `pm shift`, `pm` → `PM`
  - `late night`, `on shift`, `on` → `ON`
- **Void flag:** `yes`, `true`, `1`, `void` → 1; else 0
- **Synthetic ID:** If `item_selection_id` is missing, generate `SYN-YYYY-MM-DD-XXXXXX`
- **Normalization:** Apply `normalize()` to server, menu_item, menu_group, sales_category (see Step 4e)
- **Dedup key:** `(date, item_selection_id)` — INSERT OR IGNORE

**Post-insert:**
1. Update `employees` table — add new employees, update `is_active` flag and `last_seen`
2. Classify substance per Step 4f
3. Verify `sales_category` is populated for all non-void items

**Category note:** `"Bulas*"` NO LONGER EXISTS as of 2026-03-28. Items previously in `Bulas*` are now in `Kava*` (brewed kava), `Kratom*` (shots/elixirs), or `Taps*` (Bula Bombs).

### 4b: Product Mix XLSX (TIER 1 — MONTHLY AGGREGATES)

**Target table:** `sales_items`

**Source:** "Items" sheet in ProductMix XLSX

**Columns:** Item, Sales Category, Qty sold, Avg. price, Gross sales, Discount amount, Void amount, Net sales

**Parsing rules:**
- **Period:** Extract from filename or pass as arguments (`period_start`, `period_end`)
- **Year/month:** Derive from `period_start`
- **Section:** Map from Sales Category (Kava → brew, Kratom → shots, Taps → kegs, Food → food, etc.)
- **Source:** `product-mix-YYYY`
- **Normalization:** Apply `normalize()` to `item_name` (see Step 4e)
- **Dedup:** DELETE all rows for the target year/month + source, then INSERT fresh

### 4c: Time Entry CSVs (TIER 1 — LABOR)

**Target table:** `time_entries`

**Columns:** Employee, Job Title, In Date, Out Date, Payable Hours

**Parsing rules:**
- **Name flip:** `"Last, First"` → `"First Last"` via `flip_name()`
- **Normalization:** Apply `normalize_name()` to employee_name (see Step 4e)
- **Date normalization:** `M/D/YY H:MM AM/PM` → `YYYY-MM-DD HH:MM`
- **Shift derivation from clock-in hour:**
  - AM: 5:00–11:59
  - MID: 12:00–15:59
  - PM: 16:00–20:59
  - ON: everything else (overnight)
- **Business date:** First 10 chars of `clock_in` timestamp
- **Source:** `time-entries-YYYY`
- **Dedup key:** `(employee_name, clock_in)` — INSERT OR IGNORE

### 4d: Item Modifier Selections CSV (TIER 1 — SUBSTANCE ATTRIBUTION)

PROMOTED from TIER 2 to TIER 1 on 2026-03-28. This data is now critical for substance attribution.

**Target table:** `item_modifier_selections`

**Format change (Mar 2026+):** 7 columns only:
- Sent Date, Server, Modifier, Parent Menu Selection, Discount, Net Price, Qty
- Order # and Option Group Name columns **removed by Toast**

**Old format (2025–Feb 2026):** 11 columns:
- Order #, Sent Date, Server, Modifier, Option Group Name, Parent Menu Selection, Discount, Net Price, Qty, Void?, Void Reason

**Parsing rules:**
- **Date normalization:** `M/D/YY H:MM AM/PM` → `YYYY-MM-DD HH:MM:SS`
- **Synthetic order number (Mar 2026+):** Generate `MOD-YYYY-MM-NNNNN` since Toast removed Order #
- **source_month:** `YYYY-MM` derived from `sent_date`
- **Normalization:** Apply `normalize()` to server, modifier, parent_menu_selection (see Step 4e)
- **Dedup:** DELETE all rows for the target source_month, then INSERT fresh

### 4e: Text Normalization (MANDATORY — ALL CSV LOADS)

MANDATORY for all Toast CSV imports. Apply these normalization functions to every text field BEFORE INSERT:

**`normalize(field)`** — collapses double-spaces, strips leading/trailing whitespace, fixes smart quotes (curly → straight)

```python
def normalize(s):
    if s is None:
        return None
    s = str(s).strip()
    s = s.replace('\u2018', "'").replace('\u2019', "'")  # smart single quotes
    s = s.replace('\u201c', '"').replace('\u201d', '"')  # smart double quotes
    while '  ' in s:
        s = s.replace('  ', ' ')
    return s if s else None
```

**`normalize_name(field)`** — same as `normalize()` plus title-case and "Last, First" → "First Last" conversion

```python
def normalize_name(s):
    s = normalize(s)
    if s is None:
        return None
    # Flip "Last, First" to "First Last"
    if ',' in s:
        parts = s.split(',', 1)
        s = f"{parts[1].strip()} {parts[0].strip()}"
    return s.title()
```

**Apply to:**
| CSV Type | Fields to Normalize |
|---|---|
| Item Selection Details | server, menu_item, menu_group, sales_category |
| Item Modifier Selections | server, modifier, parent_menu_selection |
| Time Entries (employee_name) | employee_name (use `normalize_name()`) |
| Product Mix | item_name |

**Post-insert verification:**
```sql
-- Must return zero rows. If not, normalization was skipped.
SELECT COUNT(*) FROM daily_order_items WHERE server LIKE '%  %';
SELECT COUNT(*) FROM daily_order_items WHERE menu_item LIKE '%  %';
SELECT COUNT(*) FROM item_modifier_selections WHERE server LIKE '%  %';
SELECT COUNT(*) FROM item_modifier_selections WHERE modifier LIKE '%  %';
```

### 4f: Substance Classification (post-insert for daily_order_items)

After loading new `daily_order_items` rows, classify the `substance` column. Apply layers in order — first match wins:

**Layer 1 — Named categories:**
- `sales_category LIKE 'Kava%'` → substance = `'kava'`
- `sales_category LIKE 'Kratom%'` → substance = `'kratom'`

**Layer 2 — Named taps (fixed substance per keg):**
- Tiki Apple, NSA Tiki Apple, Island Breeze, Blueberry Lemonade, Rootbeer, Passionfruit Mojito, Lavender Lemonade → `'kratom'`
- Orange Dream, Tutti Frutti → `'kava'`
- Lemon Pound Cake, Perfect Pear, Gummy Bear → `'delta9'`

**Layer 3 — Bula Bombs:**
- Default to `'kratom'` (99%+ of modifier data shows kratom shots)
- If modifier join available, check tap strain: kava taps (Orange Dream/Tutti Frutti) → `'mixed'`

**Layer 4 — Cocktails:**
- Mixed Drinks\*, Happy Hour, Early Bird, Seasonal Drinks → `'kratom'` (99%+ per modifier data)
- EXCEPTIONS:
  - Double Bula (HH) → `'kava'`
  - 6PM Slam\* → `'kava'`
  - Double/Single Top Shelf Elixir → `'kava'`
  - Growler O' Kava → `'kava'`
  - Bu-Latte → `'kava'`

**Layer 5 — Non-drink categories:**
- Teas & Coffee\*, Food\*, Hot Food, Apparel\* → `'none'`
- Kids Drinks\* → `'none'`
- Events, AYCD, fees, pool → `'none'`

**Layer 6 — Retail:**
- BBCo cans/packs → `'mixed'` (flavor varies per order)
- Rhino Dart → `'kava'`
- Plant Tribals, Kratom Capsules → `'kratom'`
- Kava Root, Kava Lift, Kava Candy → `'kava'`
- New Level / KBD add-ons → `'kratom'`

**Layer 7 — Residual:**
- BYO Newbie Special → `'kratom'` (99.2% per modifier data)
- Kavatender's Choice → `'kratom'` (100% per modifier data)
- Generic tap promos (Buy1 Get 50%, Mixed Tap, Tap Flight) → `'mixed'`

---

## Step 5: Generate & Execute SQL

**Batch sizing:**
- 200 rows per INSERT statement
- 8 statements per SQL file (for large datasets)
- Use `INSERT OR IGNORE` with UNIQUE constraints for deduplication

**Execution pattern:**
```bash
# Generate SQL files
python3 dev-docs/scripts/load-<type>.py --data-dir ./path/to/csvs --output-dir ./output

# Execute to remote D1
npx wrangler d1 execute kc-actuals --file=output/file.sql --remote

# Or execute locally for testing
npx wrangler d1 execute kc-actuals --file=output/file.sql --local
```

**Idempotency:** All loaders use either:
- DELETE + re-insert for the target period (modifiers, product mix)
- INSERT OR IGNORE with UNIQUE constraints (daily_order_items, time_entries, daily_performance)

Both patterns are safe to re-run.

---

## Step 6: Post-Insert Validation

Run ALL of these checks after every load. Fix any failures before proceeding.

```sql
-- Row count verification (compare against CSV line count minus header)
SELECT COUNT(*) as loaded FROM daily_order_items WHERE date BETWEEN 'START' AND 'END';
SELECT COUNT(*) as loaded FROM item_modifier_selections WHERE source_month = 'YYYY-MM';
SELECT COUNT(*) as loaded FROM sales_items WHERE year = YYYY AND month = MM;
SELECT COUNT(*) as loaded FROM time_entries WHERE business_date BETWEEN 'START' AND 'END';

-- Double-space check (must be zero — normalization was skipped if nonzero)
SELECT 'doi.server' as field, COUNT(*) FROM daily_order_items WHERE server LIKE '%  %'
UNION ALL SELECT 'doi.menu_item', COUNT(*) FROM daily_order_items WHERE menu_item LIKE '%  %'
UNION ALL SELECT 'mod.server', COUNT(*) FROM item_modifier_selections WHERE server LIKE '%  %'
UNION ALL SELECT 'mod.modifier', COUNT(*) FROM item_modifier_selections WHERE modifier LIKE '%  %';

-- NULL substance check (should be zero for non-void items with revenue)
SELECT COUNT(*) FROM daily_order_items
WHERE substance IS NULL AND is_void = 0 AND net_price > 0;

-- NULL sales_category check (should be zero for non-void items with revenue)
SELECT COUNT(*) FROM daily_order_items
WHERE (sales_category IS NULL OR sales_category = '') AND is_void = 0 AND net_price > 0;

-- Employee table sync check (should return no rows)
SELECT server FROM daily_order_items
WHERE server IS NOT NULL AND server != ''
  AND server NOT IN (SELECT canonical_name FROM employees)
GROUP BY server;

-- Date gap check (no missing days in range)
WITH RECURSIVE dates(d) AS (
  SELECT 'START_DATE'
  UNION ALL SELECT date(d, '+1 day') FROM dates WHERE d < 'END_DATE'
)
SELECT d as missing_date FROM dates
WHERE d NOT IN (SELECT DISTINCT date FROM daily_order_items)
AND strftime('%w', d) NOT IN ('0');  -- exclude Sundays if store is closed

-- Revenue sanity check (compare with Toast dashboard)
SELECT SUM(net_price) as total_net FROM daily_order_items
WHERE date BETWEEN 'START' AND 'END' AND is_void = 0;
```

---

## Step 7: Monthly Closing Procedure

After loading all data for a complete month, run the closing checklist:

1. **Verify all 4 data types loaded:** daily_order_items, item_modifier_selections, sales_items, time_entries
2. **Cross-check totals:** daily_order_items SUM(net_price) should approximate sales_items SUM(revenue) for the month
3. **Run monthly rollup:** `POST /api/scraper/rollup?year=YYYY&month=MM` or call `rollupMonthlyFromDaily()`
4. **Verify monthly_actuals updated:** Check revenue, units, COGS populated for the month
5. **Verify daily_performance coverage:** Ensure daily scraper data exists for all business days in the month
6. **Lock if final:** For completed months with verified data, set `is_locked = 1` on `monthly_actuals`
7. **Update employees table:** Refresh `is_active`, `last_seen`, `total_orders`, `total_shifts`
8. **Verify substance column:** Populated for all new daily_order_items
9. **Verify no "Bulas\*" category entries:** This category was eliminated 2026-03-28
10. **Cross-check COGS bridge:** Any new ingredients without bridge mappings?

---

## Reference: Database Tables

### ACTUALS_DB (kc-actuals) — 31 tables

| Table | Purpose |
|---|---|
| `monthly_actuals` | Monthly P&L rollup (revenue, COGS, GP, units) |
| `daily_performance` | Toast daily scraper data (35 fields) |
| `daily_shifts` | Shift-level daily breakdown |
| `daily_sales_categories` | Category-level daily breakdown |
| `daily_order_items` | Order-level item details (with substance column) |
| `expense_orders` | Purchase orders (COGS/OPEX classification) |
| `expense_line_items` | Order line items |
| `sales_items` | POS item sales by month (product mix) |
| `item_modifier_selections` | Order-line modifiers (sizes, strains, add-ons) |
| `time_entries` | Employee clock-in/out with shift derivation |
| `employees` | Employee roster (canonical_name, is_active, last_seen) |
| `employee_aliases` | Maps raw POS names to canonical employee names |
| `bbco_flavor_substance` | Maps BBCO can/pack flavors to substance type |
| `cogs_bridge` | Links ACTUALS_DB expense items to MENU_DB ingredients |
| `settings` | Key-value store config |
| `fixed_costs` | Monthly fixed expenses |
| `revenue_targets` | Monthly revenue targets |
| `product_cmr` | Product CMR scorecard |
| `budget_line_items` | COGS/OpEx budget waterfall |
| `promo_targets` | Shift-level discount targets |
| `pos_menu_map` | POS item name → clean menu item mapping (590→64) |
| `scraper_log` | Scraper run history |
| `data_source_guide` | Data quality documentation |
| `field_quality` | Field-level trust ratings |
| `product_source_map` | Item source classification |
| `toast_weekly_performance` | Weekly performance email scrapes |
| `event_hosts` | Event host costs |

### MENU_DB (kc-menu-2) — READ ONLY

| Table | Purpose |
|---|---|
| `menu_items` (64) | Canonical menu item catalog |
| `ingredients` (48) | Ingredient costs |
| `recipes` (38) | Recipe definitions |
| `recipe_components` (149) | Recipe ingredient links |
| `brew_recipes` (8) | Brew batch costings |
| `tap_drinks` (10) | Tap drink definitions |
| `tap_keg_costs` (10) | Keg cost per drink |
| `food_items` (20) | Food item costs |
| `retail_products` (12) | Retail item costs |

### Dropped Tables (no longer in schema)
- `order_substance_map` — temporary, dropped after substance column built on daily_order_items
- `monthly_revenue` — dropped (data now in monthly_actuals + daily_performance)
- `chart_of_accounts` — dropped (data now in budget_line_items + expense_orders)

---

## Reference: Loader Scripts

| Script | Purpose | Target Table |
|---|---|---|
| `dev-docs/scripts/load-item-selection-details.py` | Item Selection Details CSV → SQL | `daily_order_items` |
| `dev-docs/scripts/load-march-2026.py` | Modifier CSV + Product Mix XLSX → SQL | `item_modifier_selections`, `sales_items` |
| `dev-docs/scripts/load-time-entries.py` | Time Entry CSV → SQL | `time_entries` |
| `dev-docs/scripts/normalize_text.py` | Text normalization functions | (imported by other scripts) |

---

## Reference: Source Column Conventions

| Value | Meaning |
|---|---|
| `seed-2025` | Initial 2025 data seed |
| `toast-2025` | Toast scraper (2025) |
| `product-mix-YYYY` | Product Mix XLSX upload |
| `csv-upload` | Generic CSV upload |
| `receipt-ocr` | Receipt image OCR |
| `gmail-scan` | Gmail invoice extraction |
| `gmail-2026` | Gmail 2026 expense scan |
| `time-entries-YYYY` | Time entry CSV upload |
| `item-details-YYYY` | Item selection details CSV upload |
