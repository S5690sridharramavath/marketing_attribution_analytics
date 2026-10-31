"""Step 8 of the brief. Validates the EXPORTED CSVs (independent of generator memory).

STRUCTURAL checks must have zero violations; DETECTOR checks must reproduce ground_truth exactly."""
import json, os

from ..config import AS_OF
from ..export.exporter import load_tables
from . import anomaly_detection, integrity, reconciliation, temporal
from .context import Ctx

FMT = "%Y-%m-%dT%H:%M:%S"


def validate(out, write=True):
    D = load_tables(out)
    ctx = Ctx(D, AS_OF.strftime(FMT))
    integrity.run(ctx)
    temporal.run(ctx)
    reconciliation.run(ctx)
    det = anomaly_detection.run(ctx, out)
    summary = dict(total_checks=len(ctx.results), failed=ctx.fails, passed=len(ctx.results) - ctx.fails, as_of=AS_OF.isoformat(),
                   row_counts={t: len(D[t]) for t in D}, detectors=det, checks=ctx.results)
    if write:
        os.makedirs(os.path.join(out, "reports"), exist_ok=True)
        with open(os.path.join(out, "reports", "validation_summary.json"), "w") as fh:
            json.dump(summary, fh, indent=1)
    return summary
