import json
from pathlib import Path

import pytest
from world_test_factories import make_row, write_split_file

from flow.world.deck import SPLIT_NAMES, load_deck, load_split
from flow.world.errors import DeckContractError


def test_load_deck_reads_four_splits_in_fixed_order(write_deck) -> None:
    deck = load_deck(write_deck())
    assert [t.split for t in deck][:1] == ["train"]
    assert {t.split for t in deck} == set(SPLIT_NAMES)
    assert len(deck) == 100


def test_load_deck_never_opens_the_quarantine_file(write_deck) -> None:
    # the quarantine file in the micro deck is invalid bytes: opening it as CSV would fail loudly
    load_deck(write_deck())


def test_load_split_refuses_a_quarantine_path(tmp_path: Path) -> None:
    path = tmp_path / "train_quarantine.csv"
    write_split_file(path, [make_row("a")])
    with pytest.raises(DeckContractError, match="quarantine"):
        load_split(path, "train")


def test_load_split_parses_label_traps_and_noise(tmp_path: Path) -> None:
    path = tmp_path / "val.csv"
    write_split_file(
        path, [make_row("a", traps="id_spaced|currency_missing", noise="typos|signature")]
    )
    ticket = load_split(path, "val")[0]
    assert ticket.label.intent == "payment_status"
    assert ticket.traps == ("id_spaced", "currency_missing")
    assert ticket.noise == ("typos", "signature")


def test_load_split_raises_on_missing_column(tmp_path: Path) -> None:
    path = tmp_path / "val.csv"
    path.write_text("card_id,ticket\na,hello\n", encoding="utf-8")
    with pytest.raises(DeckContractError, match="missing columns"):
        load_split(path, "val")


def test_load_split_raises_on_invalid_target(tmp_path: Path) -> None:
    path = tmp_path / "val.csv"
    write_split_file(path, [make_row("a", target=json.dumps({"intent": "nonsense"}))])
    with pytest.raises(DeckContractError, match="a"):
        load_split(path, "val")


def test_load_split_raises_on_non_json_target(tmp_path: Path) -> None:
    path = tmp_path / "val.csv"
    write_split_file(path, [make_row("a", target="{not json")])
    with pytest.raises(DeckContractError):
        load_split(path, "val")


def test_load_split_raises_on_duplicate_card_id(tmp_path: Path) -> None:
    path = tmp_path / "val.csv"
    write_split_file(path, [make_row("a"), make_row("a")])
    with pytest.raises(DeckContractError, match="duplicate"):
        load_split(path, "val")


def test_load_deck_raises_on_card_id_shared_between_splits(tmp_path: Path) -> None:
    for split in SPLIT_NAMES:
        write_split_file(tmp_path / f"{split}.csv", [make_row("same")])
    with pytest.raises(DeckContractError, match="unique"):
        load_deck(tmp_path)


def test_deck_ticket_anomalies_combine_traps_and_sentinel(tmp_path: Path) -> None:
    path = tmp_path / "val.csv"
    write_split_file(
        path,
        [make_row("a", traps="id_spaced|currency_missing", sentinel_kind="spam"), make_row("b")],
    )
    first, second = load_split(path, "val")
    assert first.anomalies == ("id_spaced", "currency_missing", "spam")
    assert second.anomalies == ("none",)


@pytest.mark.parametrize(
    "override",
    [{"language": "xx"}, {"channel": "carrier_pigeon"}, {"sector": "mining"}, {"id_case": "weird"}],
)
def test_load_split_rejects_a_value_outside_the_known_categories(
    tmp_path: Path, override: dict[str, str]
) -> None:
    path = tmp_path / "val.csv"
    write_split_file(path, [make_row("a", **override)])
    with pytest.raises(DeckContractError):
        load_split(path, "val")


def test_load_split_rejects_an_unexpected_column(tmp_path: Path) -> None:
    path = tmp_path / "val.csv"
    write_split_file(path, [make_row("a")])
    text = path.read_text(encoding="utf-8").replace("card_id,", "card_id,surprise,", 1)
    path.write_text(text, encoding="utf-8")
    with pytest.raises(DeckContractError, match="unexpected"):
        load_split(path, "val")
