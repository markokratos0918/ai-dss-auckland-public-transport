"""
AI-DSS Auckland Public Transport
GTFS Realtime Automated Collection Script

Purpose:
- Fetch Auckland Transport GTFS Realtime Trip Updates
- Extract trip-level delay records
- Append records into a growing CSV log
- Support multi-day data collection for AI modeling and SUMO scenario validation

Run from project root:
    python collect_gtfs_realtime.py

Stop:
    CTRL + C
"""

import time
import json
from pathlib import Path
from datetime import datetime, timezone

import requests
import pandas as pd
from dotenv import load_dotenv
import os


# -----------------------------
# Project paths
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parent

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "gtfs_realtime"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Legacy single-file log retained for compatibility with earlier notebooks.
# New collection writes to daily files to avoid Excel row limits and file locks.
LEGACY_OUTPUT_CSV = RAW_DIR / "gtfs_realtime_log.csv"

DAILY_DIR = RAW_DIR / "daily"
DAILY_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Environment / API setup
# -----------------------------
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("AT_API_KEY")

if not API_KEY:
    raise ValueError(
        "AT_API_KEY not found. Check that your .env file exists in the project root "
        "and contains: AT_API_KEY=your_key_here"
    )

URL = "https://api.at.govt.nz/realtime/legacy/tripupdates"

HEADERS = {
    "Ocp-Apim-Subscription-Key": API_KEY
}


# -----------------------------
# Fetch GTFS Realtime JSON
# -----------------------------
def fetch_tripupdates() -> dict:
    """
    Fetch GTFS Realtime trip updates from Auckland Transport.
    Returns JSON response as dictionary.
    """
    response = requests.get(URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


# -----------------------------
# Extract records
# -----------------------------
def extract_records(data: dict) -> pd.DataFrame:
    """
    Extract trip-level delay records from Auckland Transport trip updates JSON.
    This follows the same structure validated in 02_gtfs_realtime_collection.ipynb.
    """
    collection_time_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    entities = data.get("response", {}).get("entity", [])

    records = []

    for entity in entities:
        trip_update = entity.get("trip_update", {})
        trip = trip_update.get("trip", {})

        delay_seconds = trip_update.get("delay")

        records.append({
            "collection_time_utc": collection_time_utc,
            "entity_id": entity.get("id"),
            "trip_id": trip.get("trip_id"),
            "route_id": trip.get("route_id"),
            "direction_id": trip.get("direction_id"),
            "start_time": trip.get("start_time"),
            "start_date": trip.get("start_date"),
            "timestamp": trip_update.get("timestamp"),
            "delay_seconds": delay_seconds,
            "is_deleted": entity.get("is_deleted")
        })

    df = pd.DataFrame(records)

    if not df.empty:
        df["delay_seconds"] = pd.to_numeric(df["delay_seconds"], errors="coerce")
        df["delay_minutes"] = df["delay_seconds"] / 60

    return df


# -----------------------------
# Append records safely
# -----------------------------
def append_to_csv(df: pd.DataFrame) -> None:
    """
    Append dataframe to a date-partitioned CSV.
    Header is written only when the daily file does not yet exist.
    """
    if df.empty:
        print("No records extracted. Nothing appended.")
        return

    collection_dt = pd.to_datetime(
        df["collection_time_utc"].iloc[0],
        errors="coerce",
        utc=True
    )

    if pd.isna(collection_dt):
        collection_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    else:
        collection_date = collection_dt.strftime("%Y-%m-%d")

    output_csv = DAILY_DIR / f"gtfs_realtime_{collection_date}.csv"
    file_exists = output_csv.exists()

    df.to_csv(
        output_csv,
        mode="a",
        header=not file_exists,
        index=False
    )

    print(f"Appended {len(df)} records to: {output_csv}")


# -----------------------------
# Optional raw JSON backup
# -----------------------------
def save_raw_json(data: dict) -> None:
    """
    Save raw JSON snapshot for audit/debugging.
    JSON files are timestamped.
    Disabled by default to avoid large raw file accumulation.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = RAW_DIR / f"tripupdates_{timestamp}.json"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Saved raw JSON snapshot: {json_path}")


# -----------------------------
# Main collection loop
# -----------------------------
def main(interval_seconds: int = 600, save_json: bool = False) -> None:
    """
    Run continuous GTFS realtime collection.

    interval_seconds:
        600 = collect every 10 minutes

    save_json:
        False by default to avoid many large files.
        Set True only for debugging/audit snapshots.
    """
    print("Starting GTFS Realtime collection.")
    print("Press CTRL+C to stop.")
    print(f"Collection interval: {interval_seconds} seconds")
    print(f"Daily output folder: {DAILY_DIR}")
    print(f"Legacy single CSV retained at: {LEGACY_OUTPUT_CSV}")

    while True:
        try:
            print("\nFetching GTFS Realtime Trip Updates...")
            print("Fetch time UTC:", datetime.now(timezone.utc).replace(microsecond=0).isoformat())

            data = fetch_tripupdates()

            if save_json:
                save_raw_json(data)

            df = extract_records(data)

            print("Records extracted:", len(df))

            if not df.empty:
                print("Sample columns:", list(df.columns))
                print(
                    "Delay range (minutes):",
                    df["delay_minutes"].min(),
                    "to",
                    df["delay_minutes"].max()
                )

            append_to_csv(df)

        except KeyboardInterrupt:
            print("\nCollection stopped by user.")
            break

        except requests.exceptions.HTTPError as e:
            print("[HTTP ERROR]", e)

        except requests.exceptions.RequestException as e:
            print("[REQUEST ERROR]", e)

        except Exception as e:
            print("[ERROR]", e)

        print(f"Waiting {interval_seconds} seconds before next fetch...")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main(interval_seconds=600, save_json=False)
