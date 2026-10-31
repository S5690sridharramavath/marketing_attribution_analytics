"""Reference constants for the generators (channels, segments, weights)."""
import bisect

FMT = "%Y-%m-%dT%H:%M:%S"
iso = lambda d: d.strftime(FMT)

# id, name, offline, touch_weight, touch-type mix, cost_model, avg budget USD, campaign share, always_on
CHANNELS = [
 ("CH-01", "paid_search",    0, 0.16, {"click": .85, "impression": .15}, "CPC",      180_000, 0.13, False),
 ("CH-02", "paid_social",    0, 0.15, {"click": .35, "impression": .65}, "CPM",      150_000, 0.13, False),
 ("CH-03", "email",          0, 0.17, {"email_open": .6, "click": .4},   "flat",      30_000, 0.14, False),
 ("CH-04", "display",        0, 0.10, {"impression": .85, "click": .15}, "CPM",      110_000, 0.09, False),
 ("CH-05", "affiliate",      0, 0.05, {"click": 1.0},                    "CPA",       60_000, 0.06, False),
 ("CH-06", "organic_search", 0, 0.12, {"click": 1.0},                    "owned",     35_000, 0.07, True),
 ("CH-07", "direct",         0, 0.06, {"click": 1.0},                    "owned",     15_000, 0.03, True),
 ("CH-08", "referral",       0, 0.05, {"click": 1.0},                    "owned",     25_000, 0.04, True),
 ("CH-09", "events",         1, 0.03, {"event_attendance": 1.0},         "flat",     300_000, 0.06, False),
 ("CH-10", "direct_mail",    1, 0.04, {"mail_delivered": .7, "mail_response": .3}, "per_piece", 100_000, 0.07, False),
 ("CH-11", "webinar",        0, 0.07, {"webinar_attendance": 1.0},       "flat",      45_000, 0.18, False),
]
FX_BASE = {"USD": 1.0, "EUR": 1.09, "GBP": 1.27, "INR": 0.012}
CUR_W = [0.70, 0.15, 0.05, 0.10]
REGIONS = ["NA", "EMEA", "APAC", "LATAM", "IN"]
SEGMENTS = ["SMB", "MID", "ENT"]
INTERESTS = ["analytics", "automation", "security"]
SEG_W, REG_W = [0.55, 0.33, 0.12], [0.35, 0.25, 0.15, 0.10, 0.15]
SEG_INTENT = {"SMB": 0.8, "MID": 1.0, "ENT": 1.3}
SEG_FIT = {"SMB": 0.8, "MID": 1.0, "ENT": 1.2}
SEG_FIT_NORM = {"SMB": 0.0, "MID": 0.5, "ENT": 1.0}
SEG_ACV = {"SMB": 5_000, "MID": 18_000, "ENT": 60_000}
SEG_CYCLE = {"SMB": (14, 45), "MID": (30, 90), "ENT": (60, 150)}
ENG_W = {"click": 3.0, "email_open": 1.0, "event_attendance": 6.0, "webinar_attendance": 5.0, "mail_response": 4.0}
FORMATS = {"paid_search": ["text_ad"], "paid_social": ["banner", "video"], "email": ["email_template"],
           "display": ["banner", "video"], "affiliate": ["banner", "landing_page"], "organic_search": ["landing_page"],
           "direct": ["landing_page"], "referral": ["landing_page"], "events": ["slide_deck", "flyer"],
           "direct_mail": ["flyer"], "webinar": ["slide_deck", "landing_page"]}
THEMES = ["spring_launch", "product_demo", "retargeting", "brand_push", "pipeline_push", "partner_program",
          "upsell", "trial_nurture", "conference", "always_on"]


def _cum(weights):
    t, out = 0.0, []
    for w in weights:
        t += w
        out.append(t)
    return out


def _pick(rng, cum, items):
    return items[bisect.bisect(cum, rng.random() * cum[-1])]


