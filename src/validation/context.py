from ..models import data_dictionary as dd


class Ghost(dict):
    """Row returned for a dangling key so a broken join is REPORTED by the FK check instead of crashing validation."""
    def __missing__(self, key):
        return "0"


class Index(dict):
    def __missing__(self, key):
        return Ghost()


class Ctx:
    def __init__(self, D, asof):
        self.D, self.asof = D, asof
        self.results, self.fails = [], 0
        self.idx = {t: Index({tuple(r[k] for k in dd.SCHEMA[t]["pk"]): r for r in D[t]}) for t in D}
        self.camp = Index({c["campaign_id"]: c for c in D["campaign"]})
        self.cre = Index({c["creative_id"]: c for c in D["creative"]})
        self.chan = Index({c["channel_id"]: c for c in D["channel"]})

    def check(self, name, bad, kind="structural", note=""):
        ok = len(bad) == 0
        self.fails += 0 if ok else 1
        self.results.append(dict(check=name, kind=kind, violations=len(bad), status="PASS" if ok else "FAIL",
                                 examples=[str(b) for b in bad[:3]], note=note))


def count(it):
    d = {}
    for x in it:
        d[x] = d.get(x, 0) + 1
    return d
