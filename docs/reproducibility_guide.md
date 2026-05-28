# Public Reproducibility Guide

Last reviewed: 2026-05-28

Module: Documentation Alignment / Public Reproducibility Guide

Architecture layer: Cross-cutting reproducibility and documentation layer

Architecture position:

```text
GTFS + Weather -> AI-DSS Modeling / SHAP -> Decision Engine -> SUMO -> Dashboard
```

## Purpose

This guide explains how to reproduce the public capstone workflow without relying on private project notes, internal planning files, or large local-only datasets.

The guide is segmented by architecture layer so GitHub readers and assessors can review one part of the workflow at a time.

## Layer Guides

| Layer | Guide |
| --- | --- |
| 1. GTFS + Weather data preparation | `docs/reproducibility/01_data_layer.md` |
| 2. AI-DSS Modeling / SHAP | `docs/reproducibility/02_ai_modeling_shap.md` |
| 3. Decision Engine | `docs/reproducibility/03_decision_engine.md` |
| 4. SUMO scenario validation | `docs/reproducibility/04_sumo_validation.md` |
| 5. Dashboard readiness | `docs/reproducibility/05_dashboard_readiness.md` |
| 6. GitHub data policy | `docs/reproducibility/06_github_data_policy.md` |

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
- AI delay-risk and delay-minute evaluation.
- SHAP or model-native explainability.
- Rule-based decision recommendations.
- SUMO scenario validation.
- Streamlit dashboard readiness through small summary outputs.

## Key Limits

- Raw GTFS-Realtime files are local archival evidence.
- Large row-level CSVs and Parquet files are generated locally.
- SUMO is scenario validation only.
- The AI model is evaluated on the current 21/22-day baseline and should be rerun after the final 30-day dataset is complete.
- Dashboard code should load small summary CSVs by default.

## Related Public Documentation

For detailed storage rules, see:

```text
docs/data_storage_manifest.md
```

For layer-by-layer reproduction, start with:

```text
docs/reproducibility/01_data_layer.md
```
