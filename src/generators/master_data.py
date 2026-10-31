"""Step 1 of the brief: master / reference data first - Channel, Audience, Campaign (+bridge, history), Creative, Contact."""
from datetime import date, datetime, timedelta

from ..config import AS_OF, DATA_START
from ..models.data_dictionary import CURRENCIES
from .constants import (CHANNELS, FORMATS, FX_BASE, CUR_W, INTERESTS, REGIONS, REG_W, SEG_INTENT, SEGMENTS, SEG_W,
                        THEMES, iso)


def build_master_data(S):
    cfg, rng, T = S.cfg, S.rng, S.T
    nch = len(CHANNELS)
    asof_date = AS_OF.date()

    T["channel"] = [dict(channel_id=c[0], channel_name=c[1], channel_type="offline" if c[2] else "digital",
                         is_offline=c[2], cost_model=c[5]) for c in CHANNELS]
    aud_id, T["audience"] = {}, []
    for r in REGIONS:
        for s in SEGMENTS:
            for i in INTERESTS:
                aid = "AUD-%04d" % (len(T["audience"]) + 1)
                aud_id[(r, s, i)] = aid
                T["audience"].append(dict(audience_id=aid, audience_name=f"{r}-{s}-{i}", region=r, segment=s, interest=i))
    all_aud = [a["audience_id"] for a in T["audience"]]

    camps, T["campaign"], T["campaign_audience"], T["campaign_status_event"], T["creative"] = [], [], [], [], []
    camp_w = [c[7] for c in CHANNELS]
    for i in range(cfg.campaigns):
        chi = i if i < nch else rng.choices(range(nch), weights=camp_w)[0]
        ch = CHANNELS[chi]
        if ch[8]:
            start = date(2025, 12, 1) + timedelta(days=0 if i < nch else rng.randint(0, 45))
            end = date(2026, 12, 31)
        else:
            start = date(2025, 12, 15) + timedelta(days=rng.randint(0, 274))
            end = start + timedelta(days=rng.randint(30, 120))
        usd = max(2_000, round(ch[6] * rng.lognormvariate(0, 0.6), -2))
        cur = rng.choices(CURRENCIES, weights=CUR_W)[0]
        quality = min(3.0, max(0.3, rng.lognormvariate(0, 0.4)))
        cid = "CMP-2026-%06d" % (i + 1)
        status = "completed" if end < asof_date else ("active" if start <= asof_date else "planned")
        auds = sorted(rng.sample(all_aud, rng.randint(1, 3)))
        camp = dict(campaign_id=cid, campaign_name=f"{ch[1]}-{rng.choice(THEMES)}-{i + 1:04d}", channel_id=ch[0],
                    objective=rng.choices(["lead_gen", "pipeline", "brand"], weights=[.45, .40, .15])[0],
                    budget=round(usd / FX_BASE[cur], -2), currency=cur, start_date=start.isoformat(),
                    end_date=end.isoformat(), status=status)
        T["campaign"].append(camp)
        camps.append(dict(chi=chi, usd=usd, q=quality, sd=(start - DATA_START.date()).days,
                          ed=(end - DATA_START.date()).days, auds=set(auds), start=start, end=end, creatives=[]))
        for a in auds:
            T["campaign_audience"].append(dict(campaign_id=cid, audience_id=a, effective_from=start.isoformat(),
                                               effective_to=end.isoformat()))
        # lifecycle history: planned -> active -> completed (only events that have happened by AS_OF)
        evs = [("planned", datetime.combine(start, datetime.min.time()) - timedelta(days=rng.randint(7, 30))),
               ("active", datetime.combine(start, datetime.min.time()))]
        if end < asof_date:
            evs.append(("completed", datetime.combine(end, datetime.max.time()).replace(microsecond=0)))
        for st, ts in evs:
            if ts <= AS_OF:
                T["campaign_status_event"].append(dict(event_id="CMPEV-%06d" % (len(T["campaign_status_event"]) + 1),
                                                       campaign_id=cid, status=st, event_ts=iso(ts)))
        for k in range(rng.randint(1, 3) + (2 if ch[1] in ("paid_social", "display") else 0)):
            crid = "CRE-%06d" % (len(T["creative"]) + 1)
            T["creative"].append(dict(creative_id=crid, campaign_id=cid, creative_name=f"{cid}-v{k + 1}",
                                      format=rng.choice(FORMATS[ch[1]]),
                                      created_date=(start - timedelta(days=rng.randint(1, 20))).isoformat()))
            camps[-1]["creatives"].append(crid)

    by_ch = [[] for _ in range(nch)]
    for ci, c in enumerate(camps):
        by_ch[c["chi"]].append(ci)

    # contacts (created_at / lifecycle_state are derived later from source records)
    contacts = []
    for i in range(cfg.contacts):
        seg = rng.choices(SEGMENTS, SEG_W)[0]
        reg = rng.choices(REGIONS, REG_W)[0]
        intr = rng.choice(INTERESTS)
        contacts.append(dict(id="CON-%06d" % (i + 1), seg=seg, reg=reg, intr=intr, aud=aud_id[(reg, seg, intr)],
                             opt=1 if rng.random() < 0.8 else 0,
                             intent=rng.lognormvariate(0, 0.7) * SEG_INTENT[seg]))
    S.camps, S.by_ch, S.contacts, S.aud_id, S.N, S.nch = camps, by_ch, contacts, aud_id, cfg.contacts, nch
