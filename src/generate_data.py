"""Regenerate data/raw/orders_SAMPLE.csv — Mini #19 sample data.

Fictional shop "GadgetHub.pk" — a made-up Pakistani online gadgets
store. ~1,000 order lines, Jan–Jun 2026. SAMPLE / DEMO data only —
never real client or real business data.

Seeded (seed 19) and fully deterministic: re-running this script
reproduces the file byte-for-byte (src/checks.py verifies that).

The generator is deliberately weighted so the analysis has real
findings to surface (the weights below are the story, not an
accident):

  * Mobiles dominate revenue — the most lines AND mid-high prices.
  * Daraz has high volume but the lowest average order value — its
    mix skews to cheap Accessories / Audio and mostly quantity 1.
  * Lahore is the clear leading city by lines and revenue.
  * COD is the biggest payment method by a wide margin.
  * May is the clear peak month (Eid-season spike in the story).

Columns: order_id, order_date, category, product, channel, city,
payment_method, quantity, unit_price, line_total.
line_total is always quantity x unit_price (checked by src/checks.py).
"""

import argparse
import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "data" / "raw" / "orders_SAMPLE.csv"

SEED = 19
N_LINES = 1000

CATEGORIES = ["Mobiles", "Laptops", "Accessories", "Audio",
              "Home Appliances", "Wearables"]

# Fixed price per product — the same price every time a product sells.
PRODUCTS = {
    "Mobiles": [("Samsung Galaxy A15", 42500),
                ("Infinix Note 40", 38999),
                ("Xiaomi Redmi 13", 34999),
                ("Oppo A18", 29999)],
    "Laptops": [("HP Laptop 15", 145000),
                ("Lenovo IdeaPad Slim 3", 128500),
                ("Dell Inspiron 15", 162000)],
    "Accessories": [("USB-C Cable 1m", 1499),
                    ("Wireless Mouse", 2499),
                    ("Laptop Stand", 3999),
                    ("Phone Cover", 999)],
    "Audio": [("Bluetooth Earbuds", 5999),
              ("Wired Earphones", 1499),
              ("Bluetooth Speaker", 8999)],
    "Home Appliances": [("Electric Kettle", 3499),
                        ("Ceiling Fan", 8500),
                        ("Iron Steamer", 6500)],
    "Wearables": [("Smartwatch Fit Pro", 9999),
                  ("Fitness Band", 4499),
                  ("Smartwatch Ultra", 18999)],
}

# Category mix per channel — this is what makes Daraz cheap and the
# Website expensive. Rows are the six categories in CATEGORIES order.
CHANNEL_CATEGORY_WEIGHTS = {
    # Website: skews to Mobiles + Laptops (big-ticket)
    "Website":  [0.46, 0.10, 0.12, 0.10, 0.10, 0.12],
    # App: close to the overall mix
    "App":      [0.38, 0.06, 0.20, 0.14, 0.12, 0.10],
    # Daraz: skews hard to cheap Accessories / Audio
    "Daraz":    [0.19, 0.01, 0.38, 0.24, 0.08, 0.10],
    # WhatsApp: skews to Mobiles + Home Appliances
    "WhatsApp": [0.42, 0.04, 0.16, 0.12, 0.18, 0.08],
}

CHANNEL_WEIGHTS = [("Website", 0.32), ("App", 0.28),
                   ("Daraz", 0.24), ("WhatsApp", 0.16)]
CITY_WEIGHTS = [("Lahore", 0.34), ("Karachi", 0.26),
                ("Islamabad", 0.16), ("Rawalpindi", 0.13),
                ("Faisalabad", 0.11)]
PAYMENT_WEIGHTS = [("COD", 0.46), ("JazzCash", 0.22),
                   ("Easypaisa", 0.18), ("Card", 0.14)]
# May is the peak month; February the quietest.
MONTH_WEIGHTS = [(1, 0.13), (2, 0.12), (3, 0.15),
                 (4, 0.16), (5, 0.26), (6, 0.18)]

# Quantity mix: mostly 1, rarely 4. Daraz lines are almost always 1.
QTY_WEIGHTS = [(1, 0.55), (2, 0.28), (3, 0.11), (4, 0.06)]
DARAZ_QTY_WEIGHTS = [(1, 0.82), (2, 0.14), (3, 0.03), (4, 0.01)]

COLUMNS = ["order_id", "order_date", "category", "product", "channel",
           "city", "payment_method", "quantity", "unit_price",
           "line_total"]


def weighted(rng, pairs):
    """Pick one label from [(label, weight), ...] using rng.random()."""
    roll = rng.random()
    acc = 0.0
    for label, w in pairs:
        acc += w
        if roll < acc:
            return label
    return pairs[-1][0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    rng = random.Random(SEED)
    rows = []
    for i in range(N_LINES):
        channel = weighted(rng, CHANNEL_WEIGHTS)
        cat_weights = list(zip(CATEGORIES,
                               CHANNEL_CATEGORY_WEIGHTS[channel]))
        category = weighted(rng, cat_weights)
        product, price = rng.choice(PRODUCTS[category])
        month = weighted(rng, MONTH_WEIGHTS)
        day = rng.randint(1, 28)
        qty = weighted(rng, DARAZ_QTY_WEIGHTS if channel == "Daraz"
                       else QTY_WEIGHTS)
        rows.append({
            "order_id": f"ORD-{2001 + i}",
            "order_date": f"2026-{month:02d}-{day:02d}",
            "category": category,
            "product": product,
            "channel": channel,
            "city": weighted(rng, CITY_WEIGHTS),
            "payment_method": weighted(rng, PAYMENT_WEIGHTS),
            "quantity": qty,
            "unit_price": price,
            "line_total": qty * price,
        })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    grand = sum(r["line_total"] for r in rows)
    print(f"Wrote {args.out} ({len(rows)} lines, "
          f"grand total PKR {grand:,})")


if __name__ == "__main__":
    main()
