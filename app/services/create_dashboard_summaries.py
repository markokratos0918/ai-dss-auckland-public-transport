from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SUMMARY_DIR = PROJECT_ROOT / "data" / "processed" / "summaries"
DECISION_INPUTS = [
    PROJECT_ROOT / "data" / "processed" / "outputs" / "all_file" / "decision_engine_output.csv",
    PROJECT_ROOT / "data" / "processed" / "outputs" / "model_baseline" / "decision_engine_output.csv",
]
FEATURE_INPUT = SUMMARY_DIR / "ai_feature_importance.csv"


def require_duckdb():
    try:
        import duckdb
    except ImportError as exc:
        raise SystemExit(
            "DuckDB is required. Activate the project environment and run: "
            "pip install -r requirements.txt"
        ) from exc
    return duckdb


def choose_decision_input() -> Path:
    for path in DECISION_INPUTS:
        if path.exists():
            return path
    expected = "\n".join(str(path) for path in DECISION_INPUTS)
    raise SystemExit(f"No Decision Engine input found. Expected one of:\n{expected}")


def sql_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "''")


def write_csv(con, query: str, output: Path) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY ({query}) TO '{sql_path(output)}' (HEADER, DELIMITER ',')")
    return con.execute(f"SELECT COUNT(*) FROM read_csv_auto('{sql_path(output)}')").fetchone()[0]


def create_route_delay_risk_summary(con, source: Path) -> int:
    query = f"""
        WITH base AS (
            SELECT
                COALESCE(NULLIF(service_type, ''), 'Unknown / unmatched route') AS service_type,
                COALESCE(NULLIF(route_display_name, ''), NULLIF(route_short_name, ''), route_id) AS route_display_name,
                COALESCE(NULLIF(route_corridor_name, ''), NULLIF(route_long_name, ''), NULLIF(route_display_name, ''), route_id) AS route_corridor_name,
                route_id,
                COALESCE(CAST(is_special_route AS BOOLEAN), starts_with(upper(route_id), 'S')) AS is_special_route,
                delay_risk,
                recommended_action,
                TRY_CAST(delay_minutes AS DOUBLE) AS delay_minutes,
                trip_id
            FROM read_csv_auto('{sql_path(source)}')
            WHERE route_id IS NOT NULL
        )
        SELECT
            service_type,
            route_display_name,
            route_corridor_name,
            route_id,
            is_special_route,
            delay_risk,
            recommended_action,
            COUNT(*) AS records,
            COUNT(DISTINCT trip_id) AS unique_trips,
            ROUND(AVG(delay_minutes), 3) AS avg_delay_minutes,
            ROUND(MAX(delay_minutes), 3) AS max_delay_minutes
        FROM base
        GROUP BY ALL
        ORDER BY records DESC
    """
    return write_csv(con, query, SUMMARY_DIR / "route_delay_risk_summary.csv")


def create_service_type_delay_summary(con, source: Path) -> int:
    query = f"""
        WITH base AS (
            SELECT
                COALESCE(NULLIF(service_type, ''), 'Unknown / unmatched route') AS service_type,
                delay_risk,
                recommended_action,
                COALESCE(CAST(is_special_route AS BOOLEAN), starts_with(upper(route_id), 'S')) AS is_special_route,
                TRY_CAST(delay_minutes AS DOUBLE) AS delay_minutes,
                trip_id
            FROM read_csv_auto('{sql_path(source)}')
        )
        SELECT
            service_type,
            delay_risk,
            recommended_action,
            is_special_route,
            COUNT(*) AS records,
            COUNT(DISTINCT trip_id) AS unique_trips,
            ROUND(AVG(delay_minutes), 3) AS avg_delay_minutes,
            ROUND(MAX(delay_minutes), 3) AS max_delay_minutes
        FROM base
        GROUP BY ALL
        ORDER BY service_type, records DESC
    """
    return write_csv(con, query, SUMMARY_DIR / "service_type_delay_summary.csv")


