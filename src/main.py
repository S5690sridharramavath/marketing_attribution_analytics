"""Command line:  python -m src.main <generate|validate|report|reproduce|docs|all> [--scale S] [--seed N] [--out DIR] [--config FILE]"""
import argparse, json, os, shutil, sys, tempfile, time

from .analytics import build_reports
from .common import sha256_file
from .config import DEFAULT_CONFIG_PATH, Config
from .export.exporter import export_all, write_manifest
from .generators import generate
from .models.data_dictionary import write_data_dictionary
from .validation import validate


def _cfg(a):
    return Config.from_scale(a.scale, a.seed, a.config)


def _formats(a):
    if a.formats in ("default", "all"):
        return {"csv", "sqlite", "sql", "json"}
    return set(a.formats.split(","))


def do_generate(a):
    cfg = _cfg(a)
    t0 = time.time()
    T, truth, quality = generate(cfg)
    files = export_all(a.out, T, truth, quality, cfg, _formats(a))
    scale_txt = a.scale if a.scale is not None else "config"
    write_manifest(a.out, cfg, files, f"python -m src.main generate --scale {scale_txt} --seed {cfg.seed} --out {a.out}")
    print(f"generated in {time.time() - t0:.1f}s -> {a.out}")
    print("  " + ", ".join(f"{k}={len(T[k])}" for k in ("campaign", "contact", "touchpoint", "web_session", "lead", "opportunity", "sales_order", "cost_record", "attribution_result")))
    print(f"  ground-truth rows: {len(truth)}")


def do_validate(a):
    s = validate(a.out)
    print(f"validation: {s['passed']}/{s['total_checks']} checks passed, {s['failed']} failed")
    for c in s["checks"]:
        if c["status"] != "PASS":
            print("  FAIL", c["check"], c["violations"], c["examples"])
    print("  detectors vs ground truth:")
    for d in s["detectors"]:
        print(f"    {d['issue_type']:<46} labelled={d['labelled']:<6} detected={d['detected']:<6} precision={d['precision']} recall={d['recall']}")
    return s["failed"] == 0


def do_report(a):
    rows = build_reports(a.out)
    print("model comparison (variant=clean):")
    for r in rows:
        if r["variant"] == "clean":
            print(f"  {r['model_id']:<15} revenue={r['total_revenue_usd']:>14,.0f} unattributed={r['unattributed_share']:.1%} portfolio_roi={r['portfolio_roi']} "
                  f"stability={r['channel_roi_rank_stability_train_vs_test']} quality_corr={r['campaign_credit_per_engaged_touch_vs_latent_quality_spearman']}")


def do_reproduce(a):
    cfg, sums = _cfg(a), []
    for i in (1, 2):
        d = tempfile.mkdtemp(prefix=f"repro{i}_")
        T, truth, quality = generate(cfg)
        files = export_all(d, T, truth, quality, cfg, {"csv"})
        sums.append({os.path.relpath(f, d): (os.path.getsize(f), sha256_file(f)) for f in files})
        shutil.rmtree(d)
    same = sums[0] == sums[1]
    rows = [dict(file=k, bytes=v[0], sha256=v[1][:16], run2_identical=(sums[1][k] == v)) for k, v in sorted(sums[0].items())]
    os.makedirs(os.path.join(a.out, "reports"), exist_ok=True)
    with open(os.path.join(a.out, "reports", "reproducibility_check.json"), "w") as fh:
        json.dump(dict(seed=cfg.seed, identical=same, files_compared=len(rows), files=rows), fh, indent=1)
    print(f"reproducibility: {'IDENTICAL' if same else 'DIFFERENT'} across 2 runs ({len(rows)} files, seed {cfg.seed})")
    return same


def main(argv=None):
    p = argparse.ArgumentParser(prog="src.main")
    p.add_argument("command", choices=["generate", "validate", "report", "reproduce", "docs", "all"])
    p.add_argument("--scale", type=float, default=None, help="overrides config.yaml: 1.0 = brief volumes, 0.05 = starter")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--out", default="output", help="output root (use '.' to refresh the committed starter layout)")
    p.add_argument("--config", default=DEFAULT_CONFIG_PATH)
    p.add_argument("--formats", default="default", help="default/all = csv+json+sql+sqlite, or a comma list")
    a = p.parse_args(argv)
    ok = True
    if a.command in ("generate", "all"):
        do_generate(a)
    if a.command in ("validate", "all"):
        ok = do_validate(a) and ok
    if a.command in ("report", "all"):
        do_report(a)
    if a.command in ("reproduce", "all"):
        ok = do_reproduce(a) and ok
    if a.command in ("docs", "all"):
        write_data_dictionary(os.path.join(a.out, "docs", "data_dictionary.md"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
