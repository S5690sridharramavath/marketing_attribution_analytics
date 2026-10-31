import os, sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.export.exporter import export_all
from src.generators import generate

SCALE = 0.02


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    out = str(tmp_path_factory.mktemp("ds"))
    cfg = Config.from_scale(SCALE)
    T, truth, q = generate(cfg)
    export_all(out, T, truth, q, cfg, {"csv", "sqlite"})
    return out, cfg, T, truth
