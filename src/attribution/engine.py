"""Explicit, deterministic attribution engine.

Eligible touch : resolved identity AND engaged type (click, email_open, event_attendance,
                 webinar_attendance, mail_response). Impressions / mail_delivered never earn credit.
Window         : [order_ts - lookback_days, order_ts]  (touches AFTER conversion are never eligible)
Reconciliation : credits are allocated in integer cents (largest remainder), so the credits of every
                 (order, model) sum exactly to the order amount. No eligible touch => one
                 'unattributed' row carrying the full amount, so revenue is never silently dropped.
"""
import bisect
from datetime import datetime, timedelta

from . import first_touch, last_touch, multi_touch

FMT = "%Y-%m-%dT%H:%M:%S"
ENGAGED = ("click", "email_open", "event_attendance", "webinar_attendance", "mail_response")
WEIGHT_FUNCS = {"first_touch": first_touch.weights, "last_touch": last_touch.weights, "linear": multi_touch.linear,
                "time_decay": multi_touch.time_decay, "position_based": multi_touch.position_based}
MODELS = [("first_touch", first_touch.DESCRIPTION), ("last_touch", last_touch.DESCRIPTION)] + \
         [(m, multi_touch.DESCRIPTIONS[m]) for m in ("linear", "time_decay", "position_based")]


def weights(model, tss, order_dt):
    return WEIGHT_FUNCS[model](tss, order_dt)


def split_cents(total, w):
    """Largest-remainder split of an integer number of cents. sum(result) == total exactly."""
    s = sum(w)
    raw = [total * x / s for x in w]
    base = [int(r) for r in raw]
    rem = total - sum(base)
    order = sorted(range(len(w)), key=lambda i: (-(raw[i] - base[i]), i))
    for i in order[:rem]:
        base[i] += 1
    return base


def run_attribution(touch_rows, order_rows, period_fn, lookback_days, post_conv_orders=frozenset(),
                    grace_days=90, id_start=1, models=None):
    """touch_rows/order_rows are dict rows (CSV-shaped). order_rows must be in the desired output order.
    post_conv_orders: orders processed with a deliberately buggy window that also admits touches
    up to `grace_days` AFTER conversion (injected edge case). Returns (rows, post_conversion_attr_ids)."""
    models = models or [m[0] for m in MODELS]
    by_contact = {}
    for t in touch_rows:
        if t["contact_id"] and t["identity_link_status"] == "resolved" and t["touch_type"] in ENGAGED:
            by_contact.setdefault(t["contact_id"], []).append(t)
    idx = {}
    for cid, lst in by_contact.items():
        lst.sort(key=lambda t: (t["touch_ts"], t["touchpoint_id"]))
        idx[cid] = ([t["touch_ts"] for t in lst], lst)

    out, flagged, n = [], [], id_start
    for o in order_rows:
        odt = datetime.strptime(o["order_ts"], FMT)
        total = round(float(o["amount"]) * 100)
        lo = (odt - timedelta(days=lookback_days)).strftime(FMT)
        hi = (odt + timedelta(days=grace_days)).strftime(FMT) if o["order_id"] in post_conv_orders else o["order_ts"]
        cand = []
        if o["contact_id"] in idx:
            tss, lst = idx[o["contact_id"]]
            cand = lst[bisect.bisect_left(tss, lo):bisect.bisect_right(tss, hi)]
        period = period_fn(o["order_ts"])
        for m in models:
            if not cand:
                out.append(dict(attribution_id="ATTR-2026-%07d" % n, order_id=o["order_id"], opportunity_id=o["opportunity_id"],
                                touchpoint_id=None, campaign_id=None, model_id=m, credit_weight=1.0,
                                attributed_revenue=total / 100, evaluation_period=period,
                                attribution_status="unattributed_no_eligible_touch"))
                n += 1
                continue
            w = weights(m, [t["touch_ts"] for t in cand], odt)
            cents = split_cents(total, w)
            for t, c in zip(cand, cents):
                if c <= 0:
                    continue
                out.append(dict(attribution_id="ATTR-2026-%07d" % n, order_id=o["order_id"], opportunity_id=o["opportunity_id"],
                                touchpoint_id=t["touchpoint_id"], campaign_id=t["campaign_id"], model_id=m,
                                credit_weight=round(c / total, 6) if total else 0.0,
                                attributed_revenue=c / 100, evaluation_period=period,
                                attribution_status="attributed"))
                if t["touch_ts"] > o["order_ts"]:
                    flagged.append(out[-1]["attribution_id"])
                n += 1
    return out, flagged


def build_evaluation_periods(orders_ts, data_start, as_of, fmt=FMT):
    """Chronological split on order timestamps: train <60th pct, validation 60-80th, test >=80th."""
    base = sorted(orders_ts)
    b1, b2 = base[int(len(base) * 0.6)].strftime(fmt), base[int(len(base) * 0.8)].strftime(fmt)
    rule = "order_ts quantiles: train <60%, validation 60-80%, test >=80%"
    rows = [dict(period_id="train", start_ts=data_start.strftime(fmt), end_ts=b1, split_rule=rule),
            dict(period_id="validation", start_ts=b1, end_ts=b2, split_rule=rule),
            dict(period_id="test", start_ts=b2, end_ts=(as_of + timedelta(seconds=1)).strftime(fmt), split_rule=rule)]
    return rows, (lambda ts: "train" if ts < b1 else ("validation" if ts < b2 else "test"))


def model_table(lookback_days):
    return [dict(model_id=m, rule_description=d, lookback_days=lookback_days, eligible_touch_types="|".join(ENGAGED)) for m, d in MODELS]
