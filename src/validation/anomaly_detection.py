"""Rule-based detectors that find the labelled edge cases from INPUT data only, then compare to ground truth."""
import json, os
from collections import defaultdict

from ..models import data_dictionary as dd


def detect(D):
    """Return {issue_type: set(entity_id)} found purely from input data (no ground truth used)."""
    found = defaultdict(set)
    opp_orders = defaultdict(list)
    for o in D["sales_order"]:
        opp_orders[o["opportunity_id"]].append(o)
    for lst in opp_orders.values():
        if len(lst) > 1:
            lst.sort(key=lambda o: (o["order_ts"], o["order_id"]))
            for o in lst[1:]:
                found["revenue_counted_more_than_once"].add(o["order_id"])
    ccur = {c["campaign_id"]: c["currency"] for c in D["campaign"]}
    for r in D["cost_record"]:
        if r["currency"] != ccur.get(r["campaign_id"]):
            found["spend_currency_mismatch"].add(r["cost_id"])
    has_cost = {r["campaign_id"] for r in D["cost_record"]}
    for c in D["campaign"]:
        if c["status"] == "completed" and float(c["budget"]) > 0 and c["campaign_id"] not in has_cost:
            found["campaign_costs_omitted"].add(c["campaign_id"])
    for s in D["web_session"]:
        if s["contact_id"] and s["identity_link_evidence"] == "none":
            found["anonymous_session_linked_without_evidence"].add(s["session_id"])
    for t in D["touchpoint"]:
        if t["identity_link_status"] == "missing":
            found["missing_identifier"].add(t["touchpoint_id"])
    tts = {t["touchpoint_id"]: t["touch_ts"] for t in D["touchpoint"]}
    ots = {o["order_id"]: o["order_ts"] for o in D["sales_order"]}
    for a in D["attribution_result"]:
        if a["touchpoint_id"] and tts.get(a["touchpoint_id"], "") > ots.get(a["order_id"], "9"):
            found["touchpoint_after_conversion_attributed"].add(a["attribution_id"])
    return found


def run(ctx, out):
    """Detectors vs ground truth (the oracle) + leak check. Returns the detector table for the summary."""
    found = detect(ctx.D)
    gt = json.load(open(os.path.join(out, "data", "ground_truth", "ground_truth.json")))
    gt_by = defaultdict(set)
    for r in gt:
        gt_by[r["issue_type"]].add(r["entity_id"])
    det = []
    for it in sorted(set(found) | set(gt_by)):
        tp_, fp, fn = len(found[it] & gt_by[it]), len(found[it] - gt_by[it]), len(gt_by[it] - found[it])
        det.append(dict(issue_type=it, labelled=len(gt_by[it]), detected=len(found[it]), true_pos=tp_, false_pos=fp, false_neg=fn,
                        precision=round(tp_ / len(found[it]), 4) if found[it] else None,
                        recall=round(tp_ / len(gt_by[it]), 4) if gt_by[it] else None))
        ctx.check(f"detector == ground truth: {it}", sorted((found[it] ^ gt_by[it]))[:5], kind="detector")
    leak = [(t, c) for t in ctx.D for c in dd.columns(t) if any(w in c for w in ("issue_type", "ground_truth", "latent_quality", "is_anomaly"))]
    ctx.check("no ground-truth columns in input tables", leak)
    return det
