# Testing and Verification

## 1. Purpose

This document describes how to run the automated test suite and reproduce the main verification results for the Marketing Attribution and ROI Analytics project.

Testing covers:

- Synthetic data generation and expected record volumes
- Primary-key and foreign-key integrity
- Business-rule and temporal validation
- Attribution calculations and revenue reconciliation
- Anomaly detection against labelled synthetic cases
- Reproducibility across repeated runs

All project datasets are synthetic. No real customer or business data is used.

## 2. Environment

The project was reviewed using Python 3.11. The core pipeline uses the Python standard library. Install the declared project dependencies from the repository root:

```bash
python -m pip install -r requirements.txt
```

The automated tests use `pytest`.

## 3. Automated test suite

Run the tests from the project root:

```bash
python -m pytest -v
```

The reviewed test suite contains **25 automated tests**.

| Test file | Main coverage |
|---|---|
| `tests/test_generators.py` | Default configuration, record volumes, output layout, labelled edge cases, ground-truth separation, identifiers and export consistency |
| `tests/test_attribution.py` | Exact cent allocation, model weights, attribution windows, eligible touches, revenue reconciliation and Spearman correlation |
| `tests/test_validation.py` | Structural validation, evaluation periods, broken foreign keys, duplicate primary keys, invalid enums, reconciliation errors, temporal violations and unlabelled anomalies |
| `tests/test_reproducibility.py` | Identical output for the same seed, changed output for a different seed and shared starter/full-scale code path |

The shared pytest fixture generates a small dataset using scale `0.02`. This keeps the automated tests relatively fast while exercising the pipeline.

### Negative and edge-case testing

The test suite includes deliberate invalid-data scenarios to check whether validation catches problems rather than only confirming that valid data passes.

Examples include:

- A broken foreign-key reference
- A duplicate primary key
- An invalid enumeration value
- An attribution reconciliation failure
- A temporal rule violation
- An injected anomaly that is not represented in the ground-truth labels

These tests help verify that validation logic can identify incorrect or inconsistent data.

## 4. Starter-scale pipeline

Run a starter-scale pipeline from the project root:

```bash
python -m src.main all --scale 0.05 --seed 20261022 --out output/starter
```

Previously recorded starter-run counts:

| Entity | Records |
|---|---:|
| Campaigns | 25 |
| Contacts | 2,500 |
| Touchpoints | 10,000 |
| Web sessions | 5,691 |
| Leads | 1,000 |
| Opportunities | 500 |
| Sales orders | 138 |
| Cost records | 353 |
| Attribution results | 2,868 |

The recorded starter run passed **169 out of 169 validation checks** and reported identical outputs across two reproducibility runs.

## 5. Full-scale pipeline

Run the full-scale pipeline:

```bash
python -m src.main all --scale 1.0 --seed 20261022 --out output/full
```

Recorded full-scale dataset counts:

| Entity | Records |
|---|---:|
| Campaigns | 500 |
| Contacts | 50,000 |
| Touchpoints | 200,000 |
| Web sessions | 110,007 |
| Leads | 20,000 |
| Opportunities | 10,000 |
| Sales orders | 3,009 |
| Cost records | 8,186 |
| Attribution results | 57,276 |

The full-scale run exercises the same pipeline with larger synthetic datasets.

## 6. Validation and anomaly detection

The recorded full-scale validation summary reports:

- **169 checks passed**
- **0 checks failed**

The project injects known synthetic anomalies and compares detected cases against separate ground-truth labels.

| Anomaly category | Ground-truth cases | Detected cases |
|---|---:|---:|
| Anonymous session linked without evidence | 25 | 25 |
| Campaign costs omitted | 15 | 15 |
| Missing identifiers | 7,544 | 7,544 |
| Revenue counted more than once | 40 | 40 |
| Spend currency mismatch | 30 | 30 |
| Touchpoint after conversion attributed | 504 | 504 |

For these labelled synthetic cases, the recorded precision and recall are 1.0 for each category.

These results demonstrate detection against the project's deliberately injected test cases. They do not guarantee the same performance on real-world marketing data.

## 7. Attribution and ROI verification

The project compares five attribution models:

1. First-touch
2. Last-touch
3. Linear
4. Time-decay
5. Position-based

The recorded full-scale clean-data portfolio ROI values are:

| Attribution model | Portfolio ROI |
|---|---:|
| First-touch | 1.1858 |
| Last-touch | 1.1562 |
| Linear | 1.1718 |
| Time-decay | 1.1593 |
| Position-based | 1.1712 |

The validation process checks that attribution credits reconcile to sales-order revenue using integer cents.

ROI results are based on the project's synthetic revenue and marketing-cost assumptions. They should not be interpreted as causal estimates of incremental marketing impact.

## 8. Reproducibility

Run the reproducibility command:

```bash
python -m src.main reproduce --scale 1.0 --seed 20261022 --out output/repro
```

The recorded full-scale reproducibility check compared **24 output files** and reported identical results across two runs using seed `20261022`.

The project uses a fixed seed so that generated data and exported results can be reproduced under the same configuration and execution environment.

A different seed is expected to produce different generated data.

## 9. Evidence retained in the repository

The `docs/full_run/` directory contains saved evidence from the recorded full-scale run:

| File | Purpose |
|---|---|
| `channel_roi.csv` | Channel-level ROI results |
| `model_comparison.csv` | Attribution model comparison |
| `reproducibility_check_full.json` | Reproducibility verification results |
| `source_manifest_full.json` | Generated source-data manifest |
| `validation_summary_full.json` | Validation checks and anomaly-detection results |

These files preserve results from the recorded run. Running the commands in this document creates fresh outputs in the selected output directory.

## 10. Dashboard verification

The dashboard is an optional way to explore generated analytics. It is separate from the core command-line pipeline.

The core data-generation, attribution, validation and export workflow can be run without launching the dashboard.

Dashboard runtime behaviour should be verified separately in the review environment before claiming that it has been tested end to end.

## 11. Limitations

- All input and evaluation data is synthetic.
- Anomaly detection is evaluated against deliberately injected and labelled cases.
- Perfect precision and recall on these test cases do not establish real-world detection performance.
- Attribution credit is not a causal estimate of incremental marketing impact.
- ROI depends on the synthetic data-generation assumptions and configuration.
- Reproducibility can depend on using the same seed, configuration and compatible software environment.
- Dashboard execution is optional and is not required to run the core pipeline.

## 12. Verification summary

The latest reviewed project version has:

- 25 automated pytest tests
- 169 recorded full-scale validation checks passed
- 6 synthetic anomaly categories with all labelled cases detected
- 24 output files compared in the recorded reproducibility check
- A full-scale dataset generated with seed `20261022`

To verify the current checkout independently, run the commands in this document and retain the resulting terminal output and generated evidence.