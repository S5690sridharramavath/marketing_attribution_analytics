-- Auto-generated from attrgen/schema.py (SQLite dialect; portable to Postgres with minor edits).

CREATE TABLE channel (
  channel_id TEXT NOT NULL,
  channel_name TEXT NOT NULL,
  channel_type TEXT NOT NULL,
  is_offline INTEGER NOT NULL,
  cost_model TEXT NOT NULL,
  PRIMARY KEY (channel_id)
);

CREATE TABLE audience (
  audience_id TEXT NOT NULL,
  audience_name TEXT NOT NULL,
  region TEXT NOT NULL,
  segment TEXT NOT NULL,
  interest TEXT NOT NULL,
  PRIMARY KEY (audience_id)
);

CREATE TABLE campaign (
  campaign_id TEXT NOT NULL,
  campaign_name TEXT NOT NULL,
  channel_id TEXT NOT NULL,
  objective TEXT NOT NULL,
  budget NUMERIC NOT NULL,
  currency TEXT NOT NULL,
  start_date TEXT NOT NULL,
  end_date TEXT NOT NULL,
  status TEXT NOT NULL,
  PRIMARY KEY (campaign_id),
  FOREIGN KEY (channel_id) REFERENCES channel(channel_id)
);

CREATE TABLE campaign_audience (
  campaign_id TEXT NOT NULL,
  audience_id TEXT NOT NULL,
  effective_from TEXT NOT NULL,
  effective_to TEXT NOT NULL,
  PRIMARY KEY (campaign_id, audience_id),
  FOREIGN KEY (campaign_id) REFERENCES campaign(campaign_id),
  FOREIGN KEY (audience_id) REFERENCES audience(audience_id)
);

CREATE TABLE campaign_status_event (
  event_id TEXT NOT NULL,
  campaign_id TEXT NOT NULL,
  status TEXT NOT NULL,
  event_ts TEXT NOT NULL,
  PRIMARY KEY (event_id),
  FOREIGN KEY (campaign_id) REFERENCES campaign(campaign_id)
);

CREATE TABLE creative (
  creative_id TEXT NOT NULL,
  campaign_id TEXT NOT NULL,
  creative_name TEXT NOT NULL,
  format TEXT NOT NULL,
  created_date TEXT NOT NULL,
  PRIMARY KEY (creative_id),
  FOREIGN KEY (campaign_id) REFERENCES campaign(campaign_id)
);

CREATE TABLE contact (
  contact_id TEXT NOT NULL,
  segment TEXT NOT NULL,
  region TEXT NOT NULL,
  interest TEXT NOT NULL,
  primary_audience_id TEXT NOT NULL,
  email_opt_in INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  lifecycle_state TEXT NOT NULL,
  PRIMARY KEY (contact_id),
  FOREIGN KEY (primary_audience_id) REFERENCES audience(audience_id)
);

CREATE TABLE contact_audience (
  contact_id TEXT NOT NULL,
  audience_id TEXT NOT NULL,
  effective_from TEXT NOT NULL,
  effective_to TEXT,
  PRIMARY KEY (contact_id, audience_id),
  FOREIGN KEY (contact_id) REFERENCES contact(contact_id),
  FOREIGN KEY (audience_id) REFERENCES audience(audience_id)
);

CREATE TABLE web_session (
  session_id TEXT NOT NULL,
  visitor_id TEXT NOT NULL,
  contact_id TEXT,
  started_at TEXT NOT NULL,
  duration_sec INTEGER NOT NULL,
  pages_viewed INTEGER NOT NULL,
  landing_campaign_id TEXT NOT NULL,
  identity_link_evidence TEXT NOT NULL,
  PRIMARY KEY (session_id),
  FOREIGN KEY (contact_id) REFERENCES contact(contact_id),
  FOREIGN KEY (landing_campaign_id) REFERENCES campaign(campaign_id)
);

CREATE TABLE touchpoint (
  touchpoint_id TEXT NOT NULL,
  contact_id TEXT,
  campaign_id TEXT NOT NULL,
  creative_id TEXT NOT NULL,
  channel_id TEXT NOT NULL,
  touch_ts TEXT NOT NULL,
  touch_type TEXT NOT NULL,
  is_offline INTEGER NOT NULL,
  session_id TEXT,
  identity_link_status TEXT NOT NULL,
  PRIMARY KEY (touchpoint_id),
  FOREIGN KEY (contact_id) REFERENCES contact(contact_id),
  FOREIGN KEY (campaign_id) REFERENCES campaign(campaign_id),
  FOREIGN KEY (creative_id) REFERENCES creative(creative_id),
  FOREIGN KEY (channel_id) REFERENCES channel(channel_id),
  FOREIGN KEY (session_id) REFERENCES web_session(session_id)
);

