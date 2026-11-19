# Mini #19 — Python pandas GroupBy, Pivot & Aggregation Pack

**Status:** built and verified locally — publish pending
(https://github.com/mhkh-stock/mini19-python-pandas-groupby-pivot).

**SAMPLE / DEMO data only.** Fictional store, fictional orders,
fictional numbers. Never claimed as real client work.

The aggregation companion to Mini #13's cleaning pack: the same
"one shop, one file" idea, now taught as grouping. A fictional
Pakistani online gadgets store — GadgetHub.pk — with 1,000 order
lines, Jan–Jun 2026. Ten pandas techniques, one per file, each
answering a question a store owner would actually ask: which
category pays the bills, which channel is volume without value,
which city leads, whether cash-on-delivery still rules, and how
concentrated the revenue really is. Every number is recomputed
independently from the raw CSV by `src/checks.py`.

## Business question

"Which parts of this store actually make the money — and which
parts only look busy?"

## What is inside

| File | What it does |
|---|---|
| `outputs/findings.md` | The teaching write-up: headline numbers + what each technique shows |
| `outputs/summary.json` | Every verified headline number, machine-readable |
| `outputs/t01_category_summary.csv` | Technique 1 — groupby sum/mean/count by category |
| `outputs/t02_category_channel.csv` | Technique 2 — multi-level groupby category × channel |
| `outputs/t03_pivot_month_category.csv` | Technique 3 — pivot_table revenue, month × category |
| `outputs/t04_crosstab_channel_payment.csv` | Technique 4 — crosstab channel × payment method |
| `outputs/t05_line_share_of_category.csv` | Technique 5 — transform: each line's share of its category |
| `outputs/t06_monthly_growth.csv` | Technique 6 — monthly resample + month-on-month growth |
| `outputs/t07_top3_products_per_category.csv` | Technique 7 — top-3 products per category |
| `outputs/t08_city_distinct_counts.csv` | Technique 8 — nunique / distinct counts per city |
| `outputs/t09_payment_method_agg.csv` | Technique 9 — agg with sum/mean/min/max/count by payment |
| `outputs/t10_pareto_products.csv` | Technique 10 — cumulative share / Pareto by product |
| `data/raw/orders_SAMPLE.csv` | The 1,000-line SAMPLE file the analysis reads |
| `data/README.md` | Data dictionary + how the story was weighted |
| `src/generate_data.py` | Regenerates the SAMPLE CSV (seed 19, deterministic) |
| `src/analyze.py` | The 10 pandas techniques + summary.json + findings.md |
| `src/checks.py` | Checks as code — 341 checks, all passing |
| `requirements.txt` | pandas only (`pandas>=2.0,<3`) |

## Key numbers (real numbers, recomputed from the CSV)

| KPI | Value |
|---|---|
| Order lines | 1,000 |
| Total units | 1,534 |
| Grand total | PKR 39,936,829 |
| Average line value | PKR 39,936.83 |
| Top category | Mobiles — PKR 21,474,048 (53.77%) |
| Second category | Laptops — PKR 13,928,500 (34.88%) |
| Top channel | Website — PKR 18,898,644 (47.32%) |
| Daraz lines / AOV | 256 lines / PKR 15,329.05 (Website AOV PKR 61,760.27) |
| Top city | Lahore — PKR 15,041,107 (37.66%) |
| Peak month | 2026-05 — PKR 9,883,200 (24.75%), +64.59% MoM |
| COD | 481 lines (48.1%), PKR 19,911,443 |
| Pareto: top 4 of 20 products | 58.13% of all revenue |
| Biggest single product | Infinix Note 40 — PKR 6,551,832 (16.41%) |
| Checks | 341 passing (`python3 src/checks.py`) |

## The 10 techniques

| # | Technique | pandas pattern | What it answers |
|---|---|---|---|
| 1 | Groupby summary | `groupby().agg(sum, mean, size)` | Which category pays the bills? |
| 2 | Multi-level groupby | `groupby([category, channel])` | Where does each category sell? |
| 3 | Pivot table | `pivot_table(index=month, columns=category)` | Revenue by month × category |
| 4 | Crosstab | `pd.crosstab(channel, payment)` | Which payment rides which channel? |
| 5 | Transform | `groupby().transform("sum")` | Each line's share of its category |
| 6 | Resample + growth | `resample("M")` + `pct_change()` | Monthly trend and MoM growth |
| 7 | Top-N per group | `groupby().rank()` / `nlargest` | Top-3 products inside each category |
| 8 | Distinct counts | `nunique()` per city | How wide is each city's range? |
| 9 | Multi-function agg | `agg([sum, mean, min, max, count])` | Payment methods, five numbers at once |
| 10 | Pareto / cumulative | `sort_values` + `cumsum()` | How concentrated is the revenue? |

## What the pack teaches

1. **Group first, then ask.** Every business question here is a
   `groupby` away — the question picks the keys, pandas does the
   arithmetic.
2. **A pivot is a groupby in a grid.** Technique 3 and technique 1
   agree to the rupee: the pivot's column totals ARE the category
   totals. If they ever disagree, the pivot is wrong.
3. **Transform keeps the row count.** Technique 5 adds a column to
   all 1,000 lines instead of collapsing them — that is the whole
   difference between `transform` and `agg`, and the shares sum to
   exactly 1.0 inside every category.
4. **Volume is not value.** Daraz is the second-biggest channel by
   lines (256) and the smallest by average order value
   (PKR 15,329). Count the lines and you overstate Daraz ~4x.
5. **Concentration is a number, not a feeling.** The top 4 of 20
   products (20%) take 58.13% of revenue — the Pareto table proves
   it line by line, with the cumulative share ending at exactly
   100%.

## Verified numbers

| KPI | Value |
|---|---|
| Lines | 1,000 |
| Grand total | PKR 39,936,829 |
| Top category | Mobiles, 53.77% |
| Top city | Lahore, 37.66% |
| Peak month | 2026-05, PKR 9,883,200 |
| Pareto (top 4 products) | 58.13% |
| Checks | 341 passing (`python3 src/checks.py`) |

Verification: `python3 src/checks.py` — every headline number is
recomputed from the raw CSV with the standard library only (no
pandas) and compared against every output file: grand total agreed
by techniques 1, 2, 3, 6, 9 and 10; pivot row totals equal monthly
totals and column totals equal category totals; crosstab margins
equal channel and payment counts; transform shares sum to 1.0 per
category; top-3 lists and Pareto shares are recomputed from
scratch; the generator is re-run and byte-compared for
determinism (see `src/checks.py`).

## How to run it

1. Install the one dependency: `pip install -r requirements.txt`.
2. Read `outputs/findings.md` — that is the deliverable.
3. To regenerate the sample data: `python3 src/generate_data.py`.
4. To re-run the analysis: `python3 src/analyze.py`.
5. To check it: `python3 src/checks.py`.
6. To practise on your own data: replace the raw CSV (same
   columns) and re-run steps 4–5 only — do NOT re-run step 3, it
   regenerates the sample data and would overwrite your file.

## Two traps this pack teaches

- **A pivot that doesn't reconcile is a wrong pivot.** The
  pivot's row and column totals must equal the groupby totals —
  technique 3 is only trusted because `src/checks.py` proves it
  against techniques 1 and 6.
- **Averages hide the mix.** The store's average line is
  PKR 39,937, but no channel actually averages that: the Website
  averages PKR 61,760 and Daraz PKR 15,329. One overall average
  describes a store that doesn't exist.

## Limits

- **SAMPLE data only.** The store and the orders are fictional;
  the "findings" are the story the seeded generator was weighted
  to tell (Mobiles lead, Daraz cheap, Lahore first, COD biggest,
  May peak). The pandas patterns are real.
- **One half-year only (Jan–Jun 2026)** — no year-on-year
  comparison is possible from this file.
- **`order_id` is one row per order line here** (one product per
  order), so "distinct orders" equals lines in this dataset.

## Published

Publish pending: https://github.com/mhkh-stock/mini19-python-pandas-groupby-pivot
