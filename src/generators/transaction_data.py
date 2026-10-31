"""Step 2-3 of the brief: dependent transaction / event records generated from valid parent ids.

Outcomes follow documented rules (score thresholds, ranked qualification, percentile win rule) - not independent dice.
"""
import math
from datetime import timedelta

from ..config import AS_OF, DATA_START
from ..models.data_dictionary import CURRENCIES
from .constants import (CHANNELS, ENG_W, FX_BASE, INTERESTS, SEG_ACV, SEG_CYCLE, SEG_FIT, SEG_FIT_NORM, SEGMENTS,
                        _cum, _pick, iso)
import bisect


# ------------------------------------------------------------------ journeys: touchpoints + sessions
def build_journeys(S):
    cfg, rng, camps, contacts, by_ch, N, nch = S.cfg, S.rng, S.camps, S.contacts, S.by_ch, S.N, S.nch
    # touches per contact: 1 each + remainder proportional to intent (largest remainder => exact total)
    extra = cfg.touchpoints - N
    tot_i = sum(c["intent"] for c in contacts)
    raw = [extra * c["intent"] / tot_i for c in contacts]
    cnt = [1 + int(r) for r in raw]
    short = cfg.touchpoints - sum(cnt)
    for i in sorted(range(N), key=lambda i: (-(raw[i] - int(raw[i])), i))[:short]:
        cnt[i] += 1

    ch_cum = {}
    for seg in SEGMENTS:
        w = []
        for c in CHANNELS:
            m = 1.0
            if seg == "ENT":
                m = {"events": 3.0, "webinar": 1.5, "direct_mail": 2.0, "paid_social": 0.6}.get(c[1], 1.0)
            if seg == "SMB":
                m = {"paid_social": 1.4, "paid_search": 1.1, "events": 0.3, "direct_mail": 0.5}.get(c[1], 1.0)
            w.append(c[3] * m)
        ch_cum[seg] = _cum(w)
    mix = [(_cum(list(c[4].values())), list(c[4].keys())) for c in CHANNELS]
    pick_cache = {}

    def pick_campaign(day, chi, aud):
        key = (day, chi, aud)
        ent = pick_cache.get(key)
        if ent is None:
            cands = [ci for ci in by_ch[chi] if camps[ci]["sd"] <= day <= camps[ci]["ed"]]
            if not cands:
                cands = [ci for ci in range(len(camps)) if camps[ci]["sd"] <= day <= camps[ci]["ed"]]
            ent = (cands, _cum([camps[ci]["usd"] * (4 if aud in camps[ci]["auds"] else 1) for ci in cands]))
            pick_cache[key] = ent
        return _pick(rng, ent[1], ent[0])

    touches, ranges = [], []
    for ci_, c in enumerate(contacts):
        s0 = len(touches)
        first = DATA_START + timedelta(days=rng.randint(0, 226), seconds=rng.randint(0, 86399))
        span = min(rng.randint(10, 150), max((AS_OF - first).days, 0))
        n = cnt[ci_]
        offs = [0.0] + sorted(rng.random() * span for _ in range(n - 1))
        for k, off in enumerate(offs):
            ts = (first + timedelta(days=off)).replace(microsecond=0)
            if ts > AS_OF:
                ts = AS_OF
            day = (ts.date() - DATA_START.date()).days
            chi = _pick(rng, ch_cum[c["seg"]], list(range(nch)))
            camp_i = pick_campaign(day, chi, c["aud"])
            chi = camps[camp_i]["chi"]           # fallback campaigns may belong to another channel: the campaign decides
            tt = _pick(rng, mix[chi][0], mix[chi][1])
            touches.append(dict(c=ci_, ts=ts, camp=camp_i, chi=chi, type=tt,
                                creative=rng.choice(camps[camp_i]["creatives"]),
                                miss=(k > 0 and rng.random() < cfg.missing_id_rate), sess=None))
        ranges.append((s0, len(touches)))
    assert len(touches) == cfg.touchpoints

    # touchpoint ids: per-contact counter (resolved), global counter for missing identity
    seq, unk = [0] * N, 0
    for t in touches:
        if t["miss"]:
            unk += 1
            t["id"] = "TOUCH-UNKNOWN-%06d" % unk
        else:
            seq[t["c"]] += 1
            t["id"] = "TOUCH-%s-%06d" % (contacts[t["c"]]["id"], seq[t["c"]])

    # sessions: one per click touch (offline / impression / email-open / webinar touches have none)
    sess, anon = [], 0
    for ti, t in enumerate(touches):
        if t["type"] != "click":
            continue
        dur = max(5, int(rng.lognormvariate(4.8, 0.8)))
        if t["miss"]:
            anon += 1
            vis, ev = "VIS-ANON%06d" % anon, "none"
        else:
            vis = "VIS-" + contacts[t["c"]]["id"][4:]
            ev = "email_click_id" if CHANNELS[t["chi"]][1] == "email" else "login"
        s = dict(ti=ti, vis=vis, ev=ev, dur=dur, cont=None if t["miss"] else t["c"])
        t["sess"] = s
        sess.append(s)
    sess.sort(key=lambda s: (touches[s["ti"]]["ts"], touches[s["ti"]]["id"]))
    for i, s in enumerate(sess):
        s["id"] = "SES-2026-%06d" % (i + 1)
    S.touches, S.ranges, S.sess = touches, ranges, sess


