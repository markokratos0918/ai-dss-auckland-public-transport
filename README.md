# AI-Driven Decision Support System for Auckland Public Transport Delay Prediction

This repository contains a Master of Software Engineering capstone prototype for an AI-driven decision-support system using Auckland public transport delay data.

The project combines GTFS Static, GTFS-Realtime, and Open-Meteo weather data to support delay-risk prediction, operational recommendations, SUMO scenario validation, and a Streamlit dashboard.

## Architecture

```text
GTFS Static + GTFS-Realtime + Open-Meteo
-> AI Prediction and SHAP Explainability
-> Decision Engine
-> SUMO Scenario Validation
-> Streamlit Dashboard
```

The implementation is a prototype decision-support system. It is not a live operations control system. SUMO outputs are scenario-estimated validation results and do not prove real-world operational success.

## Main Reproduction Commands

Run commands from the repository root unless stated otherwise.

Prepare scalable GTFS-Realtime storage:

```powershell
python src/prepare_realtime_storage.py
```

Audit Decision Engine outputs and regenerate lightweight recommendation summaries:

```powershell
python src/audit_decision_engine_outputs.py
```

Run the AI-DSS modeling checkpoint:

```powershell
python src/train_ai_dss_model.py
```

Run the AI-DSS modeling checkpoint without writing outputs:

```powershell
python src/train_ai_dss_model.py --dry-run
```

Run the Streamlit dashboard:

```powershell
cd app
streamlit run streamlit_app.py
```

## Environment Setup

Create and activate a Python environment:

```powershell
conda create -n capstone-gtfs python=3.11 -y
conda activate capstone-gtfs
pip install -r requirements.txt
```

Optional development checks:

```powershell
pip install -r requirements-dev.txt
pytest tests/smoke
```

Create a `.env` file in the project root when live GTFS-Realtime collection is required:

```text
AT_API_KEY=your_api_key_here
```

The `.env` file is not included in the repository.

## Required Data Artifacts

Some artifacts are generated locally and intentionally excluded from GitHub because they are large or raw evidence files.

| Artifact | Source | Role | GitHub policy |
|---|---|---|---|
| `data/raw/gtfs_static/*.txt` | Auckland Transport GTFS Static download | Route, trip, stop, and schedule reference data | Some static files may be included when small enough; large raw files should stay local |
| `data/raw/gtfs_realtime/daily/*.csv` | GTFS-Realtime collection script | Raw archival trip-update observations | Do not commit |
| `data/processed/gtfs_realtime_cleaned.parquet` | `python src/prepare_realtime_storage.py` | Cleaned scalable GTFS-Realtime working dataset | Do not commit |
| `data/processed/decision_engine_output.parquet` | Notebook 09 / Decision Engine export | Preferred local row-level decision output | Do not commit |
| `data/processed/decision_engine_output.csv` | Notebook 09 / Decision Engine export | Legacy/export row-level decision output | Do not commit |
| `data/processed/summaries/*.csv` | Notebook 09, Decision Engine audit, and AI scripts | Lightweight reproducibility and dashboard summaries | Commit after review when small |
| `data/processed/sumo_*.csv` | SUMO scenario-validation module | Saved scenario validation outputs for dashboard use | Commit after review when small |

## Key Public Outputs

The dashboard and public reproducibility checks should use lightweight processed outputs by default:

```text
data/processed/summaries/ai_model_metrics.csv
data/processed/summaries/ai_feature_importance.csv
data/processed/summaries/ai_prediction_sample.csv
data/processed/summaries/decision_recommendation_summary.csv
data/processed/summaries/decision_route_recommendation_counts.csv
data/processed/summaries/gtfs_realtime_daily_summary.csv
data/processed/summaries/gtfs_realtime_route_daily_summary.csv
data/processed/summaries/gtfs_realtime_top_delayed_routes.csv
data/processed/intervention_logic.csv
data/processed/sumo_scenarios.csv
data/processed/sumo_kpis.csv
data/processed/sumo_validation_results.csv
```

Large row-level files should not be loaded by the dashboard by default.

## Module Summary

| Module | Purpose | Main files |
|---|---|---|
| GTFS and weather validation | Validate real Auckland GTFS-Realtime, GTFS Static, and weather integration | `notebooks/09_validation_and_evaluation_realtimegtfs.ipynb` |
| Scalable storage | Convert cleaned GTFS-Realtime data into Parquet and small summaries | `src/prepare_realtime_storage.py` |
| AI-DSS modeling and SHAP | Train/evaluate prediction models and create explainability evidence | `src/train_ai_dss_model.py`, `src/ai_dss_modeling/` |
| Decision Engine | Validate delay-risk to recommendation traceability | `src/audit_decision_engine_outputs.py` |
| SUMO validation | Compare baseline, disruption, and intervention scenarios | `notebooks/10_sumo_minimal_prototype.ipynb`, `data/processed/sumo_*.csv` |
| Dashboard | Present delay risk, recommendation, and scenario-estimated impact | `app/streamlit_app.py`, `app/pages/` |

## Documentation

Public reproducibility notes are kept in:

```text
docs/reproducibility_guide.md
docs/reproducibility/
```

Internal planning notes are local-only and are not part of the public project evidence.

## Scope Limits

- The current system is a capstone prototype.
- AI model outputs support decision analysis and are not production-ready predictions.
- SUMO is used for scenario validation only.
- The dashboard should display saved processed outputs and should not depend on live SUMO execution.
- The final 30-day GTFS-Realtime dataset should be regenerated and revalidated through the same pipeline before final reporting.
