# Assumptions and Limitations

This document records the assumptions used to generate and analyse the synthetic marketing dataset. These are implementation choices where the assignment does not prescribe a specific value or behaviour.

## 1. Data scope and time

- All campaign, contact, touchpoint, lead, opportunity, order and cost records are synthetic. The source manifest records no external data sources (`external_data: []`).
- The configured data cut-off is 2026-10-22.
- Touchpoints begin on 2026-01-01; campaigns may begin in December 2025 to provide campaign context for the generated journeys.

## 2. Revenue and costs

- Sales revenue is represented in USD and models one-off bookings. Renewals, refunds and churn are outside the current scope.
- Campaign costs can be recorded in multiple currencies. Monthly FX rates convert costs to USD for ROI calculations.
- FX rates are synthetic reference values with bounded variation; they are not intended to represent historical market rates.
- A campaign with no recorded cost does not receive a fabricated ROI. Its ROI is NULL and its cost status identifies the missing cost data.

## 3. Customer lifecycle

- A contact can have at most one lead.
- A lead can have at most one opportunity.
- A won opportunity produces one sales order in the valid baseline; labelled duplicate-order anomalies are added separately.
- A click touch creates one web session. Offline touches do not create web sessions.
- The project does not implement cross-device identity stitching. Missing identity remains missing rather than being inferred.

## 4. Identity and touchpoint eligibility

- The first touch for each contact is resolved and defines the contact creation timestamp.
- Some later touchpoints have missing identity identifiers. These are not eligible for contact-level attribution.
- `TOUCH-UNKNOWN-NNNNNN` is used when a touchpoint has no known contact ID; this is a documented exception to the normal contact-based touchpoint ID pattern.
- Only eligible, resolved and engaged touch types receive attribution credit. Impressions and mail deliveries do not receive credit.

## 5. Attribution assumptions

- The default lookback window is 120 days before the order timestamp, including the order timestamp and excluding later touches.
- First-touch, last-touch, linear, time-decay and position-based models are compared.
- Time-decay uses a seven-day half-life.
- Position-based attribution uses 40% for the first touch, 40% for the last touch and 20% for middle touches. The implementation handles one- and two-touch journeys as documented in `business_rules.md`.
- The 120-day window is shorter than some generated sales cycles. Consequently, a portion of revenue has no eligible touch and is reported as unattributed rather than hidden.

## 6. Synthetic campaign quality and ROI

- Campaign quality is a hidden synthetic variable used in generation and evaluation. It is stored separately under `data/ground_truth/` and is not an input feature for the anomaly detectors.
- Attribution credit is based on observed eligible interactions; it is not a causal estimate of incremental marketing impact.
- Owned channels can show high ROI because their generated costs are intentionally low. These values should not be treated as real-world marketing benchmarks.
- Synthetic ROI and attribution results depend on the configured distributions, budgets, conversion rules and random seed.

## 7. Scale behaviour

At small scale settings, minimum record counts are applied so that the generator can still exercise the principal business rules and edge cases. Therefore, record counts at very small scales may not be an exact linear fraction of full-scale counts.

## 8. Limitations and possible extensions

- No real marketing platform, CRM or billing integration is included.
- No causal incrementality or holdout experiment is implemented.
- Cross-device identity resolution is not implemented.
- Refunds, renewals and customer churn are outside the current data model.
- Further work could add holdout-based incrementality, Markov or Shapley attribution, identity-resolution confidence scoring and richer revenue lifecycle events.
