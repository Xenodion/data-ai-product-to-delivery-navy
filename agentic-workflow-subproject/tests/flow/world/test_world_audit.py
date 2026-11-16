from datetime import date
from pathlib import Path

from world_test_factories import make_row, write_split_file

from flow.world.audit import build_audit, quarantine_sizes
from flow.world.deck import SPLIT_NAMES, load_deck

REFERENCE = date(2026, 11, 12)


def _deck_with_text(tmp_path: Path, text: str):
    for split in SPLIT_NAMES:
        write_split_file(tmp_path / f"{split}.csv", [make_row(f"{split}-1", text)])
    return load_deck(tmp_path)


def test_build_audit_renders_every_section(write_deck) -> None:
    report = build_audit(load_deck(write_deck()), REFERENCE, {}, cited_date_cutoff=date(2026, 7, 1))
    for heading in (
        "## 1. Splits, sectors, languages",
        "## 2. id_case against the annotated transaction_id",
        "## 3. Annotated amount and currency",
        "## 4. Reference extractor, validated on the annotations",
        "## 5. Dates cited in ticket text",
        "## 6. Stale dates in current and dev pools",
        "## 7. Amount quantiles in EUR",
        "## 8. Quarantine files",
    ):
        assert heading in report


def test_build_audit_counts_the_deck_and_holds_no_ticket_text(write_deck) -> None:
    report = build_audit(load_deck(write_deck()), REFERENCE, {})
    assert "Tickets: 100" in report
    assert "about TX-" not in report


def test_build_audit_reports_a_full_extractor_match_when_text_holds_the_annotated_id(
    tmp_path: Path,
) -> None:
    report = build_audit(_deck_with_text(tmp_path, "Payment TX-123456 is late"), REFERENCE, {})
    assert "| canonical | 4 | 4 | - |" in report


def test_build_audit_lists_the_card_id_when_the_annotated_id_is_not_in_the_text(
    tmp_path: Path,
) -> None:
    report = build_audit(_deck_with_text(tmp_path, "Payment TX-999999 is late"), REFERENCE, {})
    assert "| canonical | 0 | 4 |" in report
    assert "train-1" in report


def test_build_audit_counts_stale_dates_of_the_current_and_dev_pools(tmp_path: Path) -> None:
    deck = _deck_with_text(tmp_path, "The payment of 3 Feb 2025 never arrived, TX-123456")
    report = build_audit(deck, REFERENCE, {}, cited_date_cutoff=date(2026, 7, 1))
    assert "| test_natural | 1 | 1 |" in report
    assert "| val | 1 | 1 |" in report


def test_quarantine_sizes_reads_file_sizes_without_opening_them(write_deck) -> None:
    sizes = quarantine_sizes(write_deck())
    assert sizes == {"train_quarantine.csv": len(b"\xff\xfe not a csv")}