# ------------------------------------------------------------------ lead rule
def build_leads(S):
    """score = sum(engaged-touch weight x campaign quality) over RESOLVED touches. Top lead_rate share of contacts
    become leads; the lead is created when the running score first reaches the threshold."""
    cfg, rng, camps, contacts, touches, ranges, N = S.cfg, S.rng, S.camps, S.contacts, S.touches, S.ranges, S.N
    final, events = [0.0] * N, [None] * N
    for ci_, (s0, e0) in enumerate(ranges):
        cum, ev = 0.0, []
        for ti in range(s0, e0):
            t = touches[ti]
            if t["miss"] or t["type"] not in ENG_W:
                continue
            cum += ENG_W[t["type"]] * camps[t["camp"]]["q"]
            ev.append((cum, ti))
        final[ci_], events[ci_] = cum, ev
    elig = sorted((c for c in range(N) if final[c] > 0), key=lambda c: (-final[c], c))
    n_leads = min(round(cfg.lead_rate * N), len(elig))
    sel = elig[:n_leads]
    tau = final[sel[-1]]
    leads = []
    for ci_ in sel:
        cum, ti = next(e for e in events[ci_] if e[0] >= tau)
        created = min(AS_OF, touches[ti]["ts"] + timedelta(minutes=rng.randint(1, 2880)))
        leads.append(dict(ci=ci_, ti=ti, score=cum, created=created))
    leads.sort(key=lambda l: (l["created"], l["ci"]))
    for i, l in enumerate(leads):
        l["id"] = "LEAD-2026-%06d" % (i + 1)
        s = touches[l["ti"]]["sess"]
        l["sess"] = s
        if s is not None and s["cont"] is not None:
            s["ev"] = "form_submit"      # lead capture is the strongest identity evidence
    S.final, S.events, S.leads = final, events, leads


