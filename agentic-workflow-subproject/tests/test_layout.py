import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_FOLDERS = {".claude", ".specify", "data", "docs", "flow", "frontend", "ml", "tests"}


def _tracked_files() -> list[str]:
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [name for name in result.stdout.splitlines() if (ROOT / name).exists()]


def test_layout_has_no_unknown_top_level_folder() -> None:
    folders = {name.split("/")[0] for name in _tracked_files() if "/" in name}
    assert folders <= ALLOWED_FOLDERS, "update LAYOUT.md, the README and this test to add a top-level folder"


def test_layout_keeps_notebooks_inside_their_ml_topic() -> None:
    notebooks = [Path(name) for name in _tracked_files() if name.endswith(".ipynb")]
    assert notebooks
    assert all(path.parts[0] == "ml" and path.parts[2] == "notebooks" for path in notebooks)
