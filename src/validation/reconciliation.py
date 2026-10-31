"""Arithmetic reconciliation: credits, revenue, spend vs budget, attribution window rules."""
from collections import defaultdict
from datetime import datetime, timedelta

from ..attribution.engine import ENGAGED, FMT
from ..models import data_dictionary as dd
from .anomaly_detection import detect


def run(ctx):
    D, check, idx, camp = ctx.D, ctx.check, ctx.idx, ctx.camp
    ords, tp, opp = idx["sales_order"], idx["touchpoint"], idx["opportunity"]
    check("order.amount = opportunity.amount", [o["order_id"] for o in D["sales_order"] if float(o["amount"]) != float(opp[(o["opportunity_id"],)]["amount"])])
    by_om = defaultdict(int)
    for a in D["attribution_result"]:
        by_om[(a["order_id"], a["model_id"])] += round(float(a["attributed_revenue"]) * 100)
    check("credits per (order,model) sum to order amount (cents)", [k for k, v in by_om.items() if v != round(float(ords[(k[0],)]["amount"]) * 100)])
    check("every order has results for every model", [o["order_id"] for o in D["sales_order"] for m in dd.ENUMS[("attribution_result", "model_id")] if (o["order_id"], m) not in by_om])
    rev_total = round(sum(float(o["amount"]) for o in D["sales_order"]) * 100)
    tot_m = defaultdict(int)
    for a in D["attribution_result"]:
        tot_m[a["model_id"]] += round(float(a["attributed_revenue"]) * 100)
    check("model totals (incl. unattributed) = total order revenue", [m for m, v in tot_m.items() if v != rev_total])
    won_amt = round(sum(float(o["amount"]) for o in D["opportunity"] if o["status"] == "won") * 100)
    dup_amt = round(sum(float(ords[(i,)]["amount"]) for i in detect(D)["revenue_counted_more_than_once"]) * 100)
    check("order revenue = won opp revenue + labelled duplicates", [] if rev_total == won_amt + dup_amt else [(rev_total, won_amt, dup_amt)])
    check("attribution touch credited belongs to order's contact", [a["attribution_id"] for a in D["attribution_result"]
          if a["touchpoint_id"] and tp[(a["touchpoint_id"],)]["contact_id"] != ords[(a["order_id"],)]["contact_id"]])
    lb = int(D["attribution_model"][0]["lookback_days"])
    check(f"attribution touch within {lb}-day lookback of conversion (past side)", [a["attribution_id"] for a in D["attribution_result"]
          if a["touchpoint_id"] and (datetime.strptime(ords[(a["order_id"],)]["order_ts"], FMT) - datetime.strptime(tp[(a["touchpoint_id"],)]["touch_ts"], FMT)) > timedelta(days=lb)])
    check("attribution only credits engaged, resolved touches", [a["attribution_id"] for a in D["attribution_result"]
          if a["touchpoint_id"] and (tp[(a["touchpoint_id"],)]["touch_type"] not in ENGAGED or tp[(a["touchpoint_id"],)]["identity_link_status"] != "resolved")])
    spend = defaultdict(float)
    for r in D["cost_record"]:
        if r["currency"] == camp[r["campaign_id"]]["currency"]:
            spend[r["campaign_id"]] += float(r["amount"])
    check("campaign spend <= 102% of budget (consistent-currency rows)", [c for c, v in spend.items() if v > 1.02 * float(camp[c]["budget"]) + 1])
