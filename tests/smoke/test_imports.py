import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "src", ROOT / "app"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def test_ai_modeling_imports():
    modules = [
        "ai_dss_modeling.config",
        "ai_dss_modeling.data",
        "ai_dss_modeling.metrics",
        "ai_dss_modeling.models",
        "ai_dss_modeling.reporting",
    ]
    for module in modules:
        importlib.import_module(module)


def test_streamlit_app_support_imports():
    modules = [
        "app.config",
        "app.services.data_loader",
    ]
    for module in modules:
        importlib.import_module(module)
