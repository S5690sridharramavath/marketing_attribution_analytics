import csv, os, shutil

from src.export.exporter import table_path
from src.validation import validate


def test_all_structural_checks_and_detectors_pass(built):
    s = validate(built[0], write=False)
    failing = [c for c in s["checks"] if c["status"] != "PASS"]
    assert not failing, failing[:3]
    assert all(d["precision"] in (1.0, None) and d["recall"] in (1.0, None) for d in s["detectors"])


def test_evaluation_periods_are_chronological(built):
    from src.common import read_csv
    out = built[0]
    D = {r["period_id"]: r for r in read_csv(table_path(out, "evaluation_period"))}
    assert D["train"]["end_ts"] == D["validation"]["start_ts"] and D["validation"]["end_ts"] == D["test"]["start_ts"]
    orders = {o["order_id"]: o["order_ts"] for o in read_csv(table_path(out, "sales_order"))}
    by = {}
    for a in read_csv(table_path(out, "attribution_result")):
        by.setdefault(a["evaluation_period"], []).append(a["order_id"])
    mx = {p: max(orders[i] for i in ids) for p, ids in by.items()}
    mn = {p: min(orders[i] for i in ids) for p, ids in by.items()}
    assert mx["train"] < mn["validation"] and mx["validation"] < mn["test"]


# ---- negative tests: the validator must catch corruption (and never crash on it)
def _corrupt(built, tmp_path, table, mutate):
    dst = str(tmp_path / "bad")
    shutil.copytree(built[0], dst, ignore=shutil.ignore_patterns("*.sqlite"))
    p = table_path(dst, table)
    rows = list(csv.DictReader(open(p)))
    mutate(rows)
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return validate(dst, write=False)


def test_validator_catches_broken_foreign_key(built, tmp_path):
    s = _corrupt(built, tmp_path, "touchpoint", lambda rows: rows[0].update(campaign_id="CMP-2026-999999"))
    assert any("FK: touchpoint.campaign_id" in c["check"] and c["status"] == "FAIL" for c in s["checks"])


def test_validator_catches_duplicate_primary_key(built, tmp_path):
    s = _corrupt(built, tmp_path, "lead", lambda rows: rows[1].update(lead_id=rows[0]["lead_id"]))
    assert any(c["check"] == "PK unique+not null: lead" and c["status"] == "FAIL" for c in s["checks"])


def test_validator_catches_bad_enum_and_reconciliation(built, tmp_path):
    s = _corrupt(built, tmp_path, "attribution_result", lambda rows: rows[0].update(attributed_revenue="1.00", model_id="magic"))
    bad = {c["check"] for c in s["checks"] if c["status"] == "FAIL"}
    assert "enum: attribution_result.model_id" in bad and "credits per (order,model) sum to order amount (cents)" in bad


def test_validator_catches_temporal_violation(built, tmp_path):
    s = _corrupt(built, tmp_path, "touchpoint", lambda rows: rows[0].update(touch_ts="2031-01-01T00:00:00"))
    bad = {c["check"] for c in s["checks"] if c["status"] == "FAIL"}
    assert "touch_ts <= as-of" in bad and "touch within campaign dates" in bad


def test_unlabelled_anomaly_breaks_detector_check(built, tmp_path):
    def dup(rows):
        r = dict(rows[0]); r["order_id"] = "ORD-2026-999999"; rows.append(r)
    s = _corrupt(built, tmp_path, "sales_order", dup)
    assert any(c["check"].startswith("detector == ground truth: revenue_counted") and c["status"] == "FAIL" for c in s["checks"])
