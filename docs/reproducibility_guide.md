# Public Reproducibility Guide

Last reviewed: 2026-06-14

Module: Documentation Alignment / Public Reproducibility Guide

Architecture layer: Cross-cutting reproducibility and documentation layer

Architecture position:

```text
GTFS Static + GTFS-Realtime + Open-Meteo
-> Data Storage / Parquet / DuckDB
-> Notebook 09 GTFS + Weather Validation
-> AI-DSS Modeling / SHAP
-> Decision Engine
-> SUMO Scenario Validation
-> M5.1 Streamlit Dashboard
-> Azure Container Apps Deployment
```

## Purpose

This guide explains how to reproduce the public capstone workflow without relying on private project notes, internal planning files, or large local-only datasets.

The guide is segmented by architecture layer so GitHub readers and assessors can review one part of the workflow at a time.

Plain-English project meaning:

```text
Data comes in
-> AI predicts risk
-> system recommends action
-> SUMO tests one scenario
-> dashboard explains it
```

The workflow keeps observed/reference risk separate from AI-predicted risk. Observed/reference risk is created from actual delay records and is used for validation, training reference, comparison, and traceability. AI-predicted risk is created by the AI model and is used for final dashboard decision support.

## Layer Guides

| Layer | Guide |
| --- | --- |
| 1. GTFS + Weather data preparation | `docs/reproducibility/01_data_layer.md` |
| 2. AI-DSS Modeling / SHAP | `docs/reproducibility/02_ai_modeling_shap.md` |
| 3. Decision Engine | `docs/reproducibility/03_decision_engine.md` |
| 4. SUMO scenario validation | `docs/reproducibility/04_sumo_validation.md` |
| 5. Dashboard readiness | `docs/reproducibility/05_dashboard_readiness.md` |

## Quick Start

Create the Python environment:

```bash
conda create -n capstone-gtfs python=3.11 -y
conda activate capstone-gtfs
pip install -r requirements.txt
```

Prepare scalable GTFS-Realtime storage:

```bash
python src/prepare_realtime_storage.py
```

Audit Decision Engine outputs:

```bash
python src/audit_decision_engine_outputs.py
```

Run AI-DSS modeling and SHAP evaluation:

```bash
python src/train_ai_dss_model.py
```

Run a no-write modeling check:

```bash
python src/train_ai_dss_model.py --dry-run
```

## Public Scope

This repository documents a prototype decision-support system, not a production deployment. The reproducible workflow supports:

- GTFS Static, GTFS-Realtime, and Open-Meteo integration.
- Parquet storage for large processed data.
- DuckDB queries over local Parquet outputs.
- AI delay-risk, prediction probability, and delay-minute evaluation.
- SHAP or model-native feature-importance evidence.
- AI-based decision recommendations.
- SUMO scenario validation.
- Streamlit dashboard readiness through AI decision-support Parquet and small summary outputs.

## Key Limits

- Raw GTFS-Realtime files are local archival evidence.
- Large row-level CSVs and Parquet files are generated locally and should not be committed.
- SUMO is scenario validation only.
- The current dataset has 23 likely complete days, not a perfect 30-day dataset.
- High and Severe classes are rare, so AI performance should be described carefully.
- Weather is included, but route, time, and service features appear stronger in the current dataset.
- Dashboard code should query Parquet through DuckDB and should not load large row-level CSVs directly.
- The dashboard is a decision-support prototype, not a live operations system.

## Related Public Documentation

For detailed storage rules, see:

```text
docs/data_storage_manifest.md
```

For layer-by-layer reproduction, start with:

```text
docs/reproducibility/01_data_layer.md
```
