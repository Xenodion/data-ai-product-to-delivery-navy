"""Read-only audit of the ticket deck: the evidence that fixes the builder's rules.

Run ``uv run python -m flow.world.audit``. The report holds counts and card identifiers only, never
ticket text. Earlier versions also reported continuation signals, look-alike references and joint
sampling cells; they fed a sampler built for rare-case coverage and were removed with it.
"""

import argparse
import logging
import re
import statistics
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Sequence
from datetime import date, timedelta
from pathlib import Path

from flow.world.config import DEFAULT_CONFIG_PATH, WorldConfig, load_world_config
from flow.world.deck import DeckTicket, load_deck
from flow.world.text_signals import extract_references, extract_text_dates

LOGGER = logging.getLogger(__name__)
UNDEFINED = "UNDEFINED"
MAX_FAILURE_EXAMPLES = 5


def _state(value: str) -> str:
    if value == "":
        return "empty"
    return "UNDEFINED" if value == UNDEFINED else "present"


def _table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines.extend("| " + " | ".join(str(cell) for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def _count_table(title: str, counter: Counter[str]) -> str:
    rows = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    return f"### {title}\n\n" + _table(("value", "tickets"), rows)


def _cross(
    deck: Sequence[DeckTicket],
    row_key: Callable[[DeckTicket], str],
    column_key: Callable[[DeckTicket], str],
) -> str:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    columns: set[str] = set()
    for ticket in deck:
        row, column = row_key(ticket), column_key(ticket)
        counts[row][column] += 1
        columns.add(column)
    ordered = sorted(columns)
    rows = [
        (row, *(counts[row][column] for column in ordered), sum(counts[row].values()))
        for row in sorted(counts)
    ]
    return _table(("", *ordered, "total"), rows)


def _extractor_validation(deck: Sequence[DeckTicket]) -> str:
    stats: dict[str, Counter[str]] = defaultdict(Counter)
    failures: dict[str, list[str]] = defaultdict(list)
    for ticket in deck:
        annotated = ticket.label.transaction_id
        if _state(annotated) != "present":
            continue
        digits = annotated.removeprefix("TX-")
        ok = annotated in extract_references(ticket.text) or digits in ticket.text
        stats[ticket.id_case]["total"] += 1
        stats[ticket.id_case]["matched"] += int(ok)
        if not ok and len(failures[ticket.id_case]) < MAX_FAILURE_EXAMPLES:
            failures[ticket.id_case].append(ticket.card_id)
    rows = [
        (case, c["matched"], c["total"], ", ".join(failures[case]) or "-")
        for case, c in sorted(stats.items())
    ]
    table = _table(
        ("id_case", "annotated id found in text", "tickets with annotated id", "failures"), rows
    )
    malformed = [t for t in deck if t.id_case == "malformed"]
    clean = sum(1 for t in malformed if not extract_references(t.text))
    return (
        table
        + f"\n\nTickets of id_case malformed with no well-formed TX reference: {clean} of "
        + f"{len(malformed)}."
    )


def _dates_section(deck: Sequence[DeckTicket], reference: date) -> str:
    years: Counter[str] = Counter()
    with_full = after_reference = 0
    for ticket in deck:
        dates = extract_text_dates(ticket.text)
        years.update(str(year) for year in dates.years)
        with_full += bool(dates.full_dates)
        bound = dates.latest_bound
        after_reference += bound is not None and bound > reference
    return (
        f"Tickets citing a complete date: {with_full}. Tickets dated after the reference date "
        f"{reference} (excluded from every role): {after_reference}.\n\n"
        "Year matches exclude amounts (2,035.00), identifiers (INV-2026-0042) and references such "
        "as 2016/679; years below 2020 are not matched.\n\n"
        + _table(("year", "tickets"), sorted(years.items()))
    )


def _stale_section(deck: Sequence[DeckTicket], cutoff: date) -> str:
    """Tickets of the current and dev pools that cite a date older than the cutoff."""
    rows = []
    for split in ("test_natural", "val"):
        tickets = [t for t in deck if t.split == split]
        stale = 0
        for ticket in tickets:
            latest = extract_text_dates(ticket.text).latest_full_date
            stale += latest is not None and latest < cutoff
        rows.append((split, stale, len(tickets)))
    return (
        f"A current or dev ticket may not cite a complete date before {cutoff}; those tickets stay "
        "available as history.\n\n"
        + _table(("split", "tickets citing an older date", "tickets"), rows)
    )


def _amount_quantiles(deck: Sequence[DeckTicket], fx_to_eur: dict[str, float]) -> str:
    """Quantiles of annotated amounts in EUR, the evidence for the merchant volume tiers."""
    by_sector: dict[str, list[float]] = defaultdict(list)
    skipped = 0
    for ticket in deck:
        label = ticket.label
        if _state(label.amount) != "present":
            continue
        rate = fx_to_eur.get(label.currency if _state(label.currency) == "present" else "EUR")
        if rate is None:
            skipped += 1
            continue
        by_sector[ticket.sector].append(float(label.amount) * rate)
    rows = []
    for sector in sorted(by_sector):
        values = sorted(by_sector[sector])
        cuts = statistics.quantiles(values, n=100, method="inclusive")
        rows.append(
            (sector, len(values))
            + tuple(f"{cuts[index]:,.0f}" for index in (49, 65, 89, 98))
            + (f"{values[-1]:,.0f}",)
        )
    note = (
        "Amounts converted with the placeholder constants of `fx_to_eur`; a ticket with an amount "
        "and no currency counts as EUR."
    )
    if skipped:
        note += f" {skipped} tickets use a currency without a rate and are skipped."
    return note + "\n\n" + _table(("sector", "amounts", "p50", "p66", "p90", "p99", "max"), rows)


def build_audit(
    deck: Sequence[DeckTicket],
    reference: date,
    quarantine_bytes: dict[str, int],
    fx_to_eur: dict[str, float] | None = None,
    cited_date_cutoff: date | None = None,
) -> str:
    """Render the audit report as Markdown."""
    sections = [
        "# Deck audit",
        (
            f"Reference date: {reference}. Tickets: {len(deck)}. "
            "Generated by `python -m flow.world.audit`; counts and card identifiers only."
        ),
        "## 1. Splits, sectors, languages",
        _count_table("Tickets per split", Counter(t.split for t in deck)),
        _count_table("Tickets per sector", Counter(t.sector for t in deck)),
        _count_table("Tickets per language", Counter(t.language for t in deck)),
        "### Sector x split\n\n" + _cross(deck, lambda t: t.sector, lambda t: t.split),
        "## 2. id_case against the annotated transaction_id\n\n"
        + _cross(deck, lambda t: t.id_case, lambda t: _state(t.label.transaction_id)),
        "## 3. Annotated amount and currency\n\n"
        + "Amount state x currency state:\n\n"
        + _cross(deck, lambda t: _state(t.label.amount), lambda t: _state(t.label.currency)),
        _count_table("Annotated currencies", Counter(t.label.currency or "(empty)" for t in deck)),
        "## 4. Reference extractor, validated on the annotations\n\n" + _extractor_validation(deck),
        "## 5. Dates cited in ticket text\n\n" + _dates_section(deck, reference),
    ]
    if cited_date_cutoff is not None:
        sections.append(
            "## 6. Stale dates in current and dev pools\n\n"
            + _stale_section(deck, cited_date_cutoff)
        )
    sections += [
        "## 7. Amount quantiles in EUR (merchant tier evidence)\n\n"
        + _amount_quantiles(deck, fx_to_eur or {"EUR": 1.0}),
        "## 8. Quarantine files (size only, never opened)\n\n"
        + _table(("file", "bytes"), sorted(quarantine_bytes.items())),
    ]
    return "\n\n".join(sections) + "\n"


def quarantine_sizes(deck_dir: Path) -> dict[str, int]:
    """File sizes of the quarantine files; the files themselves are not opened."""
    return {path.name: path.stat().st_size for path in sorted(deck_dir.glob("*_quarantine.csv"))}


def run_audit(config: WorldConfig) -> Path:
    """Write the audit report under the artifacts folder and return its path."""
    deck_dir = config.resolve(config.paths.deck_dir)
    deck = load_deck(deck_dir, config.text_newline)
    cutoff = config.window_end - timedelta(days=config.dates.max_cited_age_days)
    report = build_audit(
        deck, config.reference_date, quarantine_sizes(deck_dir), config.fx_to_eur, cutoff
    )
    target = config.resolve(config.paths.artifacts_dir) / "reports" / "deck_audit.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(re.sub(r"[ \t]+\n", "\n", report), encoding="utf-8")
    LOGGER.info("deck audit written: %s", target)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    arguments = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_audit(load_world_config(arguments.config))


if __name__ == "__main__":
    main()
