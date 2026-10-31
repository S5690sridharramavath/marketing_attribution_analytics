"""Evaluation metrics for comparing attribution approaches."""
from collections import defaultdict

TOUCH_ENGAGED = ("click", "email_open", "event_attendance", "webinar_attendance", "mail_response")


def spearman(xs, ys):
    """Spearman rank correlation with average ranks for ties. Returns None if undefined."""
    n = len(xs)
    if n < 3:
        return None

    def ranks(v):
        order = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = sum((a - mx) ** 2 for a in rx) ** 0.5
    dy = sum((b - my) ** 2 for b in ry) ** 0.5
    return None if dx == 0 or dy == 0 else round(num / (dx * dy), 4)


def engaged_touch_counts(touchpoints):
    eng = defaultdict(int)
    for t in touchpoints:
        if t["identity_link_status"] == "resolved" and t["touch_type"] in TOUCH_ENGAGED:
            eng[t["campaign_id"]] += 1
    return eng


def model_comparison(models, camps, has_cost, cost, rev, unattr, total_rev, ch_rows, eng, quality):
    """One row per (model, variant): coverage, portfolio ROI, chronological stability, and (evaluation-only) validity."""
    out = []
    for m in models:
        for var in ("raw", "clean"):
            tot, un = total_rev[(m, "all", var)], unattr[(m, "all", var)]
            crev = {c: rev.get((c, m, "all", var), 0.0) for c in camps}
            used = [c for c in camps if eng[c] > 0]
            qual = spearman([crev[c] / eng[c] for c in used], [quality[c] for c in used])
            sel = lambda p: {r["channel_name"]: r["roi"] for r in ch_rows if r["model_id"] == m and r["variant"] == var and r["period"] == p and r["roi"] is not None}
            tr, te = sel("train"), sel("test")
            common = sorted(set(tr) & set(te))
            stab = spearman([tr[c] for c in common], [te[c] for c in common])
            costed = [c for c in camps if c in has_cost]
            rv, ck = sum(crev[c] for c in costed), sum(cost[(c, "all", var)] for c in costed)
            out.append(dict(model_id=m, variant=var, total_revenue_usd=round(tot, 2), unattributed_revenue_usd=round(un, 2),
                            unattributed_share=round(un / tot, 4) if tot else None,
                            portfolio_roi=round((rv - ck) / ck, 4) if ck else None,
                            channel_roi_rank_stability_train_vs_test=stab, n_channels_compared=len(common),
                            campaign_credit_per_engaged_touch_vs_latent_quality_spearman=qual))
    return out
