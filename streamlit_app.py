from pathlib import Path
import os
import runpy
import sys


APP_DIR = Path(__file__).resolve().parent / "app"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

os.chdir(APP_DIR)
runpy.run_path(str(APP_DIR / "streamlit_app.py"), run_name="__main__")
