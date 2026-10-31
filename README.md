# Marketing Attribution & ROI Analytics

**An end-to-end marketing analytics project for synthetic data generation, multi-touch attribution, ROI measurement, data quality validation and anomaly detection.**

## 1. Project Overview

Marketing teams use multiple channels and campaigns to attract customers, generate leads and drive revenue. Understanding which marketing interactions contribute to conversions is important for measuring campaign effectiveness and allocating budgets.

This project implements an end-to-end Marketing Attribution and ROI Analytics pipeline. It generates a reproducible synthetic marketing dataset, models customer interactions and conversion journeys, applies multiple attribution approaches, calculates campaign and channel ROI, and validates data quality through automated checks and anomaly detection.

The system is designed to demonstrate how marketing data can be generated, structured, validated and analysed in a consistent and reproducible way.

**Key capabilities:**

- Synthetic marketing data generation at configurable scales.
- Relational data modelling with primary and foreign key relationships.
- Customer journey and conversion lifecycle simulation.
- Five attribution models for revenue allocation.
- Campaign-level and channel-level ROI analysis.
- Controlled anomaly injection and independent detection.
- Automated data quality and reconciliation checks.
- Reproducibility verification using a fixed random seed.
- CSV, JSON and SQL data exports.
- Optional interactive Streamlit dashboard.

> **Data note:** All customer, campaign, touchpoint, opportunity and revenue records in this project are synthetic. No real customer or confidential business data is used.

## 2. Project Objectives

The main objectives are to:

1. Generate realistic, relational marketing datasets with configurable record volumes.
2. Represent customer journeys from marketing interactions through leads, opportunities and sales.
3. Compare different attribution models and their revenue allocation.
4. Calculate marketing ROI across campaigns, channels and evaluation periods.
5. Identify data quality issues that could affect attribution and financial reporting.
6. Validate data integrity, business rules and revenue reconciliation.
7. Ensure that generated datasets and analytical results are reproducible.

## 3. Technology Stack

| Area | Technologies |

 Programming language : Python 
 Data generation : Python standard library 
 Data processing : Python 
 Attribution modelling : Python 
 Data validation : Python 
 Testing | pytest 
 Data storage and export : CSV, JSON, SQL, SQLite 
 Dashboard | Streamlit, pandas 
 Version control | Git, GitHub 

The core generation, validation, attribution and reporting pipeline uses Python's standard library. Additional packages are used for automated tests and the optional dashboard.

## 4. Dataset Overview

The project generates a relational marketing dataset consisting of master data, customer interaction events, conversion records, financial records and attribution results.

### Full-scale dataset

The full-scale configuration uses the following record volumes:

| Entity | Records |

 Channels : 11 
 Audiences : 45 
 Campaigns : 500 
 Creatives : 1,190 
 Contacts : 50,000 
 Web sessions : 110,007 
 Touchpoints : 200,000 
 Leads : 20,000 
 Opportunities : 10,000
 Sales orders : 3,009 
 Cost records : 8,186 
 Attribution results : 57,276 

The generated dataset also contains campaign-audience relationships, contact-audience relationships, lifecycle events, FX rates, evaluation periods and attribution model reference data.

### Data entities

The main entities include:

- **Campaign:** Marketing campaign details, objectives, budgets, dates and channel relationships.
- **Channel:** Marketing channel information and cost models.
- **Creative:** Campaign-specific marketing assets.
- **Audience:** Target audience segments.
- **Contact:** Customer and prospect information.
- **Touchpoint:** Customer interactions with marketing campaigns.
- **Web Session:** Digital sessions associated with customer interactions.
- **Lead:** Qualified or potential customer records.
- **Opportunity:** Sales opportunities associated with leads.
- **Sales Order:** Revenue generated from won opportunities.
- **Cost Record:** Marketing expenditure associated with campaigns.
- **Attribution Result:** Revenue credit allocated to campaigns and touchpoints by attribution model.

