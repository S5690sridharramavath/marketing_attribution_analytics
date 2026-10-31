"""Single source of truth: data dictionary, enums, FKs, ID formats. Drives DDL, docs and validation."""

def _f(name, typ, req, rule="", unit="", uniq=False, desc=""):
    return dict(name=name, type=typ, required=req, rule=rule, unit=unit, unique=uniq, desc=desc)

CURRENCIES = ["USD", "EUR", "GBP", "INR"]
ENUMS = {
    ("channel", "channel_type"): ["digital", "offline"],
    ("channel", "cost_model"): ["CPC", "CPM", "CPA", "flat", "per_piece", "owned"],
    ("campaign", "objective"): ["lead_gen", "pipeline", "brand"],
    ("campaign", "currency"): CURRENCIES,
    ("campaign", "status"): ["planned", "active", "completed"],
    ("campaign_status_event", "status"): ["planned", "active", "completed"],
    ("creative", "format"): ["banner", "video", "text_ad", "email_template", "landing_page", "flyer", "slide_deck"],
    ("audience", "segment"): ["SMB", "MID", "ENT"],
    ("contact", "segment"): ["SMB", "MID", "ENT"],
    ("contact", "lifecycle_state"): ["prospect", "lead", "opportunity", "customer"],
    ("touchpoint", "touch_type"): ["impression", "click", "email_open", "event_attendance",
                                   "mail_delivered", "mail_response", "webinar_attendance"],
    ("touchpoint", "identity_link_status"): ["resolved", "missing"],
    ("web_session", "identity_link_evidence"): ["email_click_id", "login", "form_submit", "none"],
    ("lead", "current_status"): ["new", "mql", "converted", "nurturing", "disqualified"],
    ("opportunity", "current_stage"): ["qualification", "proposal", "negotiation", "closed_won", "closed_lost"],
    ("opportunity", "status"): ["open", "won", "lost"],
    ("sales_order", "order_status"): ["booked"],
    ("sales_order", "source_system"): ["crm", "billing"],
    ("sales_order", "currency"): ["USD"],
    ("cost_record", "cost_type"): ["media", "production"],
    ("cost_record", "currency"): CURRENCIES,
    ("fx_rate", "currency"): CURRENCIES,
    ("attribution_result", "model_id"): ["first_touch", "last_touch", "linear", "time_decay", "position_based"],
    ("attribution_result", "evaluation_period"): ["train", "validation", "test"],
    ("attribution_result", "attribution_status"): ["attributed", "unattributed_no_eligible_touch"],
}

LEAD_TRANSITIONS = {None: {"new"}, "new": {"mql"}, "mql": {"converted", "nurturing", "disqualified"}}
OPP_TRANSITIONS = {None: {"qualification"}, "qualification": {"proposal", "closed_lost"},
                   "proposal": {"negotiation", "closed_lost"}, "negotiation": {"closed_won", "closed_lost"}}
CAMPAIGN_TRANSITIONS = {None: {"planned"}, "planned": {"active"}, "active": {"completed"}}

ID_PATTERNS = {
    "channel": ("channel_id", r"^CH-\d{2}$"),
    "audience": ("audience_id", r"^AUD-\d{4}$"),
    "campaign": ("campaign_id", r"^CMP-2026-\d{6}$"),
    "campaign_status_event": ("event_id", r"^CMPEV-\d{6}$"),
    "creative": ("creative_id", r"^CRE-\d{6}$"),
    "contact": ("contact_id", r"^CON-\d{6}$"),
    "touchpoint": ("touchpoint_id", r"^TOUCH-(CON-\d{6}|UNKNOWN)-\d{6}$"),
    "web_session": ("session_id", r"^SES-2026-\d{6}$"),
    "lead": ("lead_id", r"^LEAD-2026-\d{6}$"),
    "lead_status_event": ("event_id", r"^LEADEV-\d{6}$"),
    "opportunity": ("opportunity_id", r"^OPP-2026-\d{6}$"),
    "opportunity_stage_event": ("event_id", r"^OPPEV-\d{6}$"),
    "sales_order": ("order_id", r"^ORD-2026-\d{6}$"),
    "cost_record": ("cost_id", r"^COST-2026-\d{6}$"),
    "attribution_result": ("attribution_id", r"^ATTR-2026-\d{7}$"),
}

