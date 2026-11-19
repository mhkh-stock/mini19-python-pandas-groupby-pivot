"""Independent checks for Mini #19 — GroupBy, Pivot & Aggregation Pack.

Recomputes EVERY headline number from data/raw/orders_SAMPLE.csv
with the standard library only (no pandas), then compares against
every output file, outputs/summary.json, outputs/findings.md and
README.md. Also verifies the generator is deterministic by re-running
it to a temp file and byte-comparing.

Run: python3 src/checks.py
Exit code 0 = all checks pass. Any failure is a build bug — fix the
build, never weaken the check.
"""

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "orders_SAMPLE.csv"
OUT = ROOT / "outputs"

EXPECTED_COLUMNS = ["order_id", "order_date", "category", "product",
                    "channel", "city", "payment_method", "quantity",
                    "unit_price", "line_total"]
EXPECTED_CATEGORIES = {"Mobiles", "Laptops", "Accessories", "Audio",
                       "Home Appliances", "Wearables"}
EXPECTED_CHANNELS = {"Website", "App", "Daraz", "WhatsApp"}
EXPECTED_CITIES = {"Lahore", "Karachi", "Islamabad", "Rawalpindi",
                   "Faisalabad"}
EXPECTED_PAYMENTS = {"COD", "JazzCash", "Easypaisa", "Card"}

PASSED = 0
FAILED = []


def check(name, ok, detail=""):
    global PASSED
    if ok:
        PASSED += 1
    else:
        FAILED.append(f"{name}: {detail}")


