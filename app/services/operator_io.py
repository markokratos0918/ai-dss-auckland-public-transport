from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from services.operator_constants import (
    ALL_DAYS,
    ALL_HOURS,
    DATA_SOURCES,
    PRIMARY_PARQUET,
    SPECIAL_SERVICE_LABEL,
)


@st.cache_data(show_spinner=False)
def load_csv(path_text: str) -> pd.DataFrame:
    path = Path(path_text)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_dataset(name: str) -> pd.DataFrame:
    return load_csv(str(DATA_SOURCES[name]))


def sql_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "''")


def data_status() -> str:
    missing = [name for name, path in DATA_SOURCES.items() if not path.exists()]
    if not PRIMARY_PARQUET.exists():
        missing.append("ai_decision_support_model_baseline.parquet")
    return "Ready" if not missing else f"{len(missing)} missing"


def numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    clean = df.copy()
    for column in columns:
        if column in clean.columns:
            clean[column] = pd.to_numeric(clean[column], errors="coerce")
    return clean


def short_action(action: str) -> str:
    if action == "No operational action required":
        return "No action required"
    return action


def filter_clause(
    service_type: str,
    include_special: bool,
    analysis_day: str = ALL_DAYS,
    analysis_hour: str = ALL_HOURS,
) -> str:
    clauses = []
    if service_type == SPECIAL_SERVICE_LABEL:
        clauses.append("COALESCE(CAST(is_special_route AS BOOLEAN), starts_with(upper(route_id), 'S')) = true")
    elif service_type != "All":
        clauses.append(f"COALESCE(NULLIF(service_type, ''), 'Unknown / unmatched route') = '{service_type}'")
    if not include_special:
        clauses.append("COALESCE(CAST(is_special_route AS BOOLEAN), starts_with(upper(route_id), 'S')) = false")
    if analysis_day != ALL_DAYS:
        clauses.append(f"CAST(collection_date AS VARCHAR) = '{analysis_day}'")
    if analysis_hour != ALL_HOURS:
        clauses.append(f"TRY_CAST(trip_hour AS INTEGER) = {int(analysis_hour.split(':')[0])}")
    return "WHERE " + " AND ".join(clauses) if clauses else ""


@st.cache_data(show_spinner=False)
def parquet_query(query: str) -> pd.DataFrame:
    if not PRIMARY_PARQUET.exists():
        return pd.DataFrame()
    try:
        import duckdb
    except ImportError:
        return pd.DataFrame()
    try:
        return duckdb.connect().execute(query).fetchdf()
    except Exception:
        return pd.DataFrame()


def from_primary(
    select_sql: str,
    service_type: str = "All",
    include_special: bool = False,
    analysis_day: str = ALL_DAYS,
    analysis_hour: str = ALL_HOURS,
) -> pd.DataFrame:
    where = filter_clause(service_type, include_special, analysis_day, analysis_hour)
    source = f"read_parquet('{sql_path(PRIMARY_PARQUET)}')"
    return parquet_query(select_sql.format(source=source, where=where))
