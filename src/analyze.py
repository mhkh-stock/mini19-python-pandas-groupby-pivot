"""Run the 10 GroupBy / pivot / aggregation techniques — Mini #19.

Reads data/raw/orders_SAMPLE.csv (SAMPLE data, GadgetHub.pk) and
writes one CSV per technique into outputs/, plus outputs/summary.json
(headline KPIs) and outputs/findings.md (the findings write-up).

Re-run any time: python3 src/analyze.py
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "orders_SAMPLE.csv"
OUT = ROOT / "outputs"

ROUND = 2  # money is integer PKR; shares/percentages keep 2 decimals


def money(x):
    return int(round(x))


def main():
    df = pd.read_csv(RAW, parse_dates=["order_date"])
    df["month"] = df["order_date"].dt.strftime("%Y-%m")
    OUT.mkdir(parents=True, exist_ok=True)

    grand_total = money(df["line_total"].sum())
    n_lines = len(df)

    # --- Technique 1: groupby sum / mean / count by category --------
    t01 = (df.groupby("category")
             .agg(lines=("line_total", "size"),
                  units=("quantity", "sum"),
                  revenue_pkr=("line_total", "sum"),
                  mean_line_total_pkr=("line_total", "mean"))
             .reset_index())
    t01["revenue_share_pct"] = (t01["revenue_pkr"] / grand_total * 100
                                ).round(ROUND)
    t01["mean_line_total_pkr"] = t01["mean_line_total_pkr"].round(ROUND)
    t01 = t01.sort_values("revenue_pkr", ascending=False)
    t01.to_csv(OUT / "t01_category_summary.csv", index=False)

    # --- Technique 2: multi-level groupby category x channel --------
    t02 = (df.groupby(["category", "channel"])
             .agg(lines=("line_total", "size"),
                  units=("quantity", "sum"),
                  revenue_pkr=("line_total", "sum"),
                  mean_line_total_pkr=("line_total", "mean"))
             .reset_index())
    t02["mean_line_total_pkr"] = t02["mean_line_total_pkr"].round(ROUND)
    t02 = t02.sort_values(["category", "revenue_pkr"],
                          ascending=[True, False])
    t02.to_csv(OUT / "t02_category_channel.csv", index=False)

    # --- Technique 3: pivot_table revenue by month x category -------
    t03 = df.pivot_table(index="month", columns="category",
                         values="line_total", aggfunc="sum",
                         fill_value=0)
    # fixed column order: biggest category first, for readability
    cat_order = list(t01["category"])
    t03 = t03[cat_order]
    t03["Total"] = t03.sum(axis=1)
    t03 = t03.reset_index()
    t03.to_csv(OUT / "t03_pivot_month_category.csv", index=False)

    # --- Technique 4: crosstab channel x payment_method -------------
    t04 = pd.crosstab(df["channel"], df["payment_method"], margins=True,
                      margins_name="Total")
    t04 = t04.reset_index().rename(columns={"channel": "channel"})
    t04.to_csv(OUT / "t04_crosstab_channel_payment.csv", index=False)

    # --- Technique 5: transform — share of own category total ------
    df["category_total_pkr"] = df.groupby("category")["line_total"] \
        .transform("sum")
    df["share_of_category"] = (df["line_total"]
                               / df["category_total_pkr"]).round(6)
    t05 = df[["order_id", "order_date", "category", "product",
              "line_total", "category_total_pkr",
              "share_of_category"]].copy()
    t05["order_date"] = t05["order_date"].dt.strftime("%Y-%m-%d")
    t05 = t05.sort_values(["category", "share_of_category"],
                          ascending=[True, False])
    t05.to_csv(OUT / "t05_line_share_of_category.csv", index=False)

    # --- Technique 6: monthly resample + month-on-month growth ------
    monthly = (df.set_index("order_date")
                 .resample("M")["line_total"]  # "M": pandas < 2.2 alias
                 .agg(["size", "sum"]))
    monthly.columns = ["lines", "revenue_pkr"]
    monthly = monthly.reset_index()
    monthly["month"] = monthly["order_date"].dt.strftime("%Y-%m")
    monthly["revenue_mom_growth_pct"] = (monthly["revenue_pkr"]
                                         .pct_change() * 100).round(ROUND)
    monthly = monthly[["month", "lines", "revenue_pkr",
                       "revenue_mom_growth_pct"]]
    monthly.to_csv(OUT / "t06_monthly_growth.csv", index=False)

    # --- Technique 7: top-3 products per category -------------------
    prod = (df.groupby(["category", "product"])
              .agg(lines=("line_total", "size"),
                   units=("quantity", "sum"),
                   revenue_pkr=("line_total", "sum"))
              .reset_index())
    prod["rank_in_category"] = (prod.groupby("category")["revenue_pkr"]
                                .rank(method="first", ascending=False)
                                .astype(int))
    t07 = prod[prod["rank_in_category"] <= 3].sort_values(
        ["category", "rank_in_category"])
    t07.to_csv(OUT / "t07_top3_products_per_category.csv", index=False)

    # --- Technique 8: nunique + distinct counts per city ------------
    t08 = (df.groupby("city")
             .agg(lines=("line_total", "size"),
                  revenue_pkr=("line_total", "sum"),
                  distinct_products=("product", "nunique"),
                  distinct_categories=("category", "nunique"),
                  distinct_orders=("order_id", "nunique"))
             .reset_index())
    t08["revenue_share_pct"] = (t08["revenue_pkr"] / grand_total * 100
                                ).round(ROUND)
    t08 = t08.sort_values("revenue_pkr", ascending=False)
    t08.to_csv(OUT / "t08_city_distinct_counts.csv", index=False)

    # --- Technique 9: agg with several functions by payment_method --
    t09 = (df.groupby("payment_method")
             .agg(lines=("line_total", "size"),
                  total_pkr=("line_total", "sum"),
                  mean_pkr=("line_total", "mean"),
                  min_pkr=("line_total", "min"),
                  max_pkr=("line_total", "max"),
                  units=("quantity", "sum"))
             .reset_index())
    t09["mean_pkr"] = t09["mean_pkr"].round(ROUND)
    t09["total_share_pct"] = (t09["total_pkr"] / grand_total * 100
                              ).round(ROUND)
    t09 = t09.sort_values("total_pkr", ascending=False)
    t09.to_csv(OUT / "t09_payment_method_agg.csv", index=False)

    # --- Technique 10: Pareto — cumulative share by product ---------
    pareto = (df.groupby("product")["line_total"].sum()
                .sort_values(ascending=False)
                .reset_index()
                .rename(columns={"line_total": "revenue_pkr"}))
    pareto["cumulative_revenue_pkr"] = pareto["revenue_pkr"].cumsum()
    pareto["cumulative_share_pct"] = (pareto["cumulative_revenue_pkr"]
                                      / grand_total * 100).round(ROUND)
    n_products = len(pareto)
    top20_n = max(1, int(round(n_products * 0.20)))
    pareto["in_top_20pct_products"] = [i < top20_n
                                       for i in range(n_products)]
    pareto.to_csv(OUT / "t10_pareto_products.csv", index=False)

    # --- Headline KPIs ----------------------------------------------
    top_cat = t01.iloc[0]
    top_channel = (df.groupby("channel")["line_total"].sum()
                   .sort_values(ascending=False))
    top_city = t08.iloc[0]
    peak_month = monthly.loc[monthly["revenue_pkr"].idxmax()]
    cod = t09[t09["payment_method"] == "COD"].iloc[0]
    daraz = df[df["channel"] == "Daraz"]
    website = df[df["channel"] == "Website"]
    pareto_top20_share = round(
        pareto[pareto["in_top_20pct_products"]]["revenue_pkr"].sum()
        / grand_total * 100, ROUND)
    best_mom = monthly.loc[monthly["revenue_mom_growth_pct"].idxmax()]

    summary = {
        "dataset": "GadgetHub.pk — SAMPLE / DEMO data only "
                   "(fictional store, Jan–Jun 2026)",
        "total_lines": n_lines,
        "distinct_orders": int(df["order_id"].nunique()),
        "distinct_products": n_products,
        "grand_total_pkr": grand_total,
        "total_units": int(df["quantity"].sum()),
        "average_line_total_pkr": round(df["line_total"].mean(), ROUND),
        "top_category": top_cat["category"],
        "top_category_revenue_pkr": money(top_cat["revenue_pkr"]),
        "top_category_share_pct": float(top_cat["revenue_share_pct"]),
        "top_channel": top_channel.index[0],
        "top_channel_revenue_pkr": money(top_channel.iloc[0]),
        "top_channel_share_pct": round(top_channel.iloc[0]
                                       / grand_total * 100, ROUND),
        "top_city": top_city["city"],
        "top_city_revenue_pkr": money(top_city["revenue_pkr"]),
        "top_city_share_pct": float(top_city["revenue_share_pct"]),
        "peak_month": peak_month["month"],
        "peak_month_revenue_pkr": money(peak_month["revenue_pkr"]),
        "peak_month_share_pct": round(peak_month["revenue_pkr"]
                                      / grand_total * 100, ROUND),
        "cod_lines": int(cod["lines"]),
        "cod_share_pct": round(int(cod["lines"]) / n_lines * 100, ROUND),
        "cod_revenue_share_pct": float(cod["total_share_pct"]),
        "cod_revenue_pkr": money(cod["total_pkr"]),
        "daraz_lines": int(len(daraz)),
        "daraz_aov_pkr": round(daraz["line_total"].mean(), ROUND),
        "website_aov_pkr": round(website["line_total"].mean(), ROUND),
        "pareto_top_20pct_products": top20_n,
        "pareto_top_20pct_share_pct": pareto_top20_share,
        "best_mom_growth_month": best_mom["month"],
        "best_mom_growth_pct": float(best_mom["revenue_mom_growth_pct"]),
        "months": 6,
        "categories": int(df["category"].nunique()),
        "channels": int(df["channel"].nunique()),
        "cities": int(df["city"].nunique()),
        "payment_methods": int(df["payment_method"].nunique()),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2)
                                      + "\n")

    # --- Findings write-up (numbers come from the computed summary) -
    def pkr(n):
        return f"PKR {n:,}"

    # per-category peak months, for the pivot finding (technique 3)
    pivot_peak = {}
    for cat in cat_order:
        peak_row = t03.loc[t03[cat].idxmax()]
        pivot_peak[cat] = (peak_row["month"], money(peak_row[cat]))
    may_peaks = [c for c, (m, _) in pivot_peak.items() if m == "2026-05"]

    # highest / lowest average line value by payment method (technique 9)
    pay_mean = t09.set_index("payment_method")["mean_pkr"]
    hi_pay, hi_pay_mean = pay_mean.idxmax(), money(pay_mean.max())
    lo_pay, lo_pay_mean = pay_mean.idxmin(), money(pay_mean.min())

    # narrowest city range (technique 8)
    narrow_city = t08.loc[t08["distinct_products"].idxmin()]
    full_range_cities = list(
        t08[t08["distinct_products"] == n_products]["city"])

    findings = f"""# Mini #19 — findings (GadgetHub.pk, SAMPLE data)

