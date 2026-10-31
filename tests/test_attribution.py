from datetime import datetime

from src.analytics.metrics import spearman
from src.attribution import first_touch, last_touch, multi_touch
from src.attribution.engine import run_attribution, split_cents, weights


def test_split_cents_is_exact():
    for total in (1, 99, 10_001, 123_456_789):
        for w in ([1], [1, 1, 1], [0.4, 0.1, 0.1, 0.4], [3, 0, 0, 7]):
            assert sum(split_cents(total, w)) == total


def test_model_weights():
    ts = ["2026-03-01T00:00:00", "2026-03-10T00:00:00", "2026-03-20T00:00:00", "2026-03-30T00:00:00"]
    o = datetime(2026, 4, 1)
    assert first_touch.weights(ts, o) == [1, 0, 0, 0] == weights("first_touch", ts, o)
    assert last_touch.weights(ts, o) == [0, 0, 0, 1]
    assert multi_touch.linear(ts, o) == [1, 1, 1, 1]
    pb = multi_touch.position_based(ts, o)
    assert pb[0] == pb[-1] == 0.4 and abs(sum(pb) - 1) < 1e-9
    assert multi_touch.position_based(ts[:1], o) == [1.0] and multi_touch.position_based(ts[:2], o) == [0.5, 0.5]
    td = multi_touch.time_decay(ts, o)
    assert td == sorted(td)                      # more recent touch => larger weight


def _t(i, cid, ts, typ="click", status="resolved"):
    return dict(touchpoint_id=f"T{i}", contact_id=cid, campaign_id=f"C{i}", touch_ts=ts, touch_type=typ, identity_link_status=status)


def test_window_boundaries_and_ineligible_touches():
    order = dict(order_id="O1", opportunity_id="P1", contact_id="K", order_ts="2026-06-01T00:00:00", amount="1000.00")
    touches = [
        _t(1, "K", "2025-12-01T00:00:00"),                    # outside 120d window -> ignored
        _t(2, "K", "2026-02-05T00:00:00"),                    # inside
        _t(3, "K", "2026-05-01T00:00:00", typ="impression"),  # not engaged -> ignored
        _t(4, "K", "2026-05-20T00:00:00", status="missing"),  # unresolved identity -> ignored
        _t(5, "K", "2026-06-02T00:00:00"),                    # AFTER conversion -> ignored
        _t(6, "OTHER", "2026-05-25T00:00:00"),                # other contact
    ]
    rows, flagged = run_attribution(touches, [order], lambda ts: "train", 120)
    assert {r["touchpoint_id"] for r in rows if r["model_id"] == "linear"} == {"T2"} and flagged == []
    rows, flagged = run_attribution(touches, [order], lambda ts: "train", 120, post_conv_orders={"O1"})
    assert flagged and {r["touchpoint_id"] for r in rows if r["attribution_id"] in flagged} == {"T5"}


def test_no_eligible_touch_is_visible_not_dropped():
    order = dict(order_id="O1", opportunity_id="P1", contact_id="K", order_ts="2026-06-01T00:00:00", amount="500.00")
    rows, _ = run_attribution([], [order], lambda ts: "test", 120)
    assert len(rows) == 5 and all(r["attribution_status"] == "unattributed_no_eligible_touch" and r["attributed_revenue"] == 500.0 for r in rows)


def test_multi_touch_credits_reconcile_to_order_amount():
    order = dict(order_id="O1", opportunity_id="P1", contact_id="K", order_ts="2026-06-01T00:00:00", amount="1000.01")
    touches = [_t(i, "K", f"2026-05-{i + 1:02d}T00:00:00") for i in range(1, 8)]
    rows, _ = run_attribution(touches, [order], lambda ts: "train", 120)
    for m in ("first_touch", "last_touch", "linear", "time_decay", "position_based"):
        assert round(sum(r["attributed_revenue"] for r in rows if r["model_id"] == m) * 100) == 100001


def test_spearman():
    assert spearman([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0
    assert spearman([1, 2, 3, 4], [4, 3, 2, 1]) == -1.0
    assert spearman([1, 1, 1], [1, 2, 3]) is None