# ------------------------------------------------------------------ opportunity + win rules
def build_opportunities(S):
    cfg, rng, contacts, leads, final = S.cfg, S.rng, S.contacts, S.leads, S.final
    n_opps = min(cfg.opportunities, len(leads))
    for l in leads:
        l["qual"] = final[l["ci"]] * SEG_FIT[contacts[l["ci"]]["seg"]]
    ranked = sorted(leads, key=lambda l: (-l["qual"], l["ci"]))[:n_opps]
    opps = []
    for r, l in enumerate(ranked):
        pct = 1.0 - (r / (n_opps - 1) if n_opps > 1 else 0.0)          # 1 = best qualified
        seg = contacts[l["ci"]]["seg"]
        created = min(AS_OF, l["created"] + timedelta(days=2 + 28 * (1 - pct), hours=rng.randint(0, 23)))
        cyc = rng.randint(*SEG_CYCLE[seg])
        amount = max(500, round(SEG_ACV[seg] * rng.lognormvariate(0, 0.35) / 50) * 50)
        opps.append(dict(lead=l, pct=pct, seg=seg, created=created.replace(microsecond=0), cycle=cyc,
                         amount=float(amount), end=(created + timedelta(days=cyc)).replace(microsecond=0)))
    opps.sort(key=lambda o: (o["created"], o["lead"]["id"]))
    closable = [o for o in opps if o["end"] <= AS_OF]
    for o in closable:   # documented win rule: 70% qualification percentile + 30% segment fit + bounded jitter
        o["win_score"] = 0.7 * o["pct"] + 0.3 * SEG_FIT_NORM[o["seg"]] + rng.uniform(-0.05, 0.05)
    n_win = round(cfg.win_rate * len(closable))
    winners = {id(o) for o in sorted(closable, key=lambda o: (-o["win_score"], o["lead"]["id"]))[:n_win]}
    for i, o in enumerate(opps):
        o["id"] = "OPP-2026-%06d" % (i + 1)
        o["outcome"] = "open" if o["end"] > AS_OF else ("won" if id(o) in winners else "lost")
        o["close"] = o["end"] if o["outcome"] == "won" else (
            (o["created"] + timedelta(days=o["cycle"] * rng.uniform(0.4, 1.0))).replace(microsecond=0)
            if o["outcome"] == "lost" else None)
        o["lead"]["opp"] = o
    S.opps = opps


