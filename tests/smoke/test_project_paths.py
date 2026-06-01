from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "app"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.config import DATA_SOURCES, LARGE_FILES_NOT_LOADED, PROJECT_ROOT


def test_project_root_contains_expected_folders():
    assert (PROJECT_ROOT / "src").exists()
    assert (PROJECT_ROOT / "app").exists()
    assert (PROJECT_ROOT / "data" / "processed").exists()


def test_dashboard_data_sources_are_lightweight_paths():
    assert DATA_SOURCES
    for path in DATA_SOURCES.values():
        assert path.is_relative_to(PROJECT_ROOT)
        assert "decision_engine_output" not in path.name
        assert path.suffix == ".csv"


def test_large_files_are_declared_not_default_dashboard_inputs():
    names = {Path(path).name for path in LARGE_FILES_NOT_LOADED}
    assert "decision_engine_output.csv" in names
    assert "decision_engine_output.parquet" in names
    assert "gtfs_realtime_cleaned.parquet" in names