The relational structure uses primary keys, foreign keys and defined business relationships to maintain consistency across the generated records.

## 5. Customer Journey Simulation

The pipeline simulates a customer lifecycle through marketing engagement and sales conversion.

A simplified journey is:

**Campaign Interaction → Contact → Lead → Opportunity → Sales Order → Attribution**

Touchpoints represent customer interactions such as clicks, email opens, event attendance and other marketing engagements.

The generation process uses configurable engagement and qualification rules to determine which contacts become leads, which leads progress into opportunities, and which opportunities become won sales.

The project also generates lifecycle events to represent changes in campaign, lead and opportunity statuses over time.

## 6. Attribution Models

The project implements five attribution approaches to compare how marketing revenue is distributed across customer interactions.

| Model | Attribution approach |
|---|---|
| First-touch | Assigns credit to the first eligible interaction. |
| Last-touch | Assigns credit to the last eligible interaction. |
| Linear | Distributes credit equally across eligible interactions. |
| Time-decay | Gives greater credit to interactions closer to conversion. |
| Position-based | Allocates 40% to the first touch, 40% to the last touch and 20% across middle touches. |

### Attribution rules

- Only eligible, resolved and engaged touchpoints are considered.
- The attribution lookback window is 120 days before conversion.
- Touchpoints occurring after conversion are excluded from clean attribution.
- Revenue allocation uses integer cents to maintain financial reconciliation.
- Revenue without eligible interactions is explicitly classified as unattributed.
- Each attribution model is evaluated independently.

The models are compared using revenue allocation, unattributed revenue, ROI, channel ranking stability and correlation with the synthetic campaign-quality variable.

## 7. ROI and Marketing Performance Analysis

The project calculates Return on Investment at campaign, channel, attribution-model and evaluation-period levels.

The ROI formula is:

\[
ROI = \frac{Attributed\ Revenue - Marketing\ Cost}{Marketing\ Cost}
\]

ROI can also be expressed as a percentage by multiplying the ratio by 100.

The analytics pipeline evaluates:

- Attributed revenue.
- Marketing expenditure.
- Campaign ROI.
- Channel ROI.
- Revenue distribution across attribution models.
- Unattributed revenue.
- Channel ranking stability across evaluation periods.
- Attribution credit correlation with synthetic campaign quality.

If a campaign has no recorded cost, its ROI is reported as NULL rather than producing a misleading result.

## 8. Anomaly Injection and Detection

To evaluate data quality, the project first generates valid baseline records and then introduces controlled, labelled anomalies.

The known anomaly labels are maintained separately as ground truth.

### Injected anomaly categories

| Anomaly | Description |
|---|---|
| Duplicate revenue | Revenue counted more than once. |
| Post-conversion touchpoint | A marketing interaction occurring after conversion but incorrectly attributed. |
| Spend currency mismatch | Campaign expenditure recorded with an inconsistent currency. |
| Missing campaign costs | Campaign expenditure records omitted. |
| Unsupported identity linkage | Anonymous sessions linked to contacts without sufficient evidence. |
| Missing identifiers | Records with missing identity information. |

The validation and anomaly detection logic independently examines the generated source data and compares detected issues with the separate ground-truth labels.

This allows precision and recall to be evaluated against known synthetic anomalies.

## 9. Data Validation and Integrity

The project includes 169 automated validation checks covering structural integrity, business rules, chronology and financial reconciliation.

The checks include:

- Primary-key uniqueness and required values.
- Foreign-key integrity.
- Identifier formats.
- Allowed enumeration values.
- Timestamp formats and chronological ordering.
- Campaign, lead and opportunity lifecycle consistency.
- Duplicate transaction detection.
- Revenue and attribution credit reconciliation.
- Campaign budget and expenditure checks.
- Ground-truth separation.
- Evaluation-period consistency.
- Anomaly detector comparison against ground truth.

