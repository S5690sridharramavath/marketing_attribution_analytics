"""ROI = (attributed revenue - cost) / cost, USD.

Two variants make the cost of the edge cases visible:
  raw   : exactly what the pipeline emitted (duplicate orders, post-conversion credit, stated currencies)
  clean : exceptions resolved by documented decisions (duplicates dropped, strict window re-run, campaign currency)
Campaigns with no cost rows get roi = NULL and cost_status = no_cost_data."""
from collections import defaultdict

from ..attribution.engine import MODELS, run_attribution
from ..validation.anomaly_detection import detect

MODEL_IDS = [m[0] for m in MODELS]
PERIODS = ["train", "validation", "test", "all"]


def compute(D, lookback_days):
    found = detect(D)
    camp = {c["campaign_id"]: c for c in D["campaign"]}
    chan = {c["channel_id"]: c["channel_name"] for c in D["channel"]}
    fx = {(r["currency"], r["rate_month"]): float(r["rate_to_usd"]) for r in D["fx_rate"]}
    per = sorted(D["evaluation_period"], key=lambda p: p["start_ts"])
    b1, b2 = per[1]["start_ts"], per[2]["start_ts"]
    period_fn = lambda ts: "train" if ts < b1 else ("validation" if ts < b2 else "test")

    cost, has_cost, mism_camp = defaultdict(float), set(), set()
    mism = found["spend_currency_mismatch"]
    for r in D["cost_record"]:
        has_cost.add(r["campaign_id"])
        p = period_fn(r["cost_date"] + "T00:00:00")
        month, amt = r["cost_date"][:7], float(r["amount"])
        raw = amt * fx[(r["currency"], month)]
        clean = amt * fx[(camp[r["campaign_id"]]["currency"], month)]
        for per_ in (p, "all"):
            cost[(r["campaign_id"], per_, "raw")] += raw
            cost[(r["campaign_id"], per_, "clean")] += clean
        if r["cost_id"] in mism:
            mism_camp.add(r["campaign_id"])

    rev, unattr, total_rev = defaultdict(float), defaultdict(float), defaultdict(float)

    def add(rows, variant):
        for a in rows:
            amt = float(a["attributed_revenue"])
            for p in (a["evaluation_period"], "all"):
                total_rev[(a["model_id"], p, variant)] += amt
                if a["campaign_id"]:
                    rev[(a["campaign_id"], a["model_id"], p, variant)] += amt
                else:
                    unattr[(a["model_id"], p, variant)] += amt
    add(D["attribution_result"], "raw")
    dups = found["revenue_counted_more_than_once"]
    clean_orders = [o for o in D["sales_order"] if o["order_id"] not in dups]
    clean_rows, _ = run_attribution(D["touchpoint"], clean_orders, period_fn, lookback_days)
    add(clean_rows, "clean")

    rows = []
    for c in D["campaign"]:
        cid = c["campaign_id"]
        for m in MODEL_IDS:
            for var in ("raw", "clean"):
                for p in PERIODS:
                    r_, k_ = rev.get((cid, m, p, var), 0.0), cost.get((cid, p, var), 0.0)
                    if cid not in has_cost:
                        status, roi = "no_cost_data", None
                    elif k_ <= 0:
                        status, roi = "no_cost_in_period", None
                    else:
                        status = "currency_mismatch_rows" if (var == "raw" and cid in mism_camp) else "ok"
                        roi = round((r_ - k_) / k_, 4)
                    rows.append(dict(campaign_id=cid, channel_name=chan[c["channel_id"]], model_id=m, variant=var, period=p,
                                     attributed_revenue_usd=round(r_, 2), cost_usd=round(k_, 2), roi=roi, cost_status=status))
    ch = defaultdict(lambda: [0.0, 0.0])
    for r in rows:   # only campaigns with cost data, so channel ROI is not inflated by missing costs
        if r["cost_status"] in ("ok", "currency_mismatch_rows"):
            k = (r["channel_name"], r["model_id"], r["variant"], r["period"])
            ch[k][0] += r["attributed_revenue_usd"]
            ch[k][1] += r["cost_usd"]
    ch_rows = [dict(channel_name=k[0], model_id=k[1], variant=k[2], period=k[3], attributed_revenue_usd=round(v[0], 2),
                    cost_usd=round(v[1], 2), roi=round((v[0] - v[1]) / v[1], 4) if v[1] > 0 else None) for k, v in sorted(ch.items())]
    return dict(found=found, camp=camp, rows=rows, ch_rows=ch_rows, cost=cost, has_cost=has_cost, rev=rev, unattr=unattr, total_rev=total_rev)