CREATE TABLE lead (
  lead_id TEXT NOT NULL,
  contact_id TEXT NOT NULL,
  session_id TEXT,
  creating_touchpoint_id TEXT NOT NULL,
  crm_source_campaign_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  lead_score NUMERIC NOT NULL,
  current_status TEXT NOT NULL,
  PRIMARY KEY (lead_id),
  FOREIGN KEY (contact_id) REFERENCES contact(contact_id),
  FOREIGN KEY (session_id) REFERENCES web_session(session_id),
  FOREIGN KEY (creating_touchpoint_id) REFERENCES touchpoint(touchpoint_id),
  FOREIGN KEY (crm_source_campaign_id) REFERENCES campaign(campaign_id)
);

CREATE TABLE lead_status_event (
  event_id TEXT NOT NULL,
  lead_id TEXT NOT NULL,
  from_status TEXT,
  to_status TEXT NOT NULL,
  event_ts TEXT NOT NULL,
  PRIMARY KEY (event_id),
  FOREIGN KEY (lead_id) REFERENCES lead(lead_id)
);

CREATE TABLE opportunity (
  opportunity_id TEXT NOT NULL,
  lead_id TEXT NOT NULL,
  contact_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  qualification_score NUMERIC NOT NULL,
  amount NUMERIC NOT NULL,
  currency TEXT NOT NULL,
  current_stage TEXT NOT NULL,
  status TEXT NOT NULL,
  close_ts TEXT,
  PRIMARY KEY (opportunity_id),
  FOREIGN KEY (lead_id) REFERENCES lead(lead_id),
  FOREIGN KEY (contact_id) REFERENCES contact(contact_id)
);

CREATE TABLE opportunity_stage_event (
  event_id TEXT NOT NULL,
  opportunity_id TEXT NOT NULL,
  from_stage TEXT,
  to_stage TEXT NOT NULL,
  event_ts TEXT NOT NULL,
  PRIMARY KEY (event_id),
  FOREIGN KEY (opportunity_id) REFERENCES opportunity(opportunity_id)
);

CREATE TABLE sales_order (
  order_id TEXT NOT NULL,
  opportunity_id TEXT NOT NULL,
  contact_id TEXT NOT NULL,
  order_ts TEXT NOT NULL,
  amount NUMERIC NOT NULL,
  currency TEXT NOT NULL,
  order_status TEXT NOT NULL,
  source_system TEXT NOT NULL,
  PRIMARY KEY (order_id),
  FOREIGN KEY (opportunity_id) REFERENCES opportunity(opportunity_id),
  FOREIGN KEY (contact_id) REFERENCES contact(contact_id)
);

CREATE TABLE cost_record (
  cost_id TEXT NOT NULL,
  campaign_id TEXT NOT NULL,
  cost_date TEXT NOT NULL,
  amount NUMERIC NOT NULL,
  currency TEXT NOT NULL,
  cost_type TEXT NOT NULL,
  PRIMARY KEY (cost_id),
  FOREIGN KEY (campaign_id) REFERENCES campaign(campaign_id)
);

CREATE TABLE fx_rate (
  fx_rate_id TEXT NOT NULL,
  currency TEXT NOT NULL,
  rate_month TEXT NOT NULL,
  rate_to_usd NUMERIC NOT NULL,
  PRIMARY KEY (fx_rate_id)
);

CREATE TABLE evaluation_period (
  period_id TEXT NOT NULL,
  start_ts TEXT NOT NULL,
  end_ts TEXT NOT NULL,
  split_rule TEXT NOT NULL,
  PRIMARY KEY (period_id)
);

CREATE TABLE attribution_model (
  model_id TEXT NOT NULL,
  rule_description TEXT NOT NULL,
  lookback_days INTEGER NOT NULL,
  eligible_touch_types TEXT NOT NULL,
  PRIMARY KEY (model_id)
);

CREATE TABLE attribution_result (
  attribution_id TEXT NOT NULL,
  order_id TEXT NOT NULL,
  opportunity_id TEXT NOT NULL,
  touchpoint_id TEXT,
  campaign_id TEXT,
  model_id TEXT NOT NULL,
  credit_weight NUMERIC NOT NULL,
  attributed_revenue NUMERIC NOT NULL,
  evaluation_period TEXT NOT NULL,
  attribution_status TEXT NOT NULL,
  PRIMARY KEY (attribution_id),
  FOREIGN KEY (order_id) REFERENCES sales_order(order_id),
  FOREIGN KEY (opportunity_id) REFERENCES opportunity(opportunity_id),
  FOREIGN KEY (touchpoint_id) REFERENCES touchpoint(touchpoint_id),
  FOREIGN KEY (campaign_id) REFERENCES campaign(campaign_id),
  FOREIGN KEY (model_id) REFERENCES attribution_model(model_id),
  FOREIGN KEY (evaluation_period) REFERENCES evaluation_period(period_id)
);
