"""
Create a local DuckDB query layer for GTFS-Realtime processed outputs.

Purpose:
- Query final all-file Parquet without repeatedly loading all rows into pandas.
- Query complete-day model baseline efficiently.
- Validate route summary and completeness outputs.
- Support future Streamlit dashboard performance.

Run from project root:
    python src/create_realtime_duckdb.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PARQUET_DIR = PROCESSED_DIR / "parquet"
DUCKDB_DIR = PROCESSED_DIR / "duckdb"
SUMMARY_DIR = PROCESSED_DIR / "summaries"

ALL_PARQUET_PATH = PARQUET_DIR / "gtfs_realtime_cleaned.parquet"
MODEL_BASELINE_PARQUET_PATH = PARQUET_DIR / "gtfs_realtime_model_baseline.parquet"
DUCKDB_PATH = DUCKDB_DIR / "gtfs_realtime.duckdb"
ROUTE_SUMMARY_PATH = SUMMARY_DIR / "gtfs_realtime_storage_route_daily_summary.csv"
COMPLETENESS_PATH = SUMMARY_DIR / "gtfs_realtime_collection_completeness.csv"


def require_input(path: Path) -> None:
    """Fail early if an expected generated storage input is missing."""
    if not path.exists():
        raise FileNotFoundError(f"Required input not found: {path}")


def create_duckdb_layer() -> None:
    """Create DuckDB views backed by Parquet and summary CSV files."""
    try:
        import duckdb
    except ImportError as exc:
        raise ImportError(
            "DuckDB output requires the duckdb Python package. Install project "
            "requirements, then rerun this script."
        ) from exc

    for path in [
        ALL_PARQUET_PATH,
        MODEL_BASELINE_PARQUET_PATH,
        ROUTE_SUMMARY_PATH,
        COMPLETENESS_PATH,
    ]:
        require_input(path)

    DUCKDB_DIR.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(DUCKDB_PATH))
    try:
        all_parquet = ALL_PARQUET_PATH.as_posix()
        model_parquet = MODEL_BASELINE_PARQUET_PATH.as_posix()
        route_summary_csv = ROUTE_SUMMARY_PATH.as_posix()
        completeness_csv = COMPLETENESS_PATH.as_posix()

        connection.execute("DROP VIEW IF EXISTS realtime_all")
        connection.execute("DROP VIEW IF EXISTS realtime_model_baseline")
        connection.execute("DROP VIEW IF EXISTS route_daily_summary")
        connection.execute("DROP VIEW IF EXISTS collection_completeness")

        connection.execute(
            f"""
            CREATE VIEW realtime_all AS
            SELECT * FROM read_parquet('{all_parquet}')
            """
        )
        connection.execute(
            f"""
            CREATE VIEW realtime_model_baseline AS
            SELECT * FROM read_parquet('{model_parquet}')
            """
        )
        connection.execute(
            f"""
            CREATE VIEW route_daily_summary AS
            SELECT * FROM read_csv_auto('{route_summary_csv}', header = true)
            """
        )
        connection.execute(
            f"""
            CREATE VIEW collection_completeness AS
            SELECT * FROM read_csv_auto('{completeness_csv}', header = true)
            """
        )
    finally:
        connection.close()


def validate_duckdb_layer() -> dict[str, object]:
    """Validate DuckDB counts against Parquet and summary CSV outputs."""
    try:
        import duckdb
    except ImportError as exc:
        raise ImportError(
            "DuckDB validation requires the duckdb Python package. Install project "
            "requirements, then rerun this script."
        ) from exc

    all_rows = len(pd.read_parquet(ALL_PARQUET_PATH))
    model_rows = len(pd.read_parquet(MODEL_BASELINE_PARQUET_PATH))
    route_summary_rows = len(pd.read_csv(ROUTE_SUMMARY_PATH))
    completeness_rows = len(pd.read_csv(COMPLETENESS_PATH))

    connection = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        duckdb_all_rows = connection.execute("SELECT COUNT(*) FROM realtime_all").fetchone()[0]
        duckdb_model_rows = connection.execute(
            "SELECT COUNT(*) FROM realtime_model_baseline"
        ).fetchone()[0]
        duckdb_route_summary_rows = connection.execute(
            "SELECT COUNT(*) FROM route_daily_summary"
        ).fetchone()[0]
        duckdb_completeness_rows = connection.execute(
            "SELECT COUNT(*) FROM collection_completeness"
        ).fetchone()[0]
    finally:
        connection.close()

    return {
        "duckdb_path": str(DUCKDB_PATH.relative_to(PROJECT_ROOT)),
        "duckdb_exists": DUCKDB_PATH.exists(),
        "duckdb_size_mb": round(DUCKDB_PATH.stat().st_size / 1024 / 1024, 2),
        "all_parquet_rows": all_rows,
        "duckdb_all_rows": duckdb_all_rows,
        "all_row_count_matches": duckdb_all_rows == all_rows,
        "model_parquet_rows": model_rows,
        "duckdb_model_rows": duckdb_model_rows,
        "model_row_count_matches": duckdb_model_rows == model_rows,
        "route_summary_csv_rows": route_summary_rows,
        "duckdb_route_summary_rows": duckdb_route_summary_rows,
        "route_summary_row_count_matches": duckdb_route_summary_rows == route_summary_rows,
        "completeness_csv_rows": completeness_rows,
        "duckdb_completeness_rows": duckdb_completeness_rows,
        "completeness_row_count_matches": duckdb_completeness_rows == completeness_rows,
    }


def main() -> None:
    print(f"Creating DuckDB query layer: {DUCKDB_PATH}")
    create_duckdb_layer()
    validation = validate_duckdb_layer()

    print("Done.")
    print("DuckDB validation:")
    print(f"- DuckDB file exists: {validation['duckdb_exists']}")
    print(f"- DuckDB size MB: {validation['duckdb_size_mb']}")
    print(f"- All-file Parquet rows: {validation['all_parquet_rows']:,}")
    print(f"- DuckDB all rows: {validation['duckdb_all_rows']:,}")
    print(f"- All row count matches: {validation['all_row_count_matches']}")
    print(f"- Model-baseline Parquet rows: {validation['model_parquet_rows']:,}")
    print(f"- DuckDB model rows: {validation['duckdb_model_rows']:,}")
    print(f"- Model row count matches: {validation['model_row_count_matches']}")
    print(f"- Route summary CSV rows: {validation['route_summary_csv_rows']:,}")
    print(f"- DuckDB route summary rows: {validation['duckdb_route_summary_rows']:,}")
    print(
        "- Route summary row count matches: "
        f"{validation['route_summary_row_count_matches']}"
    )
    print(f"- Completeness CSV rows: {validation['completeness_csv_rows']:,}")
    print(f"- DuckDB completeness rows: {validation['duckdb_completeness_rows']:,}")
    print(
        "- Completeness row count matches: "
        f"{validation['completeness_row_count_matches']}"
    )


if __name__ == "__main__":
    main()