The validation engine also includes tests that deliberately introduce invalid data to verify that issues are detected.

## 10. Reproducibility

A fixed random seed is used to make synthetic data generation repeatable.

The default full-scale execution uses:

`20261022`

The reproducibility process runs the pipeline twice using the same configuration and compares generated file outputs using file sizes and SHA-256 checksums.

The full-scale verification produced identical results across 25 compared files.

Full-run evidence is available in:

`docs/full_run/`

## 11. Project Structure

```text
marketing-attribution-analytics/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── config/
│   └── config.yaml
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── ground_truth/
│   └── source_manifest.json
│
├── database/
│   ├── schema.sql
│   └── seed.sql
│
├── src/
│   ├── generators/
│   ├── models/
│   ├── attribution/
│   ├── validation/
│   ├── analytics/
│   ├── export/
│   └── main.py

│
├── tests/
│
├── dashboard/
│   └── app.py
│
├── reports/
│
└── docs/
    ├── data_dictionary.md
    ├── architecture.md
    ├── business_rules.md
    ├── assumptions.md
    ├── testing.md
    ├── prompt_history.md
    ├── ai_usage.md
    └── full_run/
```

### Directory responsibilities

| Directory | Description |
|---|---|
| `config/` | Generation configuration and parameters. |
| `data/raw/` | Generated source datasets. |
| `data/processed/` | Derived and processed datasets. |
| `data/ground_truth/` | Synthetic anomaly labels and ground-truth records. |
| `database/` | SQL schema and seed data. |
| `src/` | Main application and business logic. |
| `tests/` | Automated test cases. |
| `dashboard/` | Optional interactive dashboard. |
| `reports/` | Generated analytics and validation reports. |
| `docs/` | Technical documentation and full-run evidence. |

Generated full-scale outputs are written to the directory specified through the `--out` argument.

## 12. Installation and Setup

### Prerequisites

- Python 3.9 or newer.
- pip.
- Git (optional).

Python 3.12 is recommended.

### Step 1: Clone the repository

```bash
git clone https://github.com/S5690sridharramavath/marketing_attribution_analytics.git

cd marketing-attribution-analytics
```

### Step 2: Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv

.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv .venv

source .venv/bin/activate
```

### Step 3: Install dependencies

```bash
python -m pip install --upgrade pip

