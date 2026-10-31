import os, sqlite3

from src.config import Config, read_yaml, DEFAULT_CONFIG_PATH
from src.models.data_dictionary import PROCESSED_TABLES, RAW_TABLES, TABLE_ORDER


def test_full_scale_defaults_match_brief():
    c = Config.from_scale(1.0)
    assert (c.campaigns, c.contacts, c.touchpoints, c.opportunities, c.seed) == (500, 50_000, 200_000, 10_000, 20261022)


def test_yaml_config_is_read_and_cli_scale_overrides_it():
    y = read_yaml(DEFAULT_CONFIG_PATH)
    assert y["seed"] == 20261022 and y["contacts"] == 50000
    assert Config.from_scale(0.05).contacts == 2500 and Config.from_scale(0.05, seed=7).seed == 7


def test_exact_volumes_at_any_scale(built):
    _, cfg, T, _ = built
    assert len(T["campaign"]) == cfg.campaigns and len(T["contact"]) == cfg.contacts
    assert len(T["touchpoint"]) == cfg.touchpoints and len(T["opportunity"]) == cfg.opportunities


def test_raw_and_processed_layout(built):
    out = built[0]
    for t in RAW_TABLES:
        assert os.path.exists(os.path.join(out, "data", "raw", f"{t}.csv"))
    for t in PROCESSED_TABLES:
        assert os.path.exists(os.path.join(out, "data", "processed", f"{t}.csv"))
    assert len(RAW_TABLES) + len(PROCESSED_TABLES) == len(TABLE_ORDER)


def test_edge_cases_present_and_labelled(built):
    _, cfg, _, truth = built
    got = {}
    for r in truth:
        got[r["issue_type"]] = got.get(r["issue_type"], 0) + 1
    assert got["revenue_counted_more_than_once"] == cfg.n_dup_orders
    assert got["spend_currency_mismatch"] == cfg.n_cost_mismatch
    assert got["campaign_costs_omitted"] == cfg.n_cost_omitted
    assert got["anonymous_session_linked_without_evidence"] == cfg.n_anon_linked
    assert got["touchpoint_after_conversion_attributed"] > 0 and got["missing_identifier"] > 0


def test_ground_truth_is_separate_from_inputs(built):
    out = built[0]
    assert os.path.exists(os.path.join(out, "data", "ground_truth", "ground_truth.csv"))
    for sub in ("raw", "processed"):
        for f in os.listdir(os.path.join(out, "data", sub)):
            header = open(os.path.join(out, "data", sub, f)).readline()
            assert "issue_type" not in header and "latent_quality" not in header


def test_ids_follow_naming_convention(built):
    T = built[2]
    assert T["campaign"][0]["campaign_id"] == "CMP-2026-000001"
    assert T["web_session"][0]["session_id"].startswith("SES-2026-")
    assert T["lead"][0]["lead_id"].startswith("LEAD-2026-") and T["opportunity"][0]["opportunity_id"].startswith("OPP-2026-")
    resolved = [t for t in T["touchpoint"] if t["contact_id"]]
    assert all(t["touchpoint_id"].startswith(f"TOUCH-{t['contact_id']}-") for t in resolved)


def test_sqlite_load_respects_foreign_keys(built):
    con = sqlite3.connect(os.path.join(built[0], "database", "attribution.sqlite"))
    assert con.execute("PRAGMA foreign_key_check").fetchall() == []


def test_json_sql_exports_match_csv_row_counts(tmp_path):
    from src.config import Config
    from src.export.exporter import export_all
    from src.generators import generate

    out = str(tmp_path / "jsonsql")
    cfg = Config.from_scale(0.02)
    T, truth, q = generate(cfg)
    files = export_all(out, T, truth, q, cfg, {"csv", "json", "sql"})
    assert any(f.endswith(os.path.join("data", "json", "campaign.json")) or f.replace("\\", "/").endswith("data/json/campaign.json") for f in files)
    import json
    with open(os.path.join(out, "data", "json", "campaign.json"), encoding="utf-8") as fh:
        assert len(json.load(fh)) == len(T["campaign"]) == cfg.campaigns
    seed = open(os.path.join(out, "database", "seed.sql"), encoding="utf-8").read()
    assert "INSERT INTO campaign" in seed and "PRAGMA foreign_keys=ON" in seed