SCHEMA = {
 "channel": dict(entity="Channel", pk=["channel_id"], fields=[
   _f("channel_id","text",True,"CH-NN","",True,"Marketing channel key"),
   _f("channel_name","text",True,"free text","",True,"e.g. paid_search"),
   _f("channel_type","text",True,"digital|offline","",False,"Offline channels never create web sessions"),
   _f("is_offline","int",True,"0|1 (derived from channel_type)","flag",False,"Offline-touch marker"),
   _f("cost_model","text",True,"CPC|CPM|CPA|flat|per_piece|owned","",False,"How spend is normally incurred")]),
 "audience": dict(entity="Audience", pk=["audience_id"], fields=[
   _f("audience_id","text",True,"AUD-NNNN","",True,"Audience key"),
   _f("audience_name","text",True,"region-segment-interest","",True,""),
   _f("region","text",True,"NA|EMEA|APAC|LATAM|IN","",False,""),
   _f("segment","text",True,"SMB|MID|ENT","",False,""),
   _f("interest","text",True,"analytics|automation|security","",False,"")]),
 "campaign": dict(entity="Campaign", pk=["campaign_id"], fields=[
   _f("campaign_id","text",True,"CMP-2026-NNNNNN","",True,"Immutable key"),
   _f("campaign_name","text",True,"free text","",False,""),
   _f("channel_id","text",True,"FK channel","",False,"N:1 to Channel"),
   _f("objective","text",True,"lead_gen|pipeline|brand","",False,""),
   _f("budget","decimal",True,">= 0","campaign currency",False,"Planned spend in the campaign's own currency"),
   _f("currency","text",True,"USD|EUR|GBP|INR","ISO 4217",False,"All cost records of the campaign should use this currency"),
   _f("start_date","date",True,"YYYY-MM-DD","",False,"Effective-from"),
   _f("end_date","date",True,">= start_date","",False,"Effective-to (always-on campaigns end 2026-12-31)"),
   _f("status","text",True,"planned|active|completed","",False,"Derived from latest campaign_status_event")]),
 "campaign_audience": dict(entity="CampaignAudience (bridge, N:M)", pk=["campaign_id","audience_id"], fields=[
   _f("campaign_id","text",True,"FK campaign","",False,""),
   _f("audience_id","text",True,"FK audience","",False,""),
   _f("effective_from","date",True,"= campaign start_date","",False,""),
   _f("effective_to","date",True,"= campaign end_date","",False,"")]),
 "campaign_status_event": dict(entity="CampaignStatusEvent (history)", pk=["event_id"], fields=[
   _f("event_id","text",True,"CMPEV-NNNNNN","",True,""),
   _f("campaign_id","text",True,"FK campaign","",False,""),
   _f("status","text",True,"planned|active|completed","",False,"Allowed: planned->active->completed"),
   _f("event_ts","datetime",True,"ISO-8601 UTC, <= as-of","",False,"")]),
 "creative": dict(entity="Creative", pk=["creative_id"], fields=[
   _f("creative_id","text",True,"CRE-NNNNNN","",True,""),
   _f("campaign_id","text",True,"FK campaign","",False,"N:1"),
   _f("creative_name","text",True,"","",False,""),
   _f("format","text",True,"banner|video|text_ad|email_template|landing_page|flyer|slide_deck","",False,""),
   _f("created_date","date",True,"< campaign start_date","",False,"")]),
 "contact": dict(entity="Contact", pk=["contact_id"], fields=[
   _f("contact_id","text",True,"CON-NNNNNN","",True,""),
   _f("segment","text",True,"SMB|MID|ENT","",False,""),
   _f("region","text",True,"NA|EMEA|APAC|LATAM|IN","",False,""),
   _f("interest","text",True,"analytics|automation|security","",False,""),
   _f("primary_audience_id","text",True,"FK audience (derived from region+segment+interest)","",False,""),
   _f("email_opt_in","int",True,"0|1","flag",False,""),
   _f("created_at","datetime",True,"= first resolved touch","UTC",False,"Derived from source records"),
   _f("lifecycle_state","text",True,"prospect|lead|opportunity|customer","",False,"Derived from lead/opportunity/order records")]),
 "contact_audience": dict(entity="ContactAudience (bridge, N:M, effective dated)", pk=["contact_id","audience_id"], fields=[
   _f("contact_id","text",True,"FK contact","",False,""),
   _f("audience_id","text",True,"FK audience","",False,""),
   _f("effective_from","date",True,">= contact created date","",False,""),
   _f("effective_to","date",False,"null = still member","",False,"")]),
 "touchpoint": dict(entity="Touchpoint", pk=["touchpoint_id"], fields=[
   _f("touchpoint_id","text",True,"TOUCH-<contact-id>-NNNNNN (TOUCH-UNKNOWN-NNNNNN when identity missing)","",True,"Counter is per contact, chronological"),
   _f("contact_id","text",False,"FK contact; NULL = missing identifier","",False,"Optional relationship (N:1)"),
   _f("campaign_id","text",True,"FK campaign; touch_ts within campaign dates","",False,""),
   _f("creative_id","text",True,"FK creative (must belong to campaign)","",False,""),
   _f("channel_id","text",True,"FK channel (must equal campaign channel)","",False,""),
   _f("touch_ts","datetime",True,"<= as-of","UTC",False,""),
   _f("touch_type","text",True,"impression|click|email_open|event_attendance|mail_delivered|mail_response|webinar_attendance","",False,""),
   _f("is_offline","int",True,"0|1 (= channel.is_offline)","flag",False,""),
   _f("session_id","text",False,"FK web_session; only for click touches","",False,"1:0..1"),
   _f("identity_link_status","text",True,"resolved|missing","",False,"missing <=> contact_id NULL")]),
 "web_session": dict(entity="WebSession", pk=["session_id"], fields=[
   _f("session_id","text",True,"SES-2026-NNNNNN","",True,""),
   _f("visitor_id","text",True,"VIS-NNNNNN | VIS-ANONNNNNN","",False,"Cookie-level id"),
   _f("contact_id","text",False,"FK contact; requires evidence != none","",False,"Optional"),
   _f("started_at","datetime",True,"= click touch_ts","UTC",False,""),
   _f("duration_sec","int",True,"> 0","seconds",False,""),
   _f("pages_viewed","int",True,">= 1 (= max(1, round(duration/90)))","pages",False,"Derived"),
   _f("landing_campaign_id","text",True,"FK campaign","",False,""),
   _f("identity_link_evidence","text",True,"email_click_id|login|form_submit|none","",False,"Why the session is tied to a contact")]),
 "lead": dict(entity="Lead", pk=["lead_id"], fields=[
   _f("lead_id","text",True,"LEAD-2026-NNNNNN","",True,""),
   _f("contact_id","text",True,"FK contact","",False,"N:1 (a contact has at most one lead)"),
   _f("session_id","text",False,"FK web_session (null for offline-created leads)","",False,""),
   _f("creating_touchpoint_id","text",True,"FK touchpoint that crossed the lead-score threshold","",False,"Traceability"),
   _f("crm_source_campaign_id","text",True,"FK campaign of the creating touch","",False,"CRM 'lead source' field"),
   _f("created_at","datetime",True,"> creating touch ts","UTC",False,""),
   _f("lead_score","decimal",True,">= threshold","points",False,"Cumulative engaged-touch score at creation"),
   _f("current_status","text",True,"new|mql|converted|nurturing|disqualified","",False,"Derived from latest lead_status_event")]),
 "lead_status_event": dict(entity="LeadStatusEvent (history)", pk=["event_id"], fields=[
   _f("event_id","text",True,"LEADEV-NNNNNN","",True,""),
   _f("lead_id","text",True,"FK lead","",False,""),
   _f("from_status","text",False,"null for first event","",False,""),
   _f("to_status","text",True,"new|mql|converted|nurturing|disqualified","",False,"new->mql->(converted|nurturing|disqualified)"),
   _f("event_ts","datetime",True,"non-decreasing per lead","UTC",False,"")]),
 "opportunity": dict(entity="Opportunity", pk=["opportunity_id"], fields=[
   _f("opportunity_id","text",True,"OPP-2026-NNNNNN","",True,""),
   _f("lead_id","text",True,"FK lead","",True,"1:1 with lead"),
   _f("contact_id","text",True,"FK contact (= lead.contact_id)","",False,""),
   _f("created_at","datetime",True,">= lead.created_at","UTC",False,""),
   _f("qualification_score","decimal",True,"lead final score x segment fit","points",False,"Drives win rule"),
   _f("amount","decimal",True,"> 0","USD",False,"Expected / closed amount"),
   _f("currency","text",True,"USD","ISO 4217",False,""),
   _f("current_stage","text",True,"qualification|proposal|negotiation|closed_won|closed_lost","",False,"Derived from latest stage event"),
   _f("status","text",True,"open|won|lost","",False,"Derived from current_stage"),
   _f("close_ts","datetime",False,"set only when closed","UTC",False,"")]),
 "opportunity_stage_event": dict(entity="OpportunityStageEvent (history)", pk=["event_id"], fields=[
   _f("event_id","text",True,"OPPEV-NNNNNN","",True,""),
   _f("opportunity_id","text",True,"FK opportunity","",False,""),
   _f("from_stage","text",False,"null for first event","",False,""),
   _f("to_stage","text",True,"stage enum","",False,"qualification->proposal->negotiation->closed_*"),
   _f("event_ts","datetime",True,"non-decreasing per opportunity","UTC",False,"")]),
 "sales_order": dict(entity="Order", pk=["order_id"], fields=[
   _f("order_id","text",True,"ORD-2026-NNNNNN","",True,""),
   _f("opportunity_id","text",True,"FK opportunity (status=won)","",False,"Expected 1:1 with a won opportunity (duplicates are a labelled edge case)"),
   _f("contact_id","text",True,"FK contact","",False,""),
   _f("order_ts","datetime",True,">= opportunity.close_ts","UTC",False,""),
   _f("amount","decimal",True,"> 0; = opportunity.amount","USD",False,"Closed revenue"),
   _f("currency","text",True,"USD","ISO 4217",False,""),
   _f("order_status","text",True,"booked","",False,""),
   _f("source_system","text",True,"crm|billing","",False,"")]),
 "cost_record": dict(entity="CostRecord", pk=["cost_id"], fields=[
   _f("cost_id","text",True,"COST-2026-NNNNNN","",True,""),
   _f("campaign_id","text",True,"FK campaign","",False,"N:1"),
   _f("cost_date","date",True,"within campaign dates and <= as-of","",False,""),
   _f("amount","decimal",True,">= 0","stated currency",False,""),
   _f("currency","text",True,"USD|EUR|GBP|INR; should equal campaign.currency","ISO 4217",False,""),
   _f("cost_type","text",True,"media|production","",False,"")]),
 "fx_rate": dict(entity="FxRate (reference)", pk=["fx_rate_id"], fields=[
   _f("fx_rate_id","text",True,"FX-<CUR>-YYYY-MM","",True,""),
   _f("currency","text",True,"USD|EUR|GBP|INR","ISO 4217",False,""),
   _f("rate_month","text",True,"YYYY-MM","",False,""),
   _f("rate_to_usd","decimal",True,"> 0","USD per 1 unit",False,"")]),
 "evaluation_period": dict(entity="EvaluationPeriod (chronological split)", pk=["period_id"], fields=[
   _f("period_id","text",True,"train|validation|test","",True,""),
   _f("start_ts","datetime",True,"","UTC",False,"Inclusive"),
   _f("end_ts","datetime",True,"","UTC",False,"Exclusive (next period start)"),
   _f("split_rule","text",True,"","",False,"Order timestamp quantiles 60% / 20% / 20%")]),
 "attribution_model": dict(entity="AttributionModel (explicit rules)", pk=["model_id"], fields=[
   _f("model_id","text",True,"enum","",True,""),
   _f("rule_description","text",True,"","",False,""),
   _f("lookback_days","int",True,"> 0","days",False,""),
   _f("eligible_touch_types","text",True,"|-separated","",False,"")]),
 "attribution_result": dict(entity="AttributionResult", pk=["attribution_id"], fields=[
   _f("attribution_id","text",True,"ATTR-2026-NNNNNNN","",True,""),
   _f("order_id","text",True,"FK sales_order","",False,""),
   _f("opportunity_id","text",True,"FK opportunity","",False,""),
   _f("touchpoint_id","text",False,"FK touchpoint; NULL when unattributed","",False,"Traceability to the credited touch"),
   _f("campaign_id","text",False,"FK campaign; NULL when unattributed","",False,""),
   _f("model_id","text",True,"FK attribution_model","",False,""),
   _f("credit_weight","decimal",True,"0..1","fraction",False,"credited cents / order cents"),
   _f("attributed_revenue","decimal",True,">= 0; credits per (order,model) sum to order amount","USD",False,""),
   _f("evaluation_period","text",True,"FK evaluation_period","",False,"By order_ts"),
   _f("attribution_status","text",True,"attributed|unattributed_no_eligible_touch","",False,"")]),
}

