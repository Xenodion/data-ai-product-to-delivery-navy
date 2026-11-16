"""Build the world database from the deck: ``python -m flow.world.build``."""

import argparse
import hashlib
import json
import logging
import sqlite3
from collections.abc import Sequence
from datetime import UTC, date, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from flow.world.config import DEFAULT_CONFIG_PATH, WorldConfig, load_world_config
from flow.world.deck import DeckTicket, load_deck
from flow.world.errors import ValidationFailure
from flow.world.ledger import build_ledger, build_money_objects
from flow.world.models import TABLE_MODELS, Message, TicketOutcome
from flow.world.oracle import export_oracle
from flow.world.policies import load_policies
from flow.world.provenance import code_version, input_hashes
from flow.world.sampling import sample_roles
from flow.world.timeline import build_people
from flow.world.validate import STAMP_FORMAT, validate_world

LOGGER = logging.getLogger(__name__)
SCHEMA_PATH = Path(__file__).with_name("schema.sql")
TABLE_ORDER = tuple(TABLE_MODELS)  # parents come before the tables that reference them


class WorldManifest(BaseModel):
    """What a build produced; it holds no ticket text."""

    model_config = ConfigDict(frozen=True)

    seed: int
    sample_hash: str
    inputs: dict[str, str]
    row_counts: dict[str, int]
    shared_references: tuple[str, ...]
    content_hash: str
    code_version: str
    threads_log_sha256: str | None = None


def _cell(value: object) -> object:
    if isinstance(value, datetime):
        return value.astimezone(UTC).strftime(STAMP_FORMAT)
    if isinstance(value, date):
        return value.isoformat()
    return value


def _insert(conn: sqlite3.Connection, table: str, rows: Sequence[BaseModel]) -> None:
    if not rows:
        return
    columns = list(TABLE_MODELS[table].model_fields)
    marks = ", ".join("?" for _ in columns)
    conn.executemany(
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({marks})",
        [tuple(_cell(getattr(row, column)) for column in columns) for row in rows],
    )


def content_hash(conn: sqlite3.Connection) -> str:
    """Hash every table, rows ordered by all columns, so that two builds can be compared."""
    digest = hashlib.sha256()
    for table in sorted(TABLE_ORDER):
        count = len(TABLE_MODELS[table].model_fields)
        order = ", ".join(str(position) for position in range(1, count + 1))
        digest.update(table.encode())
        for row in conn.execute(f"SELECT * FROM {table} ORDER BY {order}"):
            digest.update(json.dumps(row, ensure_ascii=False).encode("utf-8"))
    return digest.hexdigest()


def load_threads(path: Path) -> tuple[list[Message], list[TicketOutcome]]:
    """Messages 2..n and outcomes of the accepted-thread log (one JSON record per line)."""
    messages: list[Message] = []
    outcomes: list[TicketOutcome] = []
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        ticket_id = record["ticket_id"]
        if ticket_id in seen:
            raise ValidationFailure(f"thread log holds {ticket_id} twice")
        seen.add(ticket_id)
        messages += [
            Message(
                message_id=f"{ticket_id}:{m['turn_index']}",
                ticket_id=ticket_id,
                turn_index=m["turn_index"],
                direction="outbound" if m["author_kind"] == "agent" else "inbound",
                sent_at=m["sent_at"],
                body=m["body"],
                author_kind=m["author_kind"],
            )
            for m in record["messages"]
        ]
        if record["outcome"]:
            outcomes.append(TicketOutcome(ticket_id=ticket_id, **record["outcome"]))
    return messages, outcomes


def build_world(
    deck_tickets: Sequence[DeckTicket],
    config: WorldConfig,
    knowledge_path: Path,
    database_path: Path,
    oracle_dir: Path | None = None,
    inputs: dict[str, str] | None = None,
    version: str = "",
    threads_log: Path | None = None,
) -> WorldManifest:
    """Run every stage, validate, and write the database atomically (no generated messages).

    Raises:
        ValidationFailure: an invariant is broken; nothing is written.
    """
    manifest = sample_roles(deck_tickets, config, inputs, version)
    book, tickets, deck = build_people(deck_tickets, manifest, config)
    selected = {item.card_id: item for item in manifest.tickets}
    ledger = build_ledger(tickets, deck, selected, book, config)
    refunds, disputes, payouts = build_money_objects(ledger, tickets, deck, book, config)
    policies, links = load_policies(knowledge_path, config)
    messages = [
        Message(
            message_id=f"{ticket.ticket_id}:1",
            ticket_id=ticket.ticket_id,
            turn_index=1,
            direction="inbound",
            sent_at=ticket.opened_at,
            body=deck[ticket.ticket_id].text,
            author_kind="merchant",
        )
        for ticket in tickets
    ]
    outcomes: list[TicketOutcome] = []
    if threads_log is not None:
        written, outcomes = load_threads(threads_log)
        history = {t.ticket_id for t in tickets if t.role == "history"}
        if {m.ticket_id for m in written} != history:
            raise ValidationFailure("the thread log must hold exactly the history tickets")
        messages += written
    tables: dict[str, Sequence[BaseModel]] = {
        "merchants": book.merchants,
        "merchant_currencies": book.currencies,
        "contacts": book.contacts,
        "transactions": ledger.transactions,
        "refunds": refunds,
        "disputes": disputes,
        "payouts": payouts,
        "tickets": tickets,
        "ticket_outcomes": outcomes,
        "messages": messages,
        "policies": policies,
        "policy_sub_intents": links,
    }
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    for name in TABLE_ORDER:
        _insert(conn, name, tables[name])
    problems = validate_world(
        conn, manifest.tickets, deck, ledger.shared_references, config, threads_log is not None
    )
    if problems:
        conn.close()
        raise ValidationFailure(f"{len(problems)} violations, first: {problems[:5]}")
    counts = {
        name: conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0] for name in TABLE_ORDER
    }
    digest = content_hash(conn)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = database_path.with_suffix(".tmp")
    temporary.unlink(missing_ok=True)
    conn.commit()
    conn.execute("VACUUM INTO ?", (str(temporary),))
    conn.close()
    temporary.replace(database_path)
    if oracle_dir is not None:
        export_oracle(manifest.tickets, deck, oracle_dir)
    return WorldManifest(
        seed=config.seed,
        sample_hash=manifest.content_hash,
        inputs=manifest.inputs,
        row_counts=counts,
        shared_references=ledger.shared_references,
        content_hash=digest,
        code_version=version,
        threads_log_sha256=(
            hashlib.sha256(threads_log.read_bytes()).hexdigest() if threads_log else None
        ),
    )


def main() -> None:
    """Build the world v0 database and write its manifest next to the other reports."""
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--threads", type=Path, help="accepted-thread log to ingest (world v1)")
    arguments = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    config = load_world_config(arguments.config)
    deck_dir = config.resolve(config.paths.deck_dir)
    manifest = build_world(
        load_deck(deck_dir, config.text_newline),
        config,
        config.resolve(config.paths.knowledge_path),
        config.resolve(config.paths.database_path),
        config.resolve(config.paths.oracle_dir),
        input_hashes(deck_dir, arguments.config),
        code_version(arguments.config.parent),
        arguments.threads,
    )
    target = config.resolve(config.paths.artifacts_dir) / "reports" / "world_manifest.json"
    payload = json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True)
    target.write_text(payload + "\n", encoding="utf-8", newline="\n")
    LOGGER.info("world built: %s; content hash %s", manifest.row_counts, manifest.content_hash)


if __name__ == "__main__":
    main()
