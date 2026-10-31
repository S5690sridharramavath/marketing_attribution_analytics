import os

from src.common import sha256_file
from src.config import Config
from src.export.exporter import export_all
from src.generators import generate


def _run(path, cfg):
    T, truth, q = generate(cfg)
    return {os.path.relpath(f, path): sha256_file(f) for f in export_all(path, T, truth, q, cfg, {"csv"})}


def test_same_seed_is_byte_identical(tmp_path):
    cfg = Config.from_scale(0.02)
    assert _run(str(tmp_path / "a"), cfg) == _run(str(tmp_path / "b"), cfg)


def test_different_seed_changes_data(tmp_path):
    a = _run(str(tmp_path / "a"), Config.from_scale(0.02, seed=1))
    b = _run(str(tmp_path / "b"), Config.from_scale(0.02, seed=2))
    assert a != b


def test_starter_and_full_share_one_code_path():
    # same generator, only the scale parameter differs
    assert Config.from_scale(0.05).seed == Config.from_scale(1.0).seed == 20261022
