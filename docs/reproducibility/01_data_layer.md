# Layer 1: GTFS + Weather Data Preparation

Architecture position:

```text
GTFS + Weather -> AI-DSS Modeling / SHAP
```

## Purpose

This layer prepares the transport and weather dataset used by the rest of the capstone workflow. It integrates Auckland Transport GTFS Static, Auckland Transport GTFS-Realtime, and Open-Meteo weather variables.

## Public Data Sources

| Source | Role |
| --- | --- |
| GTFS Static | Route, trip, stop, schedule, and route metadata |
| GTFS-Realtime | Live trip updates and delay observations |
| Open-Meteo | Hourly weather variables aligned to GTFS timestamps |

Expected local GTFS Static path:

```text
data/raw/gtfs_static/
```

Expected local GTFS-Realtime archival paths:

```text
data/raw/gtfs_realtime/
data/raw/gtfs_realtime/daily/
```

## Environment Setup

```bash
conda create -n capstone-gtfs python=3.11 -y
conda activate capstone-gtfs
pip install -r requirements.txt
```

Create a local `.env` file only if collecting new GTFS-Realtime data:

```text
AT_API_KEY=your_api_key_here
```

Do not commit `.env`.

## Storage Preparation

Place local raw GTFS-Realtime daily CSV files under:

```text
data/raw/gtfs_realtime/daily/
```

Generate the cleaned local Parquet dataset and storage summaries:

```bash
python src/prepare_realtime_storage.py
```

Expected local output:

```text
data/processed/gtfs_realtime_cleaned.parquet
```

Expected small summary outputs:

```text
data/processed/summaries/gtfs_realtime_storage_daily_summary.csv
data/processed/summaries/gtfs_realtime_storage_route_daily_summary.csv
data/processed/summaries/gtfs_realtime_storage_top_delayed_routes.csv
```

## Notebook 09 Validation

Notebook 09 is the real Auckland validation source:

```text
notebooks/09_validation_and_evaluation_realtimegtfs.ipynb
```

It validates the GTFS-Realtime pipeline, merges GTFS Static route metadata, aligns Open-Meteo weather, creates delay-risk categories, and exports dashboard-ready decision outputs when the export switch is enabled.

Expected local row-level output:

```text
data/processed/decision_engine_output.csv
```

This file is large and must stay local.

Expected small summary outputs:

```text
data/processed/summaries/gtfs_realtime_daily_summary.csv
data/processed/summaries/gtfs_realtime_route_daily_summary.csv
data/processed/summaries/gtfs_realtime_top_delayed_routes.csv
```

## Notes

- Raw GTFS-Realtime files are archival/local evidence.
- The cleaned Parquet file is generated locally.
- For detailed storage rules, see `docs/data_storage_manifest.md`.
