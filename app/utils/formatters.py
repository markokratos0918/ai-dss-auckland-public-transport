"""Centralized formatting utilities for dashboard data display."""

import pandas as pd


def format_delay(value, precision: int = 2) -> str:
    """Format delay value in minutes.

    Args:
        value: Numeric delay value
        precision: Decimal places (default 2)

    Returns:
        Formatted string like "5.25 min" or "Unavailable"
    """
    try:
        return f"{float(value):.{precision}f} min"
    except (TypeError, ValueError):
        return "Unavailable"


def format_weather(value, unit: str, precision: int = 1) -> str:
    """Format weather metric with unit.

    Args:
        value: Numeric weather value
        unit: Unit suffix (e.g., "%", " km/h", " mm")
        precision: Decimal places (default 1)

    Returns:
        Formatted string like "65.2%" or "Unavailable"
    """
    try:
        return f"{float(value):.{precision}f}{unit}"
    except (TypeError, ValueError):
        return "Unavailable"


def format_count(value) -> str:
    """Format count with comma separators.

    Args:
        value: Numeric count value

    Returns:
        Formatted string like "1,234" or empty string if NaN
    """
    try:
        if pd.isna(value):
            return ""
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return ""


def format_percentage(value, precision: int = 1) -> str:
    """Format percentage value.

    Args:
        value: Numeric value (0-100)
        precision: Decimal places (default 1)

    Returns:
        Formatted string like "85.5%" or "Unavailable"
    """
    try:
        return f"{float(value):.{precision}f}%"
    except (TypeError, ValueError):
        return "Unavailable"


def apply_delay_formatting(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Apply delay formatting to specified columns in a dataframe."""
    result = df.copy()
    for column in columns:
        if column in result.columns:
            result[column] = result[column].apply(lambda v: format_delay(v) if pd.notna(v) else "")
    return result


def apply_count_formatting(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Apply count formatting to specified columns in a dataframe."""
    result = df.copy()
    for column in columns:
        if column in result.columns:
            result[column] = result[column].apply(format_count)
    return result