# (child_table, child_col, parent_table, parent_col, optional)
FKS = [
 ("campaign","channel_id","channel","channel_id",False),
 ("campaign_audience","campaign_id","campaign","campaign_id",False),
 ("campaign_audience","audience_id","audience","audience_id",False),
 ("campaign_status_event","campaign_id","campaign","campaign_id",False),
 ("creative","campaign_id","campaign","campaign_id",False),
 ("contact","primary_audience_id","audience","audience_id",False),
 ("contact_audience","contact_id","contact","contact_id",False),
 ("contact_audience","audience_id","audience","audience_id",False),
 ("touchpoint","contact_id","contact","contact_id",True),
 ("touchpoint","campaign_id","campaign","campaign_id",False),
 ("touchpoint","creative_id","creative","creative_id",False),
 ("touchpoint","channel_id","channel","channel_id",False),
 ("touchpoint","session_id","web_session","session_id",True),
 ("web_session","contact_id","contact","contact_id",True),
 ("web_session","landing_campaign_id","campaign","campaign_id",False),
 ("lead","contact_id","contact","contact_id",False),
 ("lead","session_id","web_session","session_id",True),
 ("lead","creating_touchpoint_id","touchpoint","touchpoint_id",False),
 ("lead","crm_source_campaign_id","campaign","campaign_id",False),
 ("lead_status_event","lead_id","lead","lead_id",False),
 ("opportunity","lead_id","lead","lead_id",False),
 ("opportunity","contact_id","contact","contact_id",False),
 ("opportunity_stage_event","opportunity_id","opportunity","opportunity_id",False),
 ("sales_order","opportunity_id","opportunity","opportunity_id",False),
 ("sales_order","contact_id","contact","contact_id",False),
 ("cost_record","campaign_id","campaign","campaign_id",False),
 ("attribution_result","order_id","sales_order","order_id",False),
 ("attribution_result","opportunity_id","opportunity","opportunity_id",False),
 ("attribution_result","touchpoint_id","touchpoint","touchpoint_id",True),
 ("attribution_result","campaign_id","campaign","campaign_id",True),
 ("attribution_result","model_id","attribution_model","model_id",False),
 ("attribution_result","evaluation_period","evaluation_period","period_id",False),
]

