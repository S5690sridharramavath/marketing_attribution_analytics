# Business Rules

This document describes the rules used to generate customer journeys, conversion events, financial records and attribution results. Values described here are synthetic project assumptions, not external business benchmarks.

## 1. Generation order

The pipeline creates parent/master records before dependent records:

1. Channel and audience reference data.
2. Campaigns, campaign-audience relationships and campaign status history.
3. Creatives.
4. Contacts and contact-audience relationships.
5. Touchpoints and web sessions.
6. Leads and lead status history.
7. Opportunities and opportunity stage history.
8. Sales orders.
9. Campaign cost records and FX rates.
10. Labelled anomaly cases.
11. Attribution results and analytical reports.

The generator modules are under `src/generators/`. Anomalies are injected after the valid baseline has been generated. The order in which random values are consumed is part of reproducibility, so changing generation order can change the output even when the seed remains the same.

## 2. Customer journeys and touchpoints

- Each contact receives at least one touchpoint. Remaining touchpoints are distributed using a generated intent score and deterministic rounding so the full-scale run reaches the configured touchpoint count.
- Touchpoint dates are generated within the contact journey window.
- Campaigns are selected from campaigns active on the touchpoint date. Selection is weighted by campaign budget and receives an additional weight when the campaign targets the contact's audience.
- The selected campaign determines the touchpoint's channel.
- Offline channels, such as events and direct mail, create offline touchpoints and do not create web sessions.
- Each click touchpoint creates exactly one web session.
- Some later touchpoints intentionally have missing identity. The first touchpoint for a contact is resolved.
- Session identity evidence can include an email click identifier, a returning-user login, a form submission or no evidence for an anonymous session.

## 3. Lead generation

A contact's engagement score is calculated from resolved engaged touchpoints, using the touch-type weights configured in the generator:

| Touch type | Weight |
|---|---:|
| Click | 3 |
| Email open | 1 |
| Webinar attendance | 5 |
| Event attendance | 6 |
| Mail response | 4 |
| Impression | 0 |
| Mail delivered | 0 |

The lead score also reflects the synthetic campaign-quality value. The top 40% of eligible contacts become leads in the full-scale configuration. A lead is created when the running score first reaches the applicable threshold, with a generated delay after the creating touchpoint. The lead stores the creating touchpoint for traceability.

## 4. Opportunity and win generation

- Leads are ranked using final qualification score and segment fit.
- Segment-fit multipliers are SMB 0.8, MID 1.0 and ENT 1.2.
- The highest-ranked leads are selected for opportunities according to the configured target count.
- Opportunity creation delay and sales-cycle length vary by qualification and segment.
- Opportunities whose sales cycle extends beyond the configured data cut-off remain open.
- Closed opportunities receive a win score based on qualification percentile, segment fit and bounded jitter. The configured top share wins; the remainder are lost.
- Synthetic deal amounts use segment ACV assumptions (SMB $5,000; MID $18,000; ENT $60,000), a log-normal variation factor and rounding.

## 5. Orders, costs and FX

- Each won opportunity produces one baseline sales order.
- The order amount equals the opportunity amount and is denominated in USD.
- Campaign costs are recorded in the campaign's currency and include production and media cost records.
- Monthly synthetic FX rates provide conversion to USD for ROI calculations.
- Labelled anomaly cases may introduce duplicate orders, missing costs or inconsistent cost currencies after baseline generation.

## 6. Lifecycle history

Lifecycle changes are recorded as events rather than silently overwriting history:

- Campaign: planned -> active -> completed.
- Lead: new -> mql -> converted, nurturing or disqualified.
- Opportunity: qualification -> proposal -> negotiation -> closed_won or closed_lost.

The current status or stage on each parent record must agree with its latest lifecycle event. Validation checks this consistency.

## 7. Attribution rules

A touchpoint is eligible when it:

- Has a resolved contact identity.
- Is an engaged touch type.
- Occurs within the configured lookback period before or at the order timestamp.

The default lookback period is 120 days. Touchpoints after conversion are not eligible in the clean attribution calculation.

| Model | Credit allocation |
|---|---|
| First-touch | 100% to the earliest eligible touch. |
| Last-touch | 100% to the latest eligible touch. |
| Linear | Equal credit across eligible touches. |
| Time-decay | Weight is `0.5 ** (age_days / 7)`, then normalised. |
| Position-based | 40% first, 40% last and 20% distributed across middle touches. One touch receives 100%; two touches are split 50/50. |

Credits are allocated in integer cents using a largest-remainder approach so that the credits for each order/model reconcile exactly to the order amount. If no touch is eligible, one explicit `unattributed_no_eligible_touch` result receives the full amount.

## 8. ROI and reporting variants

The ROI calculation is:

`ROI = (attributed_revenue_usd - cost_usd) / cost_usd`

ROI is calculated by campaign, attribution model and evaluation period. Costs are converted using the monthly FX reference table. Where no cost is available, ROI is NULL and the cost status identifies missing cost data.

The project reports raw and clean analytical variants. The clean variant applies the documented anomaly-handling decisions, including duplicate-order removal, strict conversion-time eligibility and campaign-currency handling. These are analytical correction rules for the synthetic scenarios, not a claim that every real-world exception can be resolved automatically.

## 9. Chronological evaluation periods

Orders are assigned to chronological train, validation and test periods using order timestamps. The intended split is 60% train, 20% validation and 20% test, with contiguous, non-overlapping periods. The evaluation period is stored with attribution results.

## 10. Injected anomaly scenarios

Ground-truth labels are stored separately under `data/ground_truth/`.

| Anomaly | Injection concept | Clean-analysis handling |
|---|---|---|
| Revenue counted more than once | A billing replay creates a duplicate order for an opportunity. | Keep the earliest order for the opportunity. |
| Touchpoint after conversion attributed | A deliberately incorrect attribution window admits post-conversion touches in the raw case. | Recalculate using the strict conversion-time window. |
| Spend currency mismatch | A cost record's currency differs from its campaign currency. | Apply the documented campaign-currency correction for the clean comparison. |
| Campaign costs omitted | A completed campaign has budget but no cost records. | Flag missing cost data; do not invent ROI. |
| Anonymous session linked without evidence | An anonymous session is assigned a contact despite evidence being `none`. | Do not treat the unsupported identity link as valid. |
| Missing identifier | A touchpoint has no contact identity. | Exclude it from resolved-contact attribution; revenue may remain unattributed. |

The anomaly detector operates on the generated input data. Ground-truth labels are used afterward to evaluate detection precision and recall.
