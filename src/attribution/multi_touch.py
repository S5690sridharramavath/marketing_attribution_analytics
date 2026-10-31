"""Multi-touch rules: linear, time_decay, position_based."""
from datetime import datetime

FMT = "%Y-%m-%dT%H:%M:%S"
HALF_LIFE_DAYS = 7.0


def linear(tss, order_dt):
    return [1.0] * len(tss)


def time_decay(tss, order_dt):
    return [0.5 ** (((order_dt - datetime.strptime(t, FMT)).total_seconds() / 86400.0) / HALF_LIFE_DAYS) for t in tss]


def position_based(tss, order_dt):
    n = len(tss)
    if n == 1:
        return [1.0]
    if n == 2:
        return [0.5, 0.5]
    mid = 0.2 / (n - 2)
    return [0.4] + [mid] * (n - 2) + [0.4]


DESCRIPTIONS = {
    "linear": "Equal credit to every eligible touch in the window",
    "time_decay": "Credit proportional to 0.5^(age_days/7): recent touches weigh more",
    "position_based": "40% first, 40% last, 20% shared by middle touches (2 touches: 50/50; 1 touch: 100%)",
}
