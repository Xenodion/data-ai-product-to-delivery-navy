from datetime import date

import pytest

from flow.world.text_signals import extract_references, extract_text_dates


@pytest.mark.parametrize(
    "text",
    [
        "payment TX-520024 is late",
        "payment TX 520 024 is late",
        "payment TX520024 is late",
        "payment tx-520024 is late",
        "payment TX-520\n024 is late",
        "> Reference: TX-520024",
        "TX - 520024",
    ],
)
def test_extract_references_recovers_the_canonical_id_from_every_surface_form(text: str) -> None:
    assert extract_references(text) == ("TX-520024",)


@pytest.mark.parametrize(
    "text",
    ["TX-6214063", "TX-3242", "TX-53-9876", "TX-12345", "no reference here", "INV-509396"],
)
def test_extract_references_ignores_malformed_or_foreign_references(text: str) -> None:
    assert extract_references(text) == ()


def test_extract_references_returns_each_reference_once_in_order() -> None:
    text = "TX-111111 then TX-222222, again TX-111111"
    assert extract_references(text) == ("TX-111111", "TX-222222")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("sent on 2026-03-05.", date(2026, 3, 5)),
        ("sent on 03/02/2025", date(2025, 2, 3)),
        ("Date: Mon, 3 Feb 2025", date(2025, 2, 3)),
        ("le 12 mars 2025 a 09:14", date(2025, 3, 12)),
        ("on February 3, 2025", date(2025, 2, 3)),
        ("le 1er avril 2026", date(2026, 4, 1)),
        ("am 3. März 2025", date(2025, 3, 3)),
        ("el 4 marzo 2025", date(2025, 3, 4)),
    ],
)
def test_extract_text_dates_parses_complete_dates(text: str, expected: date) -> None:
    assert extract_text_dates(text).full_dates == (expected,)


def test_extract_text_dates_ignores_impossible_dates() -> None:
    assert extract_text_dates("on 31/02/2025 and 2025-13-01").full_dates == ()


def test_extract_text_dates_latest_bound_uses_first_of_year_for_a_bare_year() -> None:
    dates = extract_text_dates("since 2024 and again in 2025")
    assert dates.full_dates == ()
    assert dates.years == (2024, 2025)
    assert dates.latest_bound == date(2025, 1, 1)
    assert dates.latest_full_date is None
    assert dates.earliest_full_date is None


def test_extract_text_dates_latest_and_earliest_full_dates() -> None:
    dates = extract_text_dates("first 2025-01-10, then 2026-02-01")
    assert dates.latest_bound == date(2026, 2, 1)
    assert dates.latest_full_date == date(2026, 2, 1)
    assert dates.earliest_full_date == date(2025, 1, 10)


@pytest.mark.parametrize(
    "text",
    [
        "no date at all",
        "amount 2024.50 EUR",
        "amount 2030,00 EUR",
        "amount 2,035.00 EUR",
        "code 120245",
        "see INV-2026-2362",
        "GDPR 2016/679",
        "IBAN FR76 2010 3000",
    ],
)
def test_extract_text_dates_does_not_read_amounts_or_identifiers_as_years(text: str) -> None:
    assert extract_text_dates(text).years == ()


def test_extract_text_dates_reads_a_year_at_the_end_of_a_sentence() -> None:
    assert extract_text_dates("It started in 2025. Then, in 2024, it stopped.").years == (
        2024,
        2025,
    )


def test_extract_text_dates_includes_the_year_of_a_complete_date() -> None:
    dates = extract_text_dates("sent on 2026-03-05")
    assert dates.years == (2026,)
    assert dates.latest_bound == date(2026, 3, 5)