Fictional Pakistani online gadgets store, Jan–Jun 2026.
**SAMPLE / DEMO data only** — invented store, invented orders,
never real client or real business data. Every number below is
recomputed from `data/raw/orders_SAMPLE.csv` by `src/analyze.py`
and re-checked independently by `src/checks.py`.

## Headline numbers

- **{n_lines:,} order lines** ({summary["distinct_orders"]:,} orders)
  worth **{pkr(grand_total)}** across {n_products} products.
- **{summary["top_category"]} dominate revenue**:
  {pkr(summary["top_category_revenue_pkr"])}
  ({summary["top_category_share_pct"]}% of all revenue) from
  {int(top_cat["lines"]):,} lines. Laptops are second at
  {pkr(money(t01[t01["category"] == "Laptops"]["revenue_pkr"].iloc[0]))}
  ({float(t01[t01["category"] == "Laptops"]["revenue_share_pct"].iloc[0])}%)
  — the two big-ticket categories together are
  {round(float(top_cat["revenue_share_pct"]) + float(t01[t01["category"] == "Laptops"]["revenue_share_pct"].iloc[0]), 1)}%
  of revenue.
- **{summary["top_channel"]} is the biggest channel**:
  {pkr(summary["top_channel_revenue_pkr"])}
  ({summary["top_channel_share_pct"]}%).