# Parents before children. NOTE: touchpoint.session_id -> web_session and web_session has no FK to touchpoint,
# so web_session loads first; lead (-> touchpoint, web_session) loads after both.
TABLE_ORDER = ["channel","audience","campaign","campaign_audience","campaign_status_event","creative",
               "contact","contact_audience","web_session","touchpoint","lead","lead_status_event",
               "opportunity","opportunity_stage_event","sales_order","cost_record","fx_rate",
               "evaluation_period","attribution_model","attribution_result"]

def columns(table):
    return [f["name"] for f in SCHEMA[table]["fields"]]

def ddl():
    sql_t = {"text": "TEXT", "int": "INTEGER", "decimal": "NUMERIC", "datetime": "TEXT", "date": "TEXT"}
    out = ["-- Auto-generated from attrgen/schema.py (SQLite dialect; portable to Postgres with minor edits).", ""]
    for t in TABLE_ORDER:
        s = SCHEMA[t]
        lines = [f"  {f['name']} {sql_t[f['type']]}{' NOT NULL' if f['required'] else ''}" for f in s["fields"]]
        lines.append(f"  PRIMARY KEY ({', '.join(s['pk'])})")
        for (ct, cc, pt, pc, opt) in FKS:
            if ct == t:
                lines.append(f"  FOREIGN KEY ({cc}) REFERENCES {pt}({pc})")
        out.append(f"CREATE TABLE {t} (\n" + ",\n".join(lines) + "\n);\n")
    return "\n".join(out)