python -m pip install -r requirements.txt
```

## 13. Running the Project

### A. Generate a starter dataset

Use a smaller dataset for quick development and testing:

```bash
python -m src.main all --scale 0.05 --seed 20261022 --out output/starter
```

### B. Generate the full-scale dataset

```bash
python -m src.main all --scale 1.0 --seed 20261022 --out output/full
```

This executes the complete workflow:

1. Synthetic data generation.
2. Data validation.
3. Attribution calculations.
4. ROI and performance reporting.
5. Reproducibility verification.
6. Documentation generation.

### C. Run individual operations

Generate data:

```bash
python -m src.main generate --scale 1.0 --seed 20261022 --out output/full
```

Validate generated data:

```bash
python -m src.main validate --out output/full
```

Generate analytics reports:

```bash
python -m src.main report --out output/full
```

Check reproducibility:

```bash
python -m src.main reproduce --scale 1.0 --seed 20261022 --out output/repro
```

Generate documentation:

```bash
python -m src.main docs --out output/full
```

### D. Run automated tests

```bash
python -m pytest -v
```

The reviewed project test suite contains 25 tests.

## 14. Generated Reports and Exports

The pipeline generates datasets and reports in the selected output directory.

Important analytical outputs include:

| File | Purpose |
|---|---|
| `model_comparison.csv` | Compares attribution models. |
| `roi_by_campaign_model.csv` | Campaign-level ROI by attribution model. |
| `roi_by_channel_model.csv` | Channel-level ROI by attribution model. |
| `attribution_report.csv` | Detailed attribution results. |
| `exceptions.csv` | Detected data quality issues. |
| `validation_summary.json` | Validation results and anomaly detection metrics. |
| `reproducibility_check.json` | Reproducibility comparison results. |

The pipeline also supports CSV, JSON, SQL and SQLite exports, depending on the selected output formats.

## 15. Sample Full-Scale Results

The following results were obtained from the full-scale synthetic dataset using seed `20261022`.

### Validation summary

| Metric | Result |
|---|---:|
| Total validation checks | 169 |
| Passed checks | 169 |
| Failed checks | 0 |
| Reproducibility | Identical |
| Files compared | 25 |

### Clean attribution model comparison

| Attribution model | Portfolio ROI | Channel rank stability |
|---|---:|---:|
| First-touch | 1.1858 | 0.9818 |
| Last-touch | 1.1562 | 0.9455 |
| Linear | 1.1718 | 0.9636 |
| Time-decay | 1.1593 | 0.9455 |
| Position-based | 1.1712 | 0.9455 |

### Anomaly detection results

All six injected anomaly categories were detected against the generated ground truth with:

- Precision: 100%
- Recall: 100%

These figures describe performance on the controlled synthetic dataset. They should not be interpreted as guaranteed performance on real-world marketing data.

### Key observations

- First-touch attribution produced the highest portfolio ROI in this full-scale clean-data comparison.
- First-touch also showed the highest channel ranking stability.
- The other attribution models produced different revenue allocation patterns.
- The results demonstrate why attribution models should be compared using multiple evaluation metrics rather than ROI alone.

## 16. Optional Dashboard

The project includes an optional Streamlit dashboard for exploring generated analytics.

After generating the full dataset, run the following commands in Windows PowerShell:

```powershell
$env:REPORTS_DIR="output/full/reports"

python -m streamlit run dashboard/app.py
```

The dashboard uses the generated reports to provide a visual interface for exploring marketing analytics.

## 17. Assumptions and Limitations

- All datasets and business records are synthetic.
- No external customer or confidential business dataset is used.
- Campaign performance and conversion outcomes are generated using configurable assumptions.
- The current model assumes one lead per contact and one opportunity per lead.
- Attribution uses a 120-day lookback window.
- Attribution credit represents interaction-based revenue allocation, not proven causal marketing impact.
- The generated ROI values depend on the assumptions and distributions used by the synthetic data generator.
- The optional dashboard requires its additional dependencies.
- The current implementation is designed for local analytical evaluation rather than production deployment.

Potential future improvements include real-world marketing data integration, advanced identity resolution, additional attribution approaches, more sophisticated causal measurement and production API integration.

## 18. AI Usage and Transparency

AI tools were used as development assistance during this project.

The project includes separate documentation describing AI assistance and the prompts used during development:

- `docs/prompt_history.md`
- `docs/ai_usage.md`

These documents should contain an accurate account of the tools used, prompts submitted, assistance received and the work reviewed or modified by the project author.

The project author is responsible for understanding and explaining the implementation, assumptions, business logic and results.

## 19. Verification

To reproduce the full-scale run and execute the automated tests:

```bash
python -m src.main all --scale 1.0 --seed 20261022 --out output/full

python -m pytest -v
```

The reviewed full-scale run produced:

- 500 campaigns.
- 50,000 contacts.
- 200,000 touchpoints.
- 10,000 opportunities.
- 169 successful validation checks.
- Identical outputs across two reproducibility runs.
- 25 passing automated tests.

## 20. Conclusion

This project demonstrates an end-to-end approach to marketing attribution and ROI analytics using reproducible synthetic data.

It brings together data engineering, relational data modelling, customer journey simulation, attribution modelling, financial analytics, anomaly detection and data validation in a modular Python implementation.

The primary focus is not only calculating marketing ROI, but also ensuring that the underlying data, attribution decisions and financial results are explainable, traceable and reproducible.

**Project developed for the YottaFlex AI Candidate Project.**
