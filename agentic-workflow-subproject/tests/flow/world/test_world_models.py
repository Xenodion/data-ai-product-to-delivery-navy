import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, get_args, get_origin

import pytest
from pydantic import ValidationError

from flow.world.models import TABLE_MODELS, Transaction

SCHEMA = Path(__file__).resolve().parents[3] / "flow" / "world" / "schema.sql"
CHECK_IN = re.compile(r"(\w+)\s+TEXT\s+NOT NULL\s+CHECK\s*\(\s*\1\s+IN\s*\(([^)]*)\)\s*\)")


def _tables() -> dict[str, str]:
    sql = SCHEMA.read_text(encoding="utf-8")
    return {
        match.group(1): match.group(2)
        for match in re.finditer(r"CREATE TABLE (\w+) \((.*?)\n\);", sql, flags=re.DOTALL)
    }


def _columns(table: str) -> list[str]:
    connection = sqlite3.connect(":memory:")
    connection.executescript(SCHEMA.read_text(encoding="utf-8"))
    return [row[1] for row in connection.execute(f"PRAGMA table_info({table})")]


def test_every_table_has_a_model_and_every_model_a_table() -> None:
    assert set(TABLE_MODELS) == set(_tables())


@pytest.mark.parametrize("table", sorted(TABLE_MODELS))
def test_model_fields_match_ddl_columns(table: str) -> None:
    assert list(TABLE_MODELS[table].model_fields) == _columns(table)


@pytest.mark.parametrize("table", sorted(TABLE_MODELS))
def test_literal_fields_match_ddl_check_lists(table: str) -> None:
    ddl_lists = {
        column: {value.strip().strip("'") for value in values.split(",")}
        for column, values in CHECK_IN.findall(_tables()[table])
    }
    literal_lists = {
        name: set(get_args(field.annotation))
        for name, field in TABLE_MODELS[table].model_fields.items()
        if get_origin(field.annotation) is Literal
    }
    assert literal_lists == ddl_lists


def test_models_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        TABLE_MODELS["merchant_currencies"].model_validate(
            {"merchant_id": "M-1", "currency": "EUR", "extra": 1}
        )


def test_models_are_immutable() -> None:
    row = TABLE_MODELS["merchant_currencies"](merchant_id="M-1", currency="EUR")
    with pytest.raises(ValidationError):
        row.currency = "GBP"


def test_timestamps_must_carry_a_timezone() -> None:
    base = {
        "transaction_id": "TX-100001",
        "merchant_id": "M-1",
        "amount_minor": 100,
        "currency": "EUR",
        "status": "settled",
        "payment_method": "card",
    }
    Transaction.model_validate(base | {"created_at": datetime(2026, 3, 1, tzinfo=UTC)})
    with pytest.raises(ValidationError):
        Transaction.model_validate(base | {"created_at": datetime(2026, 3, 1)})


def test_currency_must_be_three_uppercase_letters() -> None:
    with pytest.raises(ValidationError):
        TABLE_MODELS["merchant_currencies"](merchant_id="M-1", currency="eur")
