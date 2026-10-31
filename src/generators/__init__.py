"""Generation pipeline. The ORDER of calls is the order of random-number consumption: do not reorder casually,
or the fixed-seed output changes (tests/test_reproducibility.py would still pass; the committed manifest would not)."""
import random
from types import SimpleNamespace

from ..attribution.engine import build_evaluation_periods, model_table, run_attribution
from ..config import AS_OF, DATA_START
from . import anomaly_generator as anomalies
from . import master_data, transaction_data as tx


def generate(cfg):
    S = SimpleNamespace(cfg=cfg, rng=random.Random(cfg.seed), T={}, truth=[])

    master_data.build_master_data(S)                       # channel, audience, campaign(+bridge,+history), creative, contact seeds
    tx.build_journeys(S)                                   # touchpoints + web sessions
    tx.build_leads(S)                                      # lead score-threshold rule
    tx.build_opportunities(S)                              # qualification rank + win rule
    tx.build_lifecycle_events(S)                           # append-only lead / opportunity history
    tx.build_base_orders(S)
    anomalies.inject_duplicate_orders(S)                   # edge case 1
    tx.finalize_orders(S)
    anomalies.label_duplicate_orders(S)
    omitted = anomalies.choose_omitted_cost_campaigns(S)   # edge case 2
    tx.build_costs(S, omitted)
    anomalies.label_omitted_costs(S, omitted)
    anomalies.inject_currency_mismatch(S)                  # edge case 3
    tx.build_contact_rows(S)
    anomalies.inject_anonymous_links(S)                    # edge case 4
    tx.build_session_touch_rows(S)
    tx.build_lead_opportunity_rows(S)
    tx.build_fx_rates(S)

    T = S.T
    T["evaluation_period"], period_fn = build_evaluation_periods([x["ts"] for x in S.orders if x["dup_of"] is None], DATA_START, AS_OF)
    T["attribution_model"] = model_table(S.cfg.lookback_days)
    bug_orders = anomalies.choose_post_conversion_orders(S)   # edge case 5
    T["attribution_result"], post_ids = run_attribution(T["touchpoint"], T["sales_order"], period_fn, S.cfg.lookback_days,
                                                        post_conv_orders=bug_orders, grace_days=S.cfg.post_conv_grace_days)
    anomalies.label_post_conversion(S, post_ids)

    order = {"revenue_counted_more_than_once": 0, "campaign_costs_omitted": 1, "spend_currency_mismatch": 2,
             "anonymous_session_linked_without_evidence": 3, "touchpoint_after_conversion_attributed": 4, "missing_identifier": 5}
    truth = sorted(S.truth, key=lambda r: (order[r["issue_type"]], r["entity_id"]))
    for i, r in enumerate(truth):
        r["gt_id"] = "GT-%06d" % (i + 1)
    quality = [dict(campaign_id=T["campaign"][i]["campaign_id"], latent_quality=round(c["q"], 4)) for i, c in enumerate(S.camps)]
    return T, truth, quality
