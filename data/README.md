# Mini #19 — data dictionary (SAMPLE / DEMO only)

Fictional store "GadgetHub.pk" — a made-up Pakistani online
gadgets store, 1,000 order lines, Jan–Jun 2026. The store, the
orders and every number are invented for teaching — the pandas
techniques are real, the business is not. Regenerate exactly
with `python3 src/generate_data.py` (seed 19, deterministic).
Analyse with `python3 src/analyze.py`.

## data/raw/orders_SAMPLE.csv (1,000 lines)

| Column | Meaning |
|---|---|
| `order_id` | Order line number, `ORD-2001` … `ORD-3000` (unique per line) |
| `order_date` | Order date, ISO `yyyy-mm-dd`, Jan–Jun 2026 |
| `category` | Product category: Mobiles, Laptops, Accessories, Audio, Home Appliances, Wearables |
| `product` | Product name (price is fixed per product) |
| `channel` | Sales channel: Website, App, Daraz, WhatsApp |
| `city` | Delivery city: Lahore, Karachi, Islamabad, Rawalpindi, Faisalabad |
| `payment_method` | COD, JazzCash, Easypaisa, Card |
| `quantity` | Units on the line (1–4; Daraz lines are almost always 1) |
| `unit_price` | Price per unit, PKR — fixed per product |
| `line_total` | Line total = quantity × unit_price |

## How the story was weighted (seed 19)

The generator is weighted so the analysis has real findings,
not flat noise:

- **Mobiles dominate revenue (53.77%):** the most lines (365)
  at mid-high prices. Laptops are second (34.88%) on only 54
  lines — the two big-ticket categories together are 88.7% of
  revenue.
- **Daraz is volume without value:** 256 lines (second-biggest
  channel) but its mix skews to cheap Accessories / Audio and
  quantity 1, so its average order value is PKR 15,329 against
  PKR 61,760 on the Website.
- **Lahore leads:** 34% of lines by weight, 37.66% of revenue
  (PKR 15,041,107).
- **COD is biggest:** 46% weight, 481 lines (48.1%), PKR 19,911,443.
- **May is the peak month:** 26% weight, 247 lines,
  PKR 9,883,200 (24.75% of the half-year), +64.59% on April.
- **Pareto:** the top 4 of 20 products (20%) take 58.13% of
  revenue — Infinix Note 40 alone is 16.41%.

## Totals (verified)

- 1,000 lines, 1,534 units, grand total PKR 39,936,829.
- Average line value PKR 39,936.83.
- Every line satisfies `line_total = quantity × unit_price`
  (checked by `src/checks.py`); every product has exactly one
  price.

## Known quirks

- **One product per order.** Each `order_id` is a single line
  with one product, so "distinct orders" (1,000) equals lines.
  A real store's multi-line orders would need a separate
  order-lines grain — this file keeps one line per order on
  purpose, so the groupby techniques stay readable.
- **The story is baked in.** The weights above are the findings;
  change the weights and the findings change. That is the point
  of a teaching dataset — but it also means no finding here is
  evidence about any real store.
