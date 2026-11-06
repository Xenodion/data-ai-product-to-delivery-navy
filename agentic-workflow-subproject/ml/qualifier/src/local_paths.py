"""Folders of the untracked local workspace. Everything in them can be rebuilt or downloaded again."""

from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[3]
LOCAL_DIR: Final = PROJECT_ROOT / ".local"
MODELS_DIR: Final = LOCAL_DIR / "models"
MLFLOW_DIR: Final = LOCAL_DIR / "mlflow"
LOGS_DIR: Final = LOCAL_DIR / "logs"
PIPELINES_DIR: Final = LOCAL_DIR / "pipelines"
RUNS_DIR: Final = LOCAL_DIR / "runs"
FIGURES_DIR: Final = LOCAL_DIR / "figures"
LOCAL_FOLDERS: Final = (MODELS_DIR, MLFLOW_DIR, LOGS_DIR, PIPELINES_DIR, RUNS_DIR, FIGURES_DIR)
