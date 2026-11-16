"""The world must feed the fine-tuned Qualifier the text the deck holds, whatever the checkout."""

import csv
from datetime import UTC, datetime
from pathlib import Path

from world_test_factories import make_row, write_split_file

from flow import inject_dataset
from flow.contracts import Ticket
from flow.world.deck import load_split, normalize_newlines
from flow.world.provenance import file_sha256
from ml.qualifier.src.prompt import build_user_message

STARTED = datetime(2026, 11, 12, tzinfo=UTC)
LF_TEXT = (
    "Subject: Remboursement TX 385 830\n\nBonjour,\n\nle paiement de 1 373,20 € n'est pas arrivé.\n"
)
CRLF_TEXT = LF_TEXT.replace("\n", "\r\n")


def _checkout(path: Path, text: str, newline: str) -> None:
    """Write a deck split as a Windows (CRLF) or Linux (LF) checkout would."""
    write_split_file(path, [make_row("val-1", text), make_row("val-2", "plain question")])
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    path.write_bytes(raw.replace(b"\n", b"\r\n") if newline == "crlf" else raw)


def test_world_text_is_the_same_on_a_windows_and_a_linux_checkout(tmp_path: Path) -> None:
    windows, linux = tmp_path / "windows.csv", tmp_path / "linux.csv"
    _checkout(windows, LF_TEXT, "crlf")
    _checkout(linux, LF_TEXT, "lf")
    assert [t.text for t in load_split(windows, "val")] == [
        t.text for t in load_split(linux, "val")
    ]
    assert load_split(windows, "val")[0].text == LF_TEXT


def test_world_text_equals_what_the_injector_sends_up_to_the_line_ending(tmp_path: Path) -> None:
    path = tmp_path / "val.csv"
    _checkout(path, LF_TEXT, "crlf")
    world = {t.card_id: t for t in load_split(path, "val")}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            envelope = inject_dataset.build_envelope(row, "val", "M-TEST", 1, STARTED)
            sent = Ticket.model_validate(envelope).message_text
            assert normalize_newlines(sent, "lf") == world[row["card_id"]].text
            deck_text = world[row["card_id"]].text
            assert build_user_message(normalize_newlines(sent, "lf")) == build_user_message(
                deck_text
            )


def test_world_can_serve_crlf_text_if_the_qualifier_turns_out_to_need_it(tmp_path: Path) -> None:
    path = tmp_path / "val.csv"
    _checkout(path, LF_TEXT, "lf")
    assert load_split(path, "val", newline="crlf")[0].text == CRLF_TEXT


def test_deck_loader_keeps_accents_and_internal_line_breaks(tmp_path: Path) -> None:
    path = tmp_path / "val.csv"
    _checkout(path, LF_TEXT, "lf")
    assert load_split(path, "val")[0].text == LF_TEXT


def test_input_hash_does_not_depend_on_the_line_ending_of_the_checkout(tmp_path: Path) -> None:
    windows, linux = tmp_path / "windows.csv", tmp_path / "linux.csv"
    _checkout(windows, LF_TEXT, "crlf")
    _checkout(linux, LF_TEXT, "lf")
    assert windows.read_bytes() != linux.read_bytes()
    assert file_sha256(windows) == file_sha256(linux)
