"""Step 9 of the brief: export CSV / JSON / SQL / SQLite plus manifest.

Layout written under <out>/ (default repo layout):
  data/raw/*.csv            tables produced by the generators
  data/processed/*.csv      tables derived by the attribution step
  data/ground_truth/        labelled anomalies + latent campaign quality  (NEVER read by the pipeline's input loaders)
  data/source_manifest.json command, seed, parameters, SHA-256 + row count per file, provenance
  database/schema.sql|seed.sql|attribution.sqlite
"""
import json, os, platform, sqlite3, sys

from ..common import sha256_file, write_csv, read_csv
from ..config import AS_OF, GENERATOR_VERSION
from ..models import data_dictionary as dd

TRUTH_FIELDS = ["gt_id", "issue_type", "category", "entity", "entity_id", "related_entity_id", "description", "expected_decision"]


def table_path(out, t):
    return os.path.join(out, "data", dd.table_dir(t), f"{t}.csv")


def load_tables(out):
    """Load ONLY input tables (raw + processed). Ground truth lives elsewhere and is never loaded here."""
    return {t: read_csv(table_path(out, t)) for t in dd.TABLE_ORDER}


def _sql_val(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return repr(v)
    return "'" + str(v).replace("'", "''") + "'"


def export_all(out, T, truth, quality, cfg, formats):
    files = []
    for t in dd.TABLE_ORDER:
        p = table_path(out, t)
        write_csv(p, T[t], dd.columns(t))
        files.append(p)
    gt = os.path.join(out, "data", "ground_truth")
    os.makedirs(gt, exist_ok=True)
    write_csv(os.path.join(gt, "ground_truth.csv"), truth, TRUTH_FIELDS)
    with open(os.path.join(gt, "ground_truth.json"), "w") as fh:
        json.dump(truth, fh, indent=1)
    write_csv(os.path.join(gt, "ground_truth_campaign_quality.csv"), quality, ["campaign_id", "latent_quality"])
    files += [os.path.join(gt, f) for f in ("ground_truth.csv", "ground_truth.json", "ground_truth_campaign_quality.csv")]

    db = os.path.join(out, "database")
    os.makedirs(db, exist_ok=True)
    with open(os.path.join(db, "schema.sql"), "w") as fh:
        fh.write(dd.ddl())
    files.append(os.path.join(db, "schema.sql"))
    if "json" in formats:
        jd = os.path.join(out, "data", "json")
        os.makedirs(jd, exist_ok=True)
        for t in dd.TABLE_ORDER:
            p = os.path.join(jd, f"{t}.json")
            with open(p, "w") as fh:
                json.dump([{k: r.get(k) for k in dd.columns(t)} for r in T[t]], fh, separators=(",", ":"))
            files.append(p)
    if "sql" in formats:
        p = os.path.join(db, "seed.sql")
        with open(p, "w") as fh:
            fh.write("PRAGMA foreign_keys=ON;\nBEGIN;\n")
            for t in dd.TABLE_ORDER:
                cols, rows = dd.columns(t), T[t]
                for i in range(0, len(rows), 500):
                    vals = ",\n".join("(" + ",".join(_sql_val(r.get(c)) for c in cols) + ")" for r in rows[i:i + 500])
                    fh.write(f"INSERT INTO {t} ({','.join(cols)}) VALUES\n{vals};\n")
            fh.write("COMMIT;\n")
        files.append(p)
    if "sqlite" in formats:
        p = os.path.join(db, "attribution.sqlite")
        if os.path.exists(p):
            os.remove(p)
        con = sqlite3.connect(p)
        con.executescript(dd.ddl())
        con.execute("PRAGMA foreign_keys=ON")        # FK integrity is enforced during load
        for t in dd.TABLE_ORDER:
            cols = dd.columns(t)
            con.executemany(f"INSERT INTO {t} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                            [tuple(r.get(c) for c in cols) for r in T[t]])
        con.commit()
        con.close()
    return files


def write_manifest(out, cfg, files, command):
    entries = []
    for p in sorted(files):
        n = None
        if p.endswith(".csv"):
            with open(p, "rb") as fh:
                n = sum(1 for _ in fh) - 1
        entries.append(dict(file=os.path.relpath(p, out), rows=n, sha256=sha256_file(p)))
    manifest = dict(generator_version=GENERATOR_VERSION, command=command, seed=cfg.seed, as_of=AS_OF.isoformat(),
                    parameters=cfg.__dict__, python=sys.version.split()[0], platform=platform.platform(),
                    external_data=[], provenance="100% synthetic. No external or personal data used; no sources to attribute.",
                    files=entries)
    with open(os.path.join(out, "data", "source_manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=1)
    return manifest
