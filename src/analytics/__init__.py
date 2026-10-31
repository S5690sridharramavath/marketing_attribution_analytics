import json, os

from ..common import read_csv, write_csv
from ..export.exporter import load_tables
from . import metrics, roi

DECISIONS = {"revenue_counted_more_than_once": "excluded from clean variant (earliest order per opportunity kept)",
             "touchpoint_after_conversion_attributed": "clean variant re-runs attribution with strict touch_ts <= order_ts",
             "spend_currency_mismatch": "clean variant converts with the campaign currency",
             "campaign_costs_omitted": "roi=NULL, cost_status=no_cost_data (not zero cost, not infinite ROI)",
             "anonymous_session_linked_without_evidence": "link ignored: attribution uses touchpoint.contact_id only, never session.contact_id",
             "missing_identifier": "touch excluded from attribution; revenue lands in the unattributed bucket when no other touch exists"}


def build_reports(out):
    D = load_tables(out)
    lookback = int(D["attribution_model"][0]["lookback_days"])
    R = roi.compute(D, lookback)
    rep = os.path.join(out, "reports")
    os.makedirs(rep, exist_ok=True)
    write_csv(os.path.join(rep, "attribution_report.csv"), R["rows"],
              ["campaign_id", "channel_name", "model_id", "variant", "period", "attributed_revenue_usd", "cost_usd", "roi", "cost_status"])
    write_csv(os.path.join(rep, "channel_roi.csv"), R["ch_rows"],
              ["channel_name", "model_id", "variant", "period", "attributed_revenue_usd", "cost_usd", "roi"])
    q = {r["campaign_id"]: float(r["latent_quality"]) for r in read_csv(os.path.join(out, "data", "ground_truth", "ground_truth_campaign_quality.csv"))}
    summ = metrics.model_comparison(roi.MODEL_IDS, R["camp"], R["has_cost"], R["cost"], R["rev"], R["unattr"], R["total_rev"],
                                    R["ch_rows"], metrics.engaged_touch_counts(D["touchpoint"]), q)
    write_csv(os.path.join(rep, "model_comparison.csv"), summ, list(summ[0].keys()))
    with open(os.path.join(rep, "model_comparison.json"), "w") as fh:
        json.dump(summ, fh, indent=1)
    ex = [dict(issue_type=it, entity_id=e, decision_applied=DECISIONS[it]) for it in sorted(R["found"]) for e in sorted(R["found"][it])]
    write_csv(os.path.join(rep, "exceptions.csv"), ex, ["issue_type", "entity_id", "decision_applied"])
    return summ
