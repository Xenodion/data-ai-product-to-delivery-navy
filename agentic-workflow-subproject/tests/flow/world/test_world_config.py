import tomllib
from pathlib import Path

import pytest
from pydantic import ValidationError

from flow.world.config import DEFAULT_CONFIG_PATH, PROJECT_ROOT, WorldConfig, load_world_config
from flow.world.errors import ConfigError


def _raw() -> dict:
    return tomllib.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))


def test_load_world_config_accepts_the_committed_file() -> None:
    config = load_world_config()
    assert config.sample.current == 200
    assert config.text_newline == "lf"
    assert config.budget.cap_usd == 1.5
    assert sorted(config.threads.exchange_weights) == [0, 1, 2]
    assert config.dates.open_days < config.dates.history_gap_days


def test_load_world_config_raises_config_error_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_world_config(tmp_path / "absent.toml")


def test_load_world_config_raises_config_error_on_invalid_toml(tmp_path: Path) -> None:
    path = tmp_path / "bad.toml"
    path.write_text("seed = = 1", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_world_config(path)


def test_world_config_rejects_unknown_top_level_key() -> None:
    with pytest.raises(ValidationError):
        WorldConfig.model_validate(_raw() | {"surprise": 1})


def test_world_config_rejects_unknown_nested_key() -> None:
    raw = _raw()
    raw["sample"] = raw["sample"] | {"surprise": 1}
    with pytest.raises(ValidationError):
        WorldConfig.model_validate(raw)


def test_world_config_rejects_removed_sampling_floor() -> None:
    raw = _raw()
    raw["sample"] = raw["sample"] | {"min_per_category": 5}
    with pytest.raises(ValidationError):
        WorldConfig.model_validate(raw)


def test_world_config_rejects_exchange_weights_not_summing_to_one() -> None:
    raw = _raw()
    raw["threads"]["exchange_weights"] = {"0": 0.5, "1": 0.5, "2": 0.5}
    with pytest.raises(ValidationError, match="sum to 1"):
        WorldConfig.model_validate(raw)


def test_world_config_rejects_missing_exchange_count() -> None:
    raw = _raw()
    raw["threads"]["exchange_weights"] = {"0": 0.5, "1": 0.5}
    with pytest.raises(ValidationError, match="exactly"):
        WorldConfig.model_validate(raw)


def test_world_config_rejects_negative_weight() -> None:
    raw = _raw()
    raw["threads"]["end_state_weights"] = {"closed": 1.25, "open_awaiting_merchant": -0.25}
    with pytest.raises(ValidationError, match="negative"):
        WorldConfig.model_validate(raw)


def test_world_config_rejects_tier_weights_not_summing_to_one() -> None:
    raw = _raw()
    raw["merchants"]["tier_weights_without_amount"] = {"small": 0.5, "medium": 0.5, "large": 0.5}
    with pytest.raises(ValidationError, match="sum to 1"):
        WorldConfig.model_validate(raw)


def test_world_config_rejects_window_after_reference_date() -> None:
    raw = _raw()
    raw["window_end"] = raw["reference_date"].replace(year=raw["reference_date"].year + 1)
    with pytest.raises(ValidationError, match="window_start"):
        WorldConfig.model_validate(raw)


def test_world_config_rejects_history_gap_not_longer_than_open_days() -> None:
    raw = _raw()
    raw["dates"]["history_gap_days"] = raw["dates"]["open_days"]
    with pytest.raises(ValidationError, match="open_days"):
        WorldConfig.model_validate(raw)


def test_world_config_rejects_history_gap_longer_than_the_window() -> None:
    raw = _raw()
    raw["dates"]["history_gap_days"] = 400
    with pytest.raises(ValidationError, match="window length"):
        WorldConfig.model_validate(raw)


def test_world_config_rejects_fx_table_without_euro() -> None:
    raw = _raw()
    raw["fx_to_eur"] = {"GBP": 1.15}
    with pytest.raises(ValidationError, match="EUR"):
        WorldConfig.model_validate(raw)


def test_world_config_rejects_pilot_cap_above_total_cap() -> None:
    raw = _raw()
    raw["budget"]["pilot_cap_usd"] = raw["budget"]["cap_usd"] + 1
    with pytest.raises(ValidationError, match="pilot_cap_usd"):
        WorldConfig.model_validate(raw)


def test_resolve_anchors_relative_paths_at_the_project_root() -> None:
    config = load_world_config()
    assert config.resolve(config.paths.deck_dir) == PROJECT_ROOT / "data" / "dataset"
