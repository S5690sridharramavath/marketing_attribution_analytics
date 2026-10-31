"""Configuration: YAML file (config/config.yaml) -> Config. One generator, parameterised scale."""
import os
from dataclasses import dataclass
from datetime import datetime

GENERATOR_VERSION = "2.0.0"
DATA_START = datetime(2026, 1, 1)            # first possible touch
AS_OF = datetime(2026, 10, 22, 23, 59, 59)   # data cut-off ("today" inside the dataset)
DEFAULT_SEED = 20261022
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "config.yaml")


def read_yaml(path):
    """Tiny parser for the flat 'key: value' YAML subset used here (keeps the project dependency-free)."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.split(" #")[0].split("\t#")[0].rstrip()
            if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
                continue
            k, v = line.split(":", 1)
            v = v.strip()
            for cast in (int, float):
                try:
                    v = cast(v)
                    break
                except ValueError:
                    continue
            out[k.strip()] = v
    return out


@dataclass(frozen=True)
class Config:
    seed: int = DEFAULT_SEED
    campaigns: int = 500
    contacts: int = 50_000
    touchpoints: int = 200_000
    opportunities: int = 10_000
    lead_rate: float = 0.40
    win_rate: float = 0.38
    missing_id_rate: float = 0.05
    lookback_days: int = 120
    post_conv_grace_days: int = 90
    n_dup_orders: int = 40
    n_post_conv: int = 60
    n_cost_mismatch: int = 30
    n_cost_omitted: int = 15
    n_anon_linked: int = 25

    @staticmethod
    def from_scale(scale=None, seed=None, path=DEFAULT_CONFIG_PATH):
        y = read_yaml(path) if path and os.path.exists(path) else {}
        d = Config()
        g = lambda k: y.get(k, getattr(d, k))
        scale = float(y.get("scale", 1.0) if scale is None else scale)
        seed = int(y.get("seed", DEFAULT_SEED) if seed is None else seed)
        c = lambda k, floor: max(floor, round(g(k) * scale))
        return Config(
            seed=seed, campaigns=c("campaigns", 20), contacts=c("contacts", 500),
            touchpoints=c("touchpoints", 2_000), opportunities=c("opportunities", 100),
            lead_rate=g("lead_rate"), win_rate=g("win_rate"), missing_id_rate=g("missing_id_rate"),
            lookback_days=int(g("lookback_days")), post_conv_grace_days=int(g("post_conv_grace_days")),
            n_dup_orders=c("n_dup_orders", 3), n_post_conv=c("n_post_conv", 3), n_cost_mismatch=c("n_cost_mismatch", 3),
            n_cost_omitted=c("n_cost_omitted", 2), n_anon_linked=c("n_anon_linked", 3))