def close(a, b, tol=0.01):
    return abs(a - b) <= tol


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def main():
    # ---------- files exist ----------
    needed = [RAW, OUT / "summary.json", OUT / "findings.md",
              ROOT / "README.md", ROOT / "data" / "README.md",
              ROOT / "requirements.txt",
              ROOT / "src" / "generate_data.py",
              ROOT / "src" / "analyze.py",
              ROOT / "src" / "checks.py"] + [
        OUT / f"t{i:02d}_{slug}.csv" for i, slug in enumerate([
            "category_summary", "category_channel",
            "pivot_month_category", "crosstab_channel_payment",
            "line_share_of_category", "monthly_growth",
            "top3_products_per_category", "city_distinct_counts",
            "payment_method_agg", "pareto_products"], start=1)]
    for p in needed:
        check(f"exists {p.name}", p.is_file(), "missing file")

    # ---------- raw file: shape and hygiene ----------
    with open(RAW, newline="") as f:
        header = next(csv.reader(f))
    check("raw header exact", header == EXPECTED_COLUMNS,
          f"got {header}")
    rows = read_csv(RAW)
    check("raw row count 1000", len(rows) == 1000, f"got {len(rows)}")
    check("no empty cells", all(v not in ("", None) for r in rows
                                for v in r.values()))
    check("order_id unique", len({r["order_id"] for r in rows})
          == len(rows))
    check("all line_total == quantity x unit_price",
          all(int(r["line_total"]) == int(r["quantity"])
              * int(r["unit_price"]) for r in rows))
    check("all dates Jan–Jun 2026",
          all(r["order_date"].startswith("2026-0") for r in rows))
    check("categories exactly the 6 expected",
          {r["category"] for r in rows} == EXPECTED_CATEGORIES)
    check("channels exactly the 4 expected",
          {r["channel"] for r in rows} == EXPECTED_CHANNELS)
    check("cities exactly the 5 expected",
          {r["city"] for r in rows} == EXPECTED_CITIES)
    check("payments exactly the 4 expected",
          {r["payment_method"] for r in rows} == EXPECTED_PAYMENTS)
    # one fixed price per product (the generator's price list)
    price_sets = defaultdict(set)
    for r in rows:
        price_sets[r["product"]].add(int(r["unit_price"]))
    for product in sorted(price_sets):
        check(f"single price for {product}",
              len(price_sets[product]) == 1,
              f"{price_sets[product]}")

    # ---------- independent aggregates from the raw file ----------
    def rev(key):
        totals = defaultdict(int)
        for r in rows:
            totals[key(r)] += int(r["line_total"])
        return totals

    grand = sum(int(r["line_total"]) for r in rows)
    by_cat = rev(lambda r: r["category"])
    by_channel = rev(lambda r: r["channel"])
    by_city = rev(lambda r: r["city"])
    by_payment = rev(lambda r: r["payment_method"])
    by_month = rev(lambda r: r["order_date"][:7])
    by_cat_channel = rev(lambda r: (r["category"], r["channel"]))
    by_product = rev(lambda r: r["product"])
    by_cat_product = rev(lambda r: (r["category"], r["product"]))

    def lines(key):
        counts = defaultdict(int)
        for r in rows:
            counts[key(r)] += 1
        return counts

    lines_cat = lines(lambda r: r["category"])
    lines_channel = lines(lambda r: r["channel"])
    lines_payment = lines(lambda r: r["payment_method"])
    lines_month = lines(lambda r: r["order_date"][:7])
    units_cat = defaultdict(int)
    for r in rows:
        units_cat[r["category"]] += int(r["quantity"])

    summary = json.loads((OUT / "summary.json").read_text())

    # ---------- summary.json headlines ----------
    check("summary total_lines", summary["total_lines"] == 1000)
    check("summary grand_total", summary["grand_total_pkr"] == grand,
          f"{summary['grand_total_pkr']} vs {grand}")
    top_cat = max(by_cat, key=by_cat.get)
    check("summary top_category", summary["top_category"] == top_cat)
    check("summary top_category revenue",
          summary["top_category_revenue_pkr"] == by_cat[top_cat])
    check("summary top_category share",
          close(summary["top_category_share_pct"],
                by_cat[top_cat] / grand * 100))
    top_channel = max(by_channel, key=by_channel.get)
    check("summary top_channel", summary["top_channel"] == top_channel)
    check("summary top_channel revenue",
          summary["top_channel_revenue_pkr"] == by_channel[top_channel])
    top_city = max(by_city, key=by_city.get)
    check("summary top_city", summary["top_city"] == top_city)
    check("summary top_city revenue",
          summary["top_city_revenue_pkr"] == by_city[top_city])
    peak_month = max(by_month, key=by_month.get)
    check("summary peak_month", summary["peak_month"] == peak_month)
    check("summary peak_month revenue",
          summary["peak_month_revenue_pkr"] == by_month[peak_month])
    check("summary cod_lines",
          summary["cod_lines"] == lines_payment["COD"])
    check("summary cod_share_pct",
          close(summary["cod_share_pct"],
                lines_payment["COD"] / len(rows) * 100))
    check("summary cod_revenue",
          summary["cod_revenue_pkr"] == by_payment["COD"])
    daraz_rows = [r for r in rows if r["channel"] == "Daraz"]
    web_rows = [r for r in rows if r["channel"] == "Website"]
    check("summary daraz_lines",
          summary["daraz_lines"] == len(daraz_rows))
    check("summary daraz_aov",
          close(summary["daraz_aov_pkr"],
                sum(int(r["line_total"]) for r in daraz_rows)
                / len(daraz_rows)))
    check("summary website_aov",
          close(summary["website_aov_pkr"],
                sum(int(r["line_total"]) for r in web_rows)
                / len(web_rows)))
    sorted_products = sorted(by_product.items(), key=lambda kv: -kv[1])
    top4_share = (sum(v for _, v in sorted_products[:4]) / grand * 100)
    check("summary pareto top-20% share",
          close(summary["pareto_top_20pct_share_pct"], top4_share),
          f"{summary['pareto_top_20pct_share_pct']} vs {top4_share:.2f}")
    check("summary total_units",
          summary["total_units"]
          == sum(int(r["quantity"]) for r in rows))
    check("summary distinct_products",
          summary["distinct_products"] == len(by_product))

    # ---------- t01: category summary ----------
    t01 = read_csv(OUT / "t01_category_summary.csv")
    check("t01 row count 6", len(t01) == 6)
    check("t01 revenue sums to grand",
          sum(int(r["revenue_pkr"]) for r in t01) == grand)
    for r in t01:
        cat = r["category"]
        check(f"t01 {cat} revenue", int(r["revenue_pkr"]) == by_cat[cat])
        check(f"t01 {cat} lines", int(r["lines"]) == lines_cat[cat])
        check(f"t01 {cat} units", int(r["units"]) == units_cat[cat])
        check(f"t01 {cat} share",
              close(float(r["revenue_share_pct"]),
                    by_cat[cat] / grand * 100))
        check(f"t01 {cat} mean",
              close(float(r["mean_line_total_pkr"]),
                    by_cat[cat] / lines_cat[cat]))

    # ---------- t02: category x channel ----------
    t02 = read_csv(OUT / "t02_category_channel.csv")
    check("t02 row count 24", len(t02) == 6 * 4, f"got {len(t02)}")
    check("t02 revenue sums to grand",
          sum(int(r["revenue_pkr"]) for r in t02) == grand)
    for r in t02:
        key = (r["category"], r["channel"])
        check(f"t02 {key} revenue",
              int(r["revenue_pkr"]) == by_cat_channel[key],
              f"{r['revenue_pkr']} vs {by_cat_channel[key]}")

    # ---------- t03: pivot month x category ----------
    t03 = read_csv(OUT / "t03_pivot_month_category.csv")
    check("t03 row count 6", len(t03) == 6)
    # proper cell check: pivot cell = revenue for that month+category
    month_cat = rev(lambda r: (r["order_date"][:7], r["category"]))
    for r in t03:
        check(f"t03 {r['month']} row total",
              int(r["Total"]) == by_month[r["month"]])
    for r in t03:
        for cat in EXPECTED_CATEGORIES:
            check(f"t03 cell {r['month']} x {cat}",
                  int(r[cat]) == month_cat[(r["month"], cat)])
    for cat in EXPECTED_CATEGORIES:
        check(f"t03 column {cat} sums to category total",
              sum(int(r[cat]) for r in t03) == by_cat[cat])

    # ---------- t04: crosstab channel x payment ----------
    t04 = read_csv(OUT / "t04_crosstab_channel_payment.csv")
    check("t04 row count 5 (4 channels + Total)", len(t04) == 5)
    ct = defaultdict(int)
    for r in rows:
        ct[(r["channel"], r["payment_method"])] += 1
    for r in t04:
        ch = r["channel"]
        if ch == "Total":
            check("t04 grand total", int(r["Total"]) == 1000)
            for pay in EXPECTED_PAYMENTS:
                check(f"t04 Total x {pay}",
                      int(r[pay]) == lines_payment[pay])
        else:
            check(f"t04 {ch} row total",
                  int(r["Total"]) == lines_channel[ch])
            for pay in EXPECTED_PAYMENTS:
                check(f"t04 {ch} x {pay}",
                      int(r[pay]) == ct[(ch, pay)])

    # ---------- t05: transform shares ----------
    t05 = read_csv(OUT / "t05_line_share_of_category.csv")
    check("t05 row count 1000", len(t05) == 1000)
    max_err = 0.0
    for r in t05:
        expect = int(r["line_total"]) / int(r["category_total_pkr"])
        max_err = max(max_err, abs(float(r["share_of_category"])
                                  - expect))
    check("t05 shares match line/category total", max_err < 1e-5,
          f"max err {max_err}")
    for cat in EXPECTED_CATEGORIES:
        s = sum(float(r["share_of_category"]) for r in t05
                if r["category"] == cat)
        check(f"t05 shares sum to 1.0 for {cat}", close(s, 1.0, 1e-4),
              f"sum {s}")
        check(f"t05 {cat} category_total",
              int(next(r["category_total_pkr"] for r in t05
                       if r["category"] == cat)) == by_cat[cat])

    # ---------- t06: monthly growth ----------
    t06 = read_csv(OUT / "t06_monthly_growth.csv")
    check("t06 row count 6", len(t06) == 6)
    check("t06 revenue sums to grand",
          sum(int(r["revenue_pkr"]) for r in t06) == grand)
    prev = None
    for r in t06:
        m = r["month"]
        check(f"t06 {m} revenue", int(r["revenue_pkr"]) == by_month[m])
        check(f"t06 {m} lines", int(r["lines"]) == lines_month[m])
        if prev is None:
            check(f"t06 {m} growth blank", r["revenue_mom_growth_pct"]
                  in ("", "nan"))
        else:
            expect = (by_month[m] - prev) / prev * 100
            check(f"t06 {m} MoM growth",
                  close(float(r["revenue_mom_growth_pct"]), expect),
                  f"{r['revenue_mom_growth_pct']} vs {expect:.2f}")
        prev = by_month[m]

    # ---------- t07: top-3 products per category ----------
    t07 = read_csv(OUT / "t07_top3_products_per_category.csv")
    check("t07 row count 18", len(t07) == 18, f"got {len(t07)}")
    for cat in EXPECTED_CATEGORIES:
        expect = sorted(
            ((p, v) for (c, p), v in by_cat_product.items() if c == cat),
            key=lambda kv: -kv[1])[:3]
        got = [(r["product"], int(r["revenue_pkr"])) for r in t07
               if r["category"] == cat]
        got_sorted = sorted(got, key=lambda kv: -kv[1])
        check(f"t07 top-3 for {cat}", got_sorted == expect,
              f"{got_sorted} vs {expect}")
        ranks = [int(r["rank_in_category"]) for r in t07
                 if r["category"] == cat]
        check(f"t07 ranks 1-3 for {cat}", sorted(ranks) == [1, 2, 3])

    # ---------- t08: city distinct counts ----------
    t08 = read_csv(OUT / "t08_city_distinct_counts.csv")
    check("t08 row count 5", len(t08) == 5)
    for r in t08:
        city = r["city"]
        city_rows = [x for x in rows if x["city"] == city]
        check(f"t08 {city} lines", int(r["lines"]) == len(city_rows))
        check(f"t08 {city} revenue",
              int(r["revenue_pkr"]) == by_city[city])
        check(f"t08 {city} distinct products",
              int(r["distinct_products"])
              == len({x["product"] for x in city_rows}))
        check(f"t08 {city} distinct categories",
              int(r["distinct_categories"])
              == len({x["category"] for x in city_rows}))
        check(f"t08 {city} distinct orders",
              int(r["distinct_orders"])
              == len({x["order_id"] for x in city_rows}))

    # ---------- t09: payment-method agg ----------
    t09 = read_csv(OUT / "t09_payment_method_agg.csv")
    check("t09 row count 4", len(t09) == 4)
    check("t09 totals sum to grand",
          sum(int(r["total_pkr"]) for r in t09) == grand)
    for r in t09:
        pay = r["payment_method"]
        vals = [int(x["line_total"]) for x in rows
                if x["payment_method"] == pay]
        check(f"t09 {pay} total", int(r["total_pkr"]) == sum(vals))
        check(f"t09 {pay} mean",
              close(float(r["mean_pkr"]), sum(vals) / len(vals)))
        check(f"t09 {pay} min", int(r["min_pkr"]) == min(vals))
        check(f"t09 {pay} max", int(r["max_pkr"]) == max(vals))
        check(f"t09 {pay} lines", int(r["lines"]) == len(vals))
        check(f"t09 {pay} units",
              int(r["units"]) == sum(int(x["quantity"]) for x in rows
                                     if x["payment_method"] == pay))

    # ---------- t10: Pareto ----------
    t10 = read_csv(OUT / "t10_pareto_products.csv")
    check("t10 row count 20", len(t10) == 20)
    check("t10 final cumulative == grand",
          int(t10[-1]["cumulative_revenue_pkr"]) == grand)
    check("t10 final cumulative share 100.0",
          close(float(t10[-1]["cumulative_share_pct"]), 100.0))
    revs = [int(r["revenue_pkr"]) for r in t10]
    check("t10 sorted descending", revs == sorted(revs, reverse=True))
    check("t10 top-4 share",
          close(float(t10[3]["cumulative_share_pct"]), top4_share))
    cum = 0
    for r in t10:
        cum += int(r["revenue_pkr"])
        check(f"t10 cumulative for {r['product']}",
              int(r["cumulative_revenue_pkr"]) == cum)
    check("t10 top-20% flag count 4",
          sum(r["in_top_20pct_products"] == "True" for r in t10) == 4)

    # ---------- findings.md + README.md carry the real numbers ------
    findings = (OUT / "findings.md").read_text()
    readme = (ROOT / "README.md").read_text()
    for label, text in [("findings", findings), ("README", readme)]:
        check(f"{label} has grand total",
              f"{grand:,}" in text)
        check(f"{label} has top category", top_cat in text)
        check(f"{label} has top city", top_city in text)
        check(f"{label} has peak month", peak_month in text)
        check(f"{label} has pareto share",
              f"{top4_share:.2f}" in text or
              f"{round(top4_share, 1)}" in text)
        check(f"{label} has SAMPLE banner", "SAMPLE" in text)

    # ---------- generator determinism ----------
    with tempfile.TemporaryDirectory() as td:
        regen = Path(td) / "orders_SAMPLE.csv"
        proc = subprocess.run(
            [sys.executable, str(ROOT / "src" / "generate_data.py"),
             "--out", str(regen)],
            capture_output=True, text=True)
        check("generator re-runs cleanly", proc.returncode == 0,
              proc.stderr[-300:])
        if proc.returncode == 0:
            h1 = hashlib.sha256(RAW.read_bytes()).hexdigest()
            h2 = hashlib.sha256(regen.read_bytes()).hexdigest()
            check("generator deterministic (byte-identical)", h1 == h2)

    print(f"{PASSED} checks passed, {len(FAILED)} failed")
    if FAILED:
        print("FAILURES:")
        for f in FAILED:
            print(" -", f)
        sys.exit(1)


if __name__ == "__main__":
    main()
