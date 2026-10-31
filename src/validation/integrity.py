"""Primary keys, ID formats, required fields, enums, timestamp shape, foreign keys, duplicates."""
import re

from ..models import data_dictionary as dd
from .context import count

ISO_TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")


def run(ctx):
    D, check = ctx.D, ctx.check
    for t in dd.TABLE_ORDER:
        pk = dd.SCHEMA[t]["pk"]
        seen, dup = set(), []
        for r in D[t]:
            k = tuple(r[c] for c in pk)
            if None in k or k in seen:
                dup.append(k)
            seen.add(k)
        check(f"PK unique+not null: {t}", dup)
    for t, (col, pat) in dd.ID_PATTERNS.items():
        rx = re.compile(pat)
        check(f"ID format: {t}.{col}", [r[col] for r in D[t] if not rx.match(r[col])])
    for t in dd.TABLE_ORDER:
        miss = [(f["name"], i) for i, r in enumerate(D[t]) for f in dd.SCHEMA[t]["fields"] if f["required"] and r[f["name"]] is None]
        check(f"required fields present: {t}", miss)
    for (t, c), allowed in dd.ENUMS.items():
        check(f"enum: {t}.{c}", [r[c] for r in D[t] if r[c] is not None and r[c] not in allowed])
    for t in D:
        for f in dd.SCHEMA[t]["fields"]:
            if f["type"] == "datetime":
                check(f"timestamp format: {t}.{f['name']}", [r[f["name"]] for r in D[t] if r[f["name"]] and not ISO_TS.match(r[f["name"]])])
    pkset = {t: {r[dd.SCHEMA[t]["pk"][0]] for r in D[t]} for t in D}
    for (ct, cc, pt, pc, opt) in dd.FKS:
        bad = [r[cc] for r in D[ct] if (r[cc] is not None and r[cc] not in pkset[pt]) or (r[cc] is None and not opt)]
        check(f"FK: {ct}.{cc} -> {pt}.{pc}", bad)
    check("duplicate touches (contact,campaign,ts,type)", [k for k, v in count((t["contact_id"], t["campaign_id"], t["touch_ts"], t["touch_type"]) for t in D["touchpoint"] if t["contact_id"]).items() if v > 1])
    check("one session per click touch", [k for k, v in count(t["session_id"] for t in D["touchpoint"] if t["session_id"]).items() if v > 1])
    check("one lead per contact", [k for k, v in count(l["contact_id"] for l in D["lead"]).items() if v > 1])
    check("one opportunity per lead", [k for k, v in count(o["lead_id"] for o in D["opportunity"]).items() if v > 1])