# ---------------------------------------------------------------- markdown rendering
import os as _os

_CARD = {"channel": "1 channel : N campaigns", "audience": "N:M with campaign and contact (bridges)",
         "campaign": "1 campaign : N creatives, touchpoints, cost records, status events",
         "contact": "1 contact : N touchpoints; 0..1 lead", "touchpoint": "N:1 contact (optional), N:1 campaign, N:1 creative, 0..1 session",
         "web_session": "1 session : 1 click touchpoint; 0..1 lead", "lead": "1 lead : 0..1 opportunity",
         "opportunity": "1 opportunity : 0..N orders (expected 1)", "sales_order": "1 order : N attribution results (per model x credited touch)"}


def write_data_dictionary(path):
    L = ["# Data dictionary", "", "_Generated from `src/models/data_dictionary.py` (single source of truth)._", "",
         "All timestamps are ISO-8601 UTC strings. Amount columns are decimals; `USD` unless the unit column says otherwise.", ""]
    for t in TABLE_ORDER:
        s = SCHEMA[t]
        L += [f"## {t}  _({s['entity']})_", "", f"Primary key: `{', '.join(s['pk'])}`" + (f" - Cardinality: {_CARD[t]}" if t in _CARD else ""), "",
              "| field | type | required | allowed values / validation rule | unit | unique | notes |", "|---|---|---|---|---|---|---|"]
        for f in s["fields"]:
            L.append(f"| `{f['name']}` | {f['type']} | {'yes' if f['required'] else 'no'} | {f['rule']} | {f['unit']} | {'yes' if f['unique'] else ''} | {f['desc']} |")
        fks = [x for x in FKS if x[0] == t]
        if fks:
            L += ["", "Foreign keys: " + "; ".join(f"`{c}` -> `{pt}.{pc}`{' (optional)' if o else ''}" for _, c, pt, pc, o in fks)]
        L.append("")
    _os.makedirs(_os.path.dirname(path) or ".", exist_ok=True)
    open(path, "w").write("\n".join(L))


# data/raw = tables produced by the generators; data/processed = tables derived by the attribution step
PROCESSED_TABLES = ["evaluation_period", "attribution_model", "attribution_result"]
RAW_TABLES = [t for t in TABLE_ORDER if t not in PROCESSED_TABLES]


def table_dir(t):
    return "processed" if t in PROCESSED_TABLES else "raw"
