# AI Usage Disclosure

## 1. AI tools used

The following AI tools were used as development assistance during this project:

- Claude (claude.ai)
- ChatGPT (OpenAI)
- GeminiAI
- Cursor

The tools were used for technical guidance, implementation assistance, reviewing documentation and improving the clarity of the project.

## 2. Where AI accelerated the work

AI assistance was used during different stages of development, including:

- Understanding the assignment requirements and planning the implementation.
- Developing initial versions of the synthetic data generator and relational data model.
- Structuring the attribution engine and its five attribution approaches.
- Designing data validation and anomaly detection logic.
- Developing ROI calculations and analytical reports.
- Organising the source code into modular packages.
- Reviewing project documentation and improving setup and execution instructions.
- Discussing test cases, edge cases and reproducibility.

## 3. Areas where AI assistance was significant

AI assistance contributed substantially to the initial implementation and design of:

- Master and transaction data generation.
- Attribution calculation and revenue allocation.
- Data integrity, temporal and reconciliation validation.
- Synthetic anomaly generation and detection.
- ROI and attribution model comparison.
- Automated tests and technical documentation.

The generated code and suggestions were treated as development assistance and required review and execution.

## 4. Work personally performed and verified

The project was executed locally to verify that the implementation worked.

The following activities were performed:

- Ran the starter-scale data generation pipeline.
- Checked the generated record counts against the required dataset volumes.
- Executed the validation process and reviewed the 169 validation checks.
- Reviewed anomaly detection results against the separate synthetic ground truth.
- Compared the five attribution models and their ROI results.
- Ran the reproducibility check and reviewed the output comparison.
- Reviewed the generated CSV and JSON reports.
- Executed the automated test suite.

The full-scale execution reported 169/169 validation checks passed, and the reproducibility check reported identical outputs across 24 compared files. The project test suite contains 24 tests.

## 5. Important implementation decisions reviewed

The following decisions are documented in the project:

- Master data is generated before dependent transaction and event data.
- Ground-truth labels are stored separately from the input datasets.
- Attribution considers eligible, resolved and engaged touchpoints within a 120-day lookback window.
- Revenue credits are allocated in integer cents to preserve reconciliation.
- Unattributed revenue is represented explicitly.
- Anomaly detectors inspect input data independently of ground-truth labels.
- A fixed seed and deterministic generation order support reproducibility.
- Synthetic ROI results are presented as generated analytical outcomes, not real-world business benchmarks.

## 6. Understanding and ownership

AI assistance was used to accelerate development, but the project author is responsible for reviewing the implementation, understanding the business rules, explaining the design decisions and discussing the limitations.

The author should be able to walk through the generator, data relationships, attribution calculations, ROI formula, anomaly detection process and validation results.

## 7. Supporting record

The prompts submitted to AI tools are recorded separately in:

`docs/prompt_history.md`

This disclosure should be read together with the prompt history and the source code.