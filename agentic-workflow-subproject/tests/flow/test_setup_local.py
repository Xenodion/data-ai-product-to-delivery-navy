import hashlib
from pathlib import Path

from flow.setup_local import create_local_dirs, file_md5, has_model


def test_create_local_dirs_is_repeatable(tmp_path: Path) -> None:
    folders = (tmp_path / ".local" / "models", tmp_path / ".local" / "runs")
    create_local_dirs(folders)
    create_local_dirs(folders)
    assert all(folder.is_dir() for folder in folders)


def test_file_md5_matches_hashlib(tmp_path: Path) -> None:
    path = tmp_path / "model.gguf"
    path.write_bytes(b"model")
    assert file_md5(path) == hashlib.md5(b"model", usedforsecurity=False).hexdigest()


def test_has_model_is_false_when_missing_or_corrupt(tmp_path: Path) -> None:
    path = tmp_path / "model.gguf"
    assert not has_model(path, "abc")
    path.write_bytes(b"corrupt")
    assert not has_model(path, "abc")
    assert has_model(path, file_md5(path))