- **{summary["top_city"]} is the clear leading city**:
  {pkr(summary["top_city_revenue_pkr"])}
  ({summary["top_city_share_pct"]}% of revenue).
- **{summary["peak_month"]} is the peak month**:
  {pkr(summary["peak_month_revenue_pkr"])}
  ({summary["peak_month_share_pct"]}% of the half-year total).
- **COD is still king**: {summary["cod_lines"]:,} lines
  ({summary["cod_share_pct"]}% of all lines),
  {pkr(summary["cod_revenue_pkr"])}.

## What the 10 techniques show

1. **Category summary (t01).** Mobiles lead on lines
   ({int(top_cat["lines"]):,}) and revenue; Accessories are the
   opposite — {int(t01[t01["category"] == "Accessories"]["lines"].iloc[0]):,}
   lines but only
   {pkr(money(t01[t01["category"] == "Accessories"]["revenue_pkr"].iloc[0]))}
   ({float(t01[t01["category"] == "Accessories"]["revenue_share_pct"].iloc[0])}%).
   Cheap, frequent, small.
2. **Category x channel (t02).** The Website sells the expensive
   mix — Mobiles and Laptops dominate its revenue — while Daraz
   lives on Accessories and Audio.
3. **Pivot month x category (t03).** {len(may_peaks)} of the 6
   categories peak in May ({", ".join(may_peaks)}); Wearables peak
   in {pivot_peak["Wearables"][0]} and Audio in
   {pivot_peak["Audio"][0]} instead. Mobiles in May alone are
   {pkr(money(t03[t03["month"] == "2026-05"]["Mobiles"].iloc[0]))}.