def create_weather_delay_risk_summary(con, source: Path) -> int:
    query = f"""
        WITH base AS (
            SELECT
                COALESCE(NULLIF(service_type, ''), 'Unknown / unmatched route') AS service_type,
                delay_risk,
                recommended_action,
                TRY_CAST(delay_minutes AS DOUBLE) AS delay_minutes,
                TRY_CAST(precipitation AS DOUBLE) AS precipitation,
                TRY_CAST(rain AS DOUBLE) AS rain,
                TRY_CAST(wind_speed_10m AS DOUBLE) AS wind_speed_10m,
                trip_id
            FROM read_csv_auto('{sql_path(source)}')
        ),
        labelled AS (
            SELECT *,
                CASE
                    WHEN COALESCE(precipitation, 0) > 0 OR COALESCE(rain, 0) > 0 OR COALESCE(wind_speed_10m, 0) >= 30
                    THEN 'Adverse weather context'
                    ELSE 'Normal / no adverse weather flag'
                END AS weather_context,
                CASE
                    WHEN COALESCE(precipitation, 0) > 0 OR COALESCE(rain, 0) > 0 THEN 'Rain / precipitation'
                    WHEN COALESCE(wind_speed_10m, 0) >= 30 THEN 'High wind'
                    ELSE 'No adverse weather flag'
                END AS weather_rule
            FROM base
        )
        SELECT
            service_type,
            weather_context,
            weather_rule,
            delay_risk,
            recommended_action,
            COUNT(*) AS records,
            COUNT(DISTINCT trip_id) AS unique_trips,
            ROUND(AVG(delay_minutes), 3) AS avg_delay_minutes,
            ROUND(MAX(delay_minutes), 3) AS max_delay_minutes,
            ROUND(AVG(precipitation), 3) AS avg_precipitation,
            ROUND(AVG(rain), 3) AS avg_rain,
            ROUND(AVG(wind_speed_10m), 3) AS avg_wind_speed_10m
        FROM labelled
        GROUP BY ALL
        ORDER BY weather_context, service_type, records DESC
    """
    return write_csv(con, query, SUMMARY_DIR / "weather_delay_risk_summary.csv")


def create_ai_feature_lookup(con) -> int:
    if not FEATURE_INPUT.exists():
        raise SystemExit(f"Missing feature importance input: {FEATURE_INPUT}")
    query = f"""
        SELECT
            source,
            explainability_type,
            feature,
            importance,
            CASE
                WHEN starts_with(feature, 'route_id_') THEN 'Route pattern'
                WHEN starts_with(feature, 'route_type_') THEN 'Service type / mode'
                WHEN feature IN ('trip_hour', 'weekday', 'day_of_month') THEN 'Time pattern'
                WHEN feature IN ('temperature_2m', 'precipitation', 'rain', 'relative_humidity_2m', 'wind_speed_10m') THEN 'Weather context'
                ELSE 'Operational / encoded model feature'
            END AS operator_category,
            CASE
                WHEN starts_with(feature, 'route_id_') THEN 'Specific routes or grouped route patterns contributed to the model signal.'
                WHEN starts_with(feature, 'route_type_') THEN 'The type of public transport service contributed to the model signal.'
                WHEN feature IN ('trip_hour', 'weekday', 'day_of_month') THEN 'Time-based operating patterns contributed to the model signal.'
                WHEN feature IN ('temperature_2m', 'precipitation', 'rain', 'relative_humidity_2m', 'wind_speed_10m') THEN 'Weather is treated as contextual evidence, not proof of delay causation.'
                ELSE 'Encoded feature retained for technical traceability.'
            END AS operator_explanation,
            notes
        FROM read_csv_auto('{sql_path(FEATURE_INPUT)}')
        ORDER BY importance DESC
    """
    return write_csv(con, query, SUMMARY_DIR / "ai_feature_explanation_lookup.csv")


def main() -> None:
    duckdb = require_duckdb()
    source = choose_decision_input()
    con = duckdb.connect()

    print("M5.1 dashboard summary generation")
    print(f"Decision input: {source}")
    print(f"Feature input: {FEATURE_INPUT}")

    outputs = {
        "route_delay_risk_summary.csv": create_route_delay_risk_summary(con, source),
        "service_type_delay_summary.csv": create_service_type_delay_summary(con, source),
        "weather_delay_risk_summary.csv": create_weather_delay_risk_summary(con, source),
        "ai_feature_explanation_lookup.csv": create_ai_feature_lookup(con),
    }

    print("\nOutputs created:")
    for name, rows in outputs.items():
        print(f"- {SUMMARY_DIR / name} ({rows:,} rows)")

    print("\nSanity checks:")
    print("- Streamlit should load these small CSV summaries by default.")
    print("- Large Decision Engine CSVs remain local inputs and should not be committed.")
    print("- S-prefix school/special routes are preserved with is_special_route for filtering.")


if __name__ == "__main__":
    main()
