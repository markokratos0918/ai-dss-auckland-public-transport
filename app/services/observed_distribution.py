from __future__ import annotations

import pandas as pd

from services.observed_data import (
    OBSERVED_SOURCE_BASELINE,
    OBSERVED_SOURCE_FULL,
    _observed_summary_filter,
)
from services.operator_data import SUMMARY_DIR, from_primary, load_csv


def observed_delay_distribution(
    service_type: str,
    include_special: bool,
    day: str,
    hour: str,
    source_mode: str = OBSERVED_SOURCE_FULL,
) -> pd.DataFrame:
    """Binned distribution of observed delay (clipped to +/-30 min, 2-min bins).

    Storage-summary mode bins route-day average delays; baseline mode bins
    individual observed records. Returns columns: bin_mid, count, band.
    """
    edges = [-30 + 2 * i for i in range(31)]
    if source_mode == OBSERVED_SOURCE_BASELINE:
        query = """
            SELECT
                FLOOR(GREATEST(LEAST(TRY_CAST(delay_minutes AS DOUBLE), 30), -30) / 2) * 2 + 1 AS bin_mid,
                COUNT(*) AS count
            FROM {source}
            {where}
            GROUP BY 1
            ORDER BY 1
        """
        dist = from_primary(query, service_type, include_special, day, hour)
    else:
        route_daily = load_csv(str(SUMMARY_DIR / "gtfs_realtime_storage_route_daily_summary.csv"))
        if route_daily.empty:
            return pd.DataFrame(columns=["bin_mid", "count", "band"])
        route_daily = _observed_summary_filter(route_daily, service_type, include_special, day)
        vals = pd.to_numeric(route_daily.get("avg_delay_minutes"), errors="coerce").dropna()
        if vals.empty:
            return pd.DataFrame(columns=["bin_mid", "count", "band"])
        cut = pd.cut(vals.clip(edges[0], edges[-1]), bins=edges, right=False, include_lowest=True)
        grouped = cut.value_counts().sort_index()
        dist = pd.DataFrame(
            {"bin_mid": [interval.left + 1 for interval in grouped.index], "count": grouped.values}
        )
    if dist.empty:
        return pd.DataFrame(columns=["bin_mid", "count", "band"])
    dist["bin_mid"] = pd.to_numeric(dist["bin_mid"], errors="coerce")
    dist["count"] = pd.to_numeric(dist["count"], errors="coerce").fillna(0).astype(int)

    def _band(mid: float) -> str:
        if mid < -1:
            return "Early-running"
        if mid > 1:
            return "Late-running"
        return "Near on-time"

    dist["band"] = dist["bin_mid"].map(_band)
    return dist.sort_values("bin_mid").reset_index(drop=True)