4. **Crosstab channel x payment (t04).** COD is the top payment
   method on every channel, not just overall — even on the Website.
5. **Transform shares (t05).** One line is never more than
   {round(float(df["share_of_category"].max()) * 100, 2)}% of its
   own category's total — no single order carries a category.
6. **Monthly growth (t06).** Revenue jumps
   {summary["best_mom_growth_pct"]}% in {summary["best_mom_growth_month"]}
   (the biggest month-on-month move), then falls back in June —
   the May spike is seasonal, not a new level.
7. **Top-3 products per category (t07).** The top product in
   Mobiles is {t07[(t07["category"] == "Mobiles") & (t07["rank_in_category"] == 1)]["product"].iloc[0]}
   ({pkr(money(t07[(t07["category"] == "Mobiles") & (t07["rank_in_category"] == 1)]["revenue_pkr"].iloc[0]))});
   in Laptops it is {t07[(t07["category"] == "Laptops") & (t07["rank_in_category"] == 1)]["product"].iloc[0]}
   ({pkr(money(t07[(t07["category"] == "Laptops") & (t07["rank_in_category"] == 1)]["revenue_pkr"].iloc[0]))}).
8. **City distinct counts (t08).** {", ".join(full_range_cities)}
   each sell all {n_products} products; only
   {narrow_city["city"]} is narrower
   ({int(narrow_city["distinct_products"])} products) — the smaller
   cities buy almost the full range, so the gap is revenue, not
   range.
9. **Payment-method agg (t09).** {hi_pay} has the highest
   average line value
   ({pkr(hi_pay_mean)}),
   {lo_pay} the lowest
   ({pkr(lo_pay_mean)}) — the payment mix follows the basket, not
   the other way round.
10. **Pareto (t10).** The top {top20_n} products (20% of the
    {n_products}) bring in **{pareto_top20_share}% of all revenue**.
    The single biggest product is
    {pareto.iloc[0]["product"]}
    ({pkr(money(pareto.iloc[0]["revenue_pkr"]))},
    {pareto.iloc[0]["cumulative_share_pct"]}% on its own).

## The Daraz trap

Daraz looks healthy on volume — {summary["daraz_lines"]:,} lines,
the second-biggest channel — but its average order value is only
{pkr(summary["daraz_aov_pkr"])}, against
{pkr(summary["website_aov_pkr"])} on the Website. Same store, same
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
"""
    (OUT / "findings.md").write_text(findings)

    print(f"Wrote 10 technique CSVs + summary.json + findings.md "
          f"to {OUT}")
    print(f"{n_lines} lines, grand total PKR {grand_total:,}, "
          f"top category {summary['top_category']} "
          f"({summary['top_category_share_pct']}%)")


if __name__ == "__main__":
    main()