# ------------------------------------------------------------------ append-only event history
def build_lifecycle_events(S):
    T, rng, leads, opps, final = S.T, S.rng, S.leads, S.opps, S.final
    T["lead_status_event"], T["opportunity_stage_event"] = [], []
    nonconv_scores = sorted(final[l["ci"]] for l in leads if "opp" not in l)
    median_nc = nonconv_scores[len(nonconv_scores) // 2] if nonconv_scores else 0.0

    def lev(l, frm, to, ts):
        T["lead_status_event"].append(dict(event_id="LEADEV-%06d" % (len(T["lead_status_event"]) + 1),
                                           lead_id=l["id"], from_status=frm, to_status=to, event_ts=iso(ts)))
        l["status"] = to
    for l in leads:
        lev(l, None, "new", l["created"])
        if "opp" in l:
            o = l["opp"]
            lev(l, "new", "mql", l["created"] + (o["created"] - l["created"]) * 0.3)
            lev(l, "mql", "converted", o["created"])
        else:
            mql = l["created"] + timedelta(days=rng.randint(1, 3))
            if mql <= AS_OF:
                lev(l, "new", "mql", mql)
                fin = mql + timedelta(days=rng.randint(5, 25))
                if fin <= AS_OF:
                    lev(l, "mql", "disqualified" if final[l["ci"]] < median_nc else "nurturing", fin)

    stages = [("qualification", 0.0), ("proposal", 0.30), ("negotiation", 0.65)]
    for o in opps:
        prev = None

        def oev(to, ts):
            nonlocal prev
            T["opportunity_stage_event"].append(dict(
                event_id="OPPEV-%06d" % (len(T["opportunity_stage_event"]) + 1), opportunity_id=o["id"],
                from_stage=prev, to_stage=to, event_ts=iso(ts)))
            prev = to
            o["stage"] = to
        for st, fr in stages:
            ts = o["created"] + timedelta(days=o["cycle"] * fr)
            limit = o["close"] if o["outcome"] == "lost" else AS_OF
            if ts <= limit and (fr == 0 or o["outcome"] != "lost" or ts < o["close"]):
                oev(st, ts.replace(microsecond=0) if fr else o["created"])
        if o["outcome"] == "won":
            oev("closed_won", o["close"])
        elif o["outcome"] == "lost":
            oev("closed_lost", o["close"])


# ------------------------------------------------------------------ orders (closed-won revenue)
def build_base_orders(S):
    S.orders = [dict(opp=o, ts=o["close"], amount=o["amount"], src="crm", dup_of=None) for o in S.opps if o["outcome"] == "won"]


def finalize_orders(S):
    orders, contacts = S.orders, S.contacts
    orders.sort(key=lambda x: (x["ts"], x["opp"]["id"], x["src"]))
    for i, x in enumerate(orders):
        x["id"] = "ORD-2026-%06d" % (i + 1)
    S.T["sales_order"] = [dict(order_id=x["id"], opportunity_id=x["opp"]["id"], contact_id=contacts[x["opp"]["lead"]["ci"]]["id"],
                               order_ts=iso(x["ts"]), amount=x["amount"], currency="USD", order_status="booked",
                               source_system=x["src"]) for x in orders]


# ------------------------------------------------------------------ costs (derived from budgets)
def build_costs(S, omitted):
    """Weekly media rows + one production row per campaign, in the campaign currency (~70-102% of budget)."""
    T, rng, camps = S.T, S.rng, S.camps
    asof_date = AS_OF.date()
    costs = []
    for ci, cp in enumerate(T["campaign"]):
        if ci in omitted:
            continue
        c = camps[ci]
        last = min(c["end"], asof_date)
        days = (last - c["start"]).days + 1
        k = max(1, math.ceil(days / 7))
        total = cp["budget"] * rng.uniform(0.70, 1.02)
        prod = round(total * 0.08, 2)
        ws = [rng.uniform(0.5, 1.5) for _ in range(k)]
        weeks = [round((total - prod) * w / sum(ws), 2) for w in ws]
        if c["end"] <= asof_date:                      # finished campaign: media spend fully booked
            weeks[-1] = round((total - prod) - sum(weeks[:-1]), 2)
        costs.append((c["start"], cp["campaign_id"], "production", prod, cp["currency"]))
        for j, a in enumerate(weeks):
            d = c["start"] + timedelta(days=7 * j)
            if d <= min(c["end"], asof_date):
                costs.append((d, cp["campaign_id"], "media", a, cp["currency"]))
    costs.sort(key=lambda r: (r[0], r[1], r[2]))
    T["cost_record"] = [dict(cost_id="COST-2026-%06d" % (i + 1), campaign_id=r[1], cost_date=r[0].isoformat(),
                             amount=r[3], currency=r[4], cost_type=r[2]) for i, r in enumerate(costs)]


# ------------------------------------------------------------------ derived entity rows
def build_contact_rows(S):
    """contact.created_at = first resolved touch; lifecycle_state derived from lead / opportunity / order records."""
    T, rng, contacts, ranges, touches, leads = S.T, S.rng, S.contacts, S.ranges, S.touches, S.leads
    asof_date = AS_OF.date()
    cont_first = {ci_: touches[s0]["ts"] for ci_, (s0, e0) in enumerate(ranges)}   # first touch is always resolved
    lead_by_ci = {l["ci"]: l for l in leads}
    T["contact"], T["contact_audience"] = [], []
    for ci_, c in enumerate(contacts):
        l = lead_by_ci.get(ci_)
        if l and "opp" in l and l["opp"]["outcome"] == "won":
            state = "customer"
        elif l and "opp" in l:
            state = "opportunity"
        else:
            state = "lead" if l else "prospect"
        T["contact"].append(dict(contact_id=c["id"], segment=c["seg"], region=c["reg"], interest=c["intr"],
                                 primary_audience_id=c["aud"], email_opt_in=c["opt"], created_at=iso(cont_first[ci_]),
                                 lifecycle_state=state))
        cd = cont_first[ci_].date()
        T["contact_audience"].append(dict(contact_id=c["id"], audience_id=c["aud"], effective_from=cd.isoformat(), effective_to=None))
        if rng.random() < 0.20:
            other = rng.choice([i for i in INTERESTS if i != c["intr"]])
            frm = min(asof_date, cd + timedelta(days=rng.randint(5, 60)))
            T["contact_audience"].append(dict(contact_id=c["id"], audience_id=S.aud_id[(c["reg"], c["seg"], other)],
                                              effective_from=frm.isoformat(), effective_to=None))


def build_session_touch_rows(S):
    T, truth, contacts, touches, sess = S.T, S.truth, S.contacts, S.touches, S.sess
    T["web_session"] = [dict(session_id=s["id"], visitor_id=s["vis"], contact_id=None if s["cont"] is None else contacts[s["cont"]]["id"],
                             started_at=iso(touches[s["ti"]]["ts"]), duration_sec=s["dur"],
                             pages_viewed=max(1, round(s["dur"] / 90)), landing_campaign_id=T["campaign"][touches[s["ti"]]["camp"]]["campaign_id"],
                             identity_link_evidence=s["ev"]) for s in sess]
    T["touchpoint"] = []
    for t in sorted(touches, key=lambda t: (t["ts"], t["id"])):
        ch = CHANNELS[t["chi"]]
        T["touchpoint"].append(dict(touchpoint_id=t["id"], contact_id=None if t["miss"] else contacts[t["c"]]["id"],
                                    campaign_id=T["campaign"][t["camp"]]["campaign_id"], creative_id=t["creative"],
                                    channel_id=ch[0], touch_ts=iso(t["ts"]), touch_type=t["type"], is_offline=ch[2],
                                    session_id=t["sess"]["id"] if t["sess"] else None,
                                    identity_link_status="missing" if t["miss"] else "resolved"))
        if t["miss"]:
            truth.append(dict(issue_type="missing_identifier", category="baseline_condition", entity="touchpoint",
                              entity_id=t["id"], related_entity_id=contacts[t["c"]]["id"],
                              description="Touch captured without an identity key; related_entity_id is the TRUE contact, unknowable from inputs",
                              expected_decision="Exclude from attribution; surface as identity gap; never guess the contact"))


def build_lead_opportunity_rows(S):
    T, contacts, touches, leads, opps = S.T, S.contacts, S.touches, S.leads, S.opps
    T["lead"] = []
    for l in leads:
        t = touches[l["ti"]]
        T["lead"].append(dict(lead_id=l["id"], contact_id=contacts[l["ci"]]["id"], session_id=l["sess"]["id"] if l["sess"] else None,
                              creating_touchpoint_id=t["id"], crm_source_campaign_id=T["campaign"][t["camp"]]["campaign_id"],
                              created_at=iso(l["created"]), lead_score=round(l["score"], 2), current_status=l["status"]))
    T["opportunity"] = [dict(opportunity_id=o["id"], lead_id=o["lead"]["id"], contact_id=contacts[o["lead"]["ci"]]["id"],
                             created_at=iso(o["created"]), qualification_score=round(o["lead"]["qual"], 2), amount=o["amount"],
                             currency="USD", current_stage=o["stage"],
                             status={"closed_won": "won", "closed_lost": "lost"}.get(o["stage"], "open"),
                             close_ts=iso(o["close"]) if o["close"] else None) for o in opps]


def build_fx_rates(S):
    T, rng = S.T, S.rng
    T["fx_rate"] = []
    for y, m in [(2025, 12)] + [(2026, k) for k in range(1, 11)]:
        for cur in CURRENCIES:
            rate = 1.0 if cur == "USD" else round(FX_BASE[cur] * (1 + rng.uniform(-0.01, 0.01)), 5)
            T["fx_rate"].append(dict(fx_rate_id=f"FX-{cur}-{y}-{m:02d}", currency=cur, rate_month=f"{y}-{m:02d}", rate_to_usd=rate))
