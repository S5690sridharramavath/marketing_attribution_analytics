"""Step 5 of the brief: inject labelled edge cases AFTER the valid baseline exists.

Every injection appends a row to S.truth (-> data/ground_truth/). Input tables carry no label columns.
"""
from datetime import datetime, timedelta

from ..attribution.engine import ENGAGED
from ..config import AS_OF
from ..models.data_dictionary import CURRENCIES
from .constants import FMT, iso


def inject_duplicate_orders(S):
    """Revenue counted more than once: billing replays an order 1-3 days later."""
    cfg, rng, orders, truth = S.cfg, S.rng, S.orders, S.truth
    dup_pool = sorted((x for x in orders if x["ts"] <= AS_OF - timedelta(days=4)), key=lambda x: x["opp"]["id"])
    for x in rng.sample(dup_pool, min(cfg.n_dup_orders, len(dup_pool))):
        orders.append(dict(opp=x["opp"], ts=x["ts"] + timedelta(days=rng.randint(1, 3)), amount=x["amount"],
                           src="billing", dup_of=x))


def label_duplicate_orders(S):
    for x in S.orders:
        if x["dup_of"]:
            S.truth.append(dict(issue_type="revenue_counted_more_than_once", category="injected_edge_case", entity="sales_order",
                                entity_id=x["id"], related_entity_id=x["dup_of"]["id"],
                                description=f"Second order for {x['opp']['id']} replayed by billing; revenue {x['amount']:.2f} USD double counted",
                                expected_decision="Keep the earliest order per won opportunity; exclude the duplicate from ROI"))


def choose_omitted_cost_campaigns(S):
    """Campaign costs omitted: completed campaigns keep their budget but get zero cost rows."""
    completed = sorted(i for i, c in enumerate(S.T["campaign"]) if c["status"] == "completed")
    return set(S.rng.sample(completed, min(S.cfg.n_cost_omitted, len(completed))))


def label_omitted_costs(S, omitted):
    for ci in sorted(omitted):
        S.truth.append(dict(issue_type="campaign_costs_omitted", category="injected_edge_case", entity="campaign",
                            entity_id=S.T["campaign"][ci]["campaign_id"], related_entity_id=None,
                            description="Completed campaign with a budget but zero cost records",
                            expected_decision="ROI is undefined (not infinite); flag cost_status=no_cost_data"))


def inject_currency_mismatch(S):
    """Spend currency mismatch: record currency differs from the campaign currency; amount unchanged."""
    T, rng = S.T, S.rng
    for i in sorted(rng.sample(range(len(T["cost_record"])), min(S.cfg.n_cost_mismatch, len(T["cost_record"])))):
        r = T["cost_record"][i]
        true_cur = r["currency"]
        r["currency"] = rng.choice([x for x in CURRENCIES if x != true_cur])
        S.truth.append(dict(issue_type="spend_currency_mismatch", category="injected_edge_case", entity="cost_record",
                            entity_id=r["cost_id"], related_entity_id=r["campaign_id"],
                            description=f"Record states {r['currency']} but campaign currency (and true amount currency) is {true_cur}",
                            expected_decision="Convert using the campaign currency, not the stated one; flag for finance review"))


def inject_anonymous_links(S):
    """Anonymous session linked to a contact WITHOUT evidence (evidence stays 'none')."""
    rng, contacts, touches, N = S.rng, S.contacts, S.touches, S.N
    anon_sess = [s for s in S.sess if s["cont"] is None]
    for s in rng.sample(anon_sess, min(S.cfg.n_anon_linked, len(anon_sess))):
        true_c = touches[s["ti"]]["c"]
        wrong = rng.randrange(N)
        while wrong == true_c:
            wrong = rng.randrange(N)
        s["cont"] = wrong
        S.truth.append(dict(issue_type="anonymous_session_linked_without_evidence", category="injected_edge_case",
                            entity="web_session", entity_id=s["id"], related_entity_id=contacts[wrong]["id"],
                            description="Session has contact_id but identity_link_evidence=none (no login, form or email click id)",
                            expected_decision="Reject the link; keep session anonymous and exclude from attribution"))


def choose_post_conversion_orders(S):
    """Touchpoint after conversion attributed: pick orders (with a post-order engaged touch) to run through a buggy window."""
    T, rng, cfg = S.T, S.rng, S.cfg
    by_contact = {}
    for t in T["touchpoint"]:
        if t["contact_id"] and t["identity_link_status"] == "resolved" and t["touch_type"] in ENGAGED:
            by_contact.setdefault(t["contact_id"], []).append(t["touch_ts"])
    grace = cfg.post_conv_grace_days
    pool = []
    for o in T["sales_order"]:
        if o["source_system"] != "crm":
            continue
        lim = iso(datetime.strptime(o["order_ts"], FMT) + timedelta(days=grace))
        if any(o["order_ts"] < ts <= lim for ts in by_contact.get(o["contact_id"], [])):
            pool.append(o["order_id"])
    return set(rng.sample(pool, min(cfg.n_post_conv, len(pool))))


def label_post_conversion(S, post_ids):
    ar = {r["attribution_id"]: r for r in S.T["attribution_result"]}
    for aid in post_ids:
        r = ar[aid]
        S.truth.append(dict(issue_type="touchpoint_after_conversion_attributed", category="injected_edge_case",
                            entity="attribution_result", entity_id=aid, related_entity_id=r["touchpoint_id"],
                            description=f"{r['model_id']} credit given to a touch that occurred after order {r['order_id']}",
                            expected_decision="Reject: only touches at or before conversion may earn credit; re-run without the touch"))
