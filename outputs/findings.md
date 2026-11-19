# Mini #19 — findings (GadgetHub.pk, SAMPLE data)

Fictional Pakistani online gadgets store, Jan–Jun 2026.
**SAMPLE / DEMO data only** — invented store, invented orders,
never real client or real business data. Every number below is
recomputed from `data/raw/orders_SAMPLE.csv` by `src/analyze.py`
and re-checked independently by `src/checks.py`.

## Headline numbers

- **1,000 order lines** (1,000 orders)
  worth **PKR 39,936,829** across 20 products.
- **Mobiles dominate revenue**:
  PKR 21,474,048
  (53.77% of all revenue) from
  365 lines. Laptops are second at
  PKR 13,928,500
  (34.88%)
  — the two big-ticket categories together are
  88.7%
  of revenue.
- **Website is the biggest channel**:
  PKR 18,898,644
  (47.32%).
- **Lahore is the clear leading city**:
  PKR 15,041,107
  (37.66% of revenue).
- **2026-05 is the peak month**:
  PKR 9,883,200
  (24.75% of the half-year total).
- **COD is still king**: 481 lines
  (48.1% of all lines),
  PKR 19,911,443.

## What the 10 techniques show

1. **Category summary (t01).** Mobiles lead on lines
   (365) and revenue; Accessories are the
   opposite — 212
   lines but only
   PKR 605,712
   (1.52%).
   Cheap, frequent, small.
2. **Category x channel (t02).** The Website sells the expensive
   mix — Mobiles and Laptops dominate its revenue — while Daraz
   lives on Accessories and Audio.
3. **Pivot month x category (t03).** 4 of the 6
   categories peak in May (Mobiles, Laptops, Home Appliances, Accessories); Wearables peak
   in 2026-04 and Audio in
   2026-06 instead. Mobiles in May alone are
   PKR 5,440,382.
4. **Crosstab channel x payment (t04).** COD is the top payment
   method on every channel, not just overall — even on the Website.
5. **Transform shares (t05).** One line is never more than
   4.65% of its
   own category's total — no single order carries a category.
6. **Monthly growth (t06).** Revenue jumps
   64.59% in 2026-05
   (the biggest month-on-month move), then falls back in June —
   the May spike is seasonal, not a new level.
7. **Top-3 products per category (t07).** The top product in
   Mobiles is Infinix Note 40
   (PKR 6,551,832);
   in Laptops it is HP Laptop 15
   (PKR 5,800,000).
8. **City distinct counts (t08).** Lahore, Karachi, Islamabad, Faisalabad
   each sell all 20 products; only
   Rawalpindi is narrower
   (19 products) — the smaller
   cities buy almost the full range, so the gap is revenue, not
   range.
9. **Payment-method agg (t09).** JazzCash has the highest
   average line value
   (PKR 43,242),
   Easypaisa the lowest
   (PKR 33,402) — the payment mix follows the basket, not
   the other way round.
10. **Pareto (t10).** The top 4 products (20% of the
    20) bring in **58.13% of all revenue**.
    The single biggest product is
    Infinix Note 40
    (PKR 6,551,832,
    16.41% on its own).

## The Daraz trap

Daraz looks healthy on volume — 256 lines,
the second-biggest channel — but its average order value is only
PKR 15,329.05, against
PKR 61,760.27 on the Website. Same store, same
half-year: Daraz moves cheap accessories one at a time, the Website
moves phones and laptops. Judging Daraz by line count alone would
overstate it by roughly 4x on value.

## Limits

- SAMPLE data: the store, the orders and the "findings" are
  invented to teach the techniques. The pandas patterns are real.
- One half-year only (Jan–Jun 2026); no year-on-year comparison
  is possible from this file.
- `order_id` is one row per order line here (one product per
  order), so "distinct orders" equals lines in this dataset.
