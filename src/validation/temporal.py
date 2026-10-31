"""Date ordering, temporal windows, lifecycle transitions, chronological evaluation split."""
from collections import defaultdict

from ..models import data_dictionary as dd


def run(ctx):
    D, check, idx, camp, cre, chan, asof = ctx.D, ctx.check, ctx.idx, ctx.camp, ctx.cre, ctx.chan, ctx.asof
    check("campaign start <= end", [c["campaign_id"] for c in D["campaign"] if c["start_date"] > c["end_date"]])
    check("touch within campaign dates", [t["touchpoint_id"] for t in D["touchpoint"]
          if not (camp[t["campaign_id"]]["start_date"] <= t["touch_ts"][:10] <= camp[t["campaign_id"]]["end_date"])])
    check("touch channel = campaign channel", [t["touchpoint_id"] for t in D["touchpoint"] if t["channel_id"] != camp[t["campaign_id"]]["channel_id"]])
    check("touch creative belongs to campaign", [t["touchpoint_id"] for t in D["touchpoint"] if cre[t["creative_id"]]["campaign_id"] != t["campaign_id"]])
    check("touch is_offline = channel.is_offline", [t["touchpoint_id"] for t in D["touchpoint"] if str(chan[t["channel_id"]]["is_offline"]) != t["is_offline"]])
    check("offline touches have no session", [t["touchpoint_id"] for t in D["touchpoint"] if t["is_offline"] == "1" and t["session_id"]])
    check("missing <=> contact_id NULL", [t["touchpoint_id"] for t in D["touchpoint"] if (t["identity_link_status"] == "missing") != (t["contact_id"] is None)])
    check("touch_ts <= as-of", [t["touchpoint_id"] for t in D["touchpoint"] if t["touch_ts"] > asof])
    sess, tp, lead, opp = idx["web_session"], idx["touchpoint"], idx["lead"], idx["opportunity"]
    check("session.started_at = touch_ts", [t["touchpoint_id"] for t in D["touchpoint"] if t["session_id"] and sess[(t["session_id"],)]["started_at"] != t["touch_ts"]])
    check("touchpoint contact counter ids", [t["touchpoint_id"] for t in D["touchpoint"] if t["contact_id"] and not t["touchpoint_id"].startswith(f"TOUCH-{t['contact_id']}-")])
    first_touch = {}
    for t in D["touchpoint"]:
        if t["contact_id"] and (t["contact_id"] not in first_touch or t["touch_ts"] < first_touch[t["contact_id"]]):
            first_touch[t["contact_id"]] = t["touch_ts"]
    check("contact.created_at = first resolved touch", [c["contact_id"] for c in D["contact"] if c["created_at"] != first_touch.get(c["contact_id"])])
    check("lead.created_at > creating touch", [l["lead_id"] for l in D["lead"] if l["created_at"] <= tp[(l["creating_touchpoint_id"],)]["touch_ts"]])
    check("lead.contact = creating touch contact", [l["lead_id"] for l in D["lead"] if tp[(l["creating_touchpoint_id"],)]["contact_id"] != l["contact_id"]])
    check("opportunity.created_at >= lead.created_at", [o["opportunity_id"] for o in D["opportunity"] if o["created_at"] < lead[(o["lead_id"],)]["created_at"]])
    check("opportunity.contact = lead.contact", [o["opportunity_id"] for o in D["opportunity"] if o["contact_id"] != lead[(o["lead_id"],)]["contact_id"]])
    check("order_ts >= opportunity.close_ts", [o["order_id"] for o in D["sales_order"] if o["order_ts"] < (opp[(o["opportunity_id"],)]["close_ts"] or "9")])
    check("orders only for won opportunities", [o["order_id"] for o in D["sales_order"] if opp[(o["opportunity_id"],)]["status"] != "won"])
    check("every won opportunity has an order", [o["opportunity_id"] for o in D["opportunity"] if o["status"] == "won" and o["opportunity_id"] not in {x["opportunity_id"] for x in D["sales_order"]}])
    check("cost_date within campaign dates & <= as-of", [r["cost_id"] for r in D["cost_record"]
          if not (camp[r["campaign_id"]]["start_date"] <= r["cost_date"] <= camp[r["campaign_id"]]["end_date"]) or r["cost_date"] > asof[:10]])

    def transitions(events, key, col, allowed, name, tbl, kcol, ccol):
        by = defaultdict(list)
        for e in events:
            by[e[key]].append(e)
        bad = []
        for k, lst in by.items():
            lst.sort(key=lambda e: e["event_id"])
            prev, last_ts = None, ""
            for e in lst:
                if e[col] not in allowed.get(prev, set()) or e["event_ts"] < last_ts:
                    bad.append((k, prev, e[col]))
                prev, last_ts = e[col], e["event_ts"]
            if idx[tbl][(k,)][ccol] != prev:
                bad.append((k, "current!=last_event", prev))
        check(name, bad)
    transitions(D["lead_status_event"], "lead_id", "to_status", dd.LEAD_TRANSITIONS, "lead lifecycle transitions + current status", "lead", "lead_id", "current_status")
    transitions(D["opportunity_stage_event"], "opportunity_id", "to_stage", dd.OPP_TRANSITIONS, "opportunity stage transitions + current stage", "opportunity", "opportunity_id", "current_stage")
    transitions(D["campaign_status_event"], "campaign_id", "status", dd.CAMPAIGN_TRANSITIONS, "campaign status transitions + current status", "campaign", "campaign_id", "status")
    check("opportunity.status consistent with stage", [o["opportunity_id"] for o in D["opportunity"]
          if o["status"] != {"closed_won": "won", "closed_lost": "lost"}.get(o["current_stage"], "open")])
    per = {p["period_id"]: p for p in D["evaluation_period"]}
    check("evaluation periods are chronological and contiguous", [] if per["train"]["end_ts"] == per["validation"]["start_ts"] and per["validation"]["end_ts"] == per["test"]["start_ts"] and per["train"]["start_ts"] < per["train"]["end_ts"] < per["validation"]["end_ts"] else ["bad"])
    ords = idx["sales_order"]
    check("attribution evaluation_period matches order_ts", [a["attribution_id"] for a in D["attribution_result"]
          if not (per[a["evaluation_period"]]["start_ts"] <= ords[(a["order_id"],)]["order_ts"] < per[a["evaluation_period"]]["end_ts"])])
