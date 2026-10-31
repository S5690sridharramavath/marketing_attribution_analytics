NAME = "last_touch"
DESCRIPTION = "100% of credit to the latest eligible touch at or before conversion"


def weights(tss, order_dt):
    return [0.0] * (len(tss) - 1) + [1.0]
