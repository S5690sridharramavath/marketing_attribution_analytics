NAME = "first_touch"
DESCRIPTION = "100% of credit to the earliest eligible touch in the window"


def weights(tss, order_dt):
    return [1.0] + [0.0] * (len(tss) - 1)
