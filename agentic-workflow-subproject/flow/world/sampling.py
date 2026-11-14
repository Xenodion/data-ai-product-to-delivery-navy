"""Seeded random sampling of the deck into the roles ``current``, ``history`` and ``dev``.

The draw follows the natural distribution of each pool: no quota, no floor, no oversampling of
rare cases. Every exclusion is applied to the candidates before the draw, so the draw itself stays
unbiased and never loops.
"""

import argparse
import hashlib
import json
import logging
from collections.abc import Sequence
from datetime import date, timedelta
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from flow.world.config import DEFAULT_CONFIG_PATH, WorldConfig, load_world_config
from flow.world.deck import DeckTicket, Split, load_deck
from flow.world.errors import SamplingError
from flow.world.provenance import code_version, input_hashes
from flow.world.rng import stage_rng
from flow.world.text_signals import extract_text_dates

LOGGER = logging.getLogger(__name__)

Role = Literal["current", "history", "dev"]
CURRENT_SPLITS: frozenset[Split] = frozenset({"test_natural"})
DEV_SPLITS: frozenset[Split] = frozenset({"val"})
HISTORY_SPLITS: frozenset[Split] = frozenset({"train", "val"})
REASON_AFTER_REFERENCE = "text_date_after_reference"
REASON_CITED_DATE_TOO_OLD = "cited_date_too_old"


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Candidate(_Frozen):
    """A deck ticket reduced to what sampling and dating need (no text)."""

    card_id: str
    split: Split
    latest_bound: date | None
    latest_full_date: date | None
    earliest_full_date: date | None


class Excluded(_Frozen):
    """A candidate kept out of a role, with the reason, so that exclusions are countable."""

    card_id: str
    role: str
    reason: str
    detail: str


class SelectedTicket(_Frozen):
    card_id: str
    split: Split
    role: Role
    latest_bound: date | None
    earliest_full_date: date | None


class SampleManifest(_Frozen):
    """Everything needed to reproduce and audit the sample; it holds no ticket text."""

    seed: int
    reference_date: date
    sizes: dict[str, int]
    pool_sizes: dict[str, int]
    inputs: dict[str, str]
    tickets: tuple[SelectedTicket, ...]
    excluded: tuple[Excluded, ...]
    code_version: str
    content_hash: str


def build_candidates(deck: Sequence[DeckTicket]) -> tuple[Candidate, ...]:
    """Reduce the deck to candidates, in card order."""
    candidates = []
    for ticket in sorted(deck, key=lambda item: item.card_id):
        dates = extract_text_dates(ticket.text)
        candidates.append(
            Candidate(
                card_id=ticket.card_id,
                split=ticket.split,
                latest_bound=dates.latest_bound,
                latest_full_date=dates.latest_full_date,
                earliest_full_date=dates.earliest_full_date,
            )
        )
    return tuple(candidates)


def _exclusions(
    candidates: Sequence[Candidate], config: WorldConfig, role: str, check_age: bool
) -> tuple[list[Candidate], list[Excluded]]:
    """Split candidates into usable ones and exclusions for a role."""
    oldest_allowed = config.window_end - timedelta(days=config.dates.max_cited_age_days)
    usable: list[Candidate] = []
    excluded: list[Excluded] = []
    for candidate in candidates:
        bound = candidate.latest_bound
        if bound is not None and bound > config.reference_date:
            excluded.append(
                Excluded(
                    card_id=candidate.card_id,
                    role=role,
                    reason=REASON_AFTER_REFERENCE,
                    detail=bound.isoformat(),
                )
            )
        elif (
            check_age and candidate.latest_full_date and candidate.latest_full_date < oldest_allowed
        ):
            excluded.append(
                Excluded(
                    card_id=candidate.card_id,
                    role=role,
                    reason=REASON_CITED_DATE_TOO_OLD,
                    detail=candidate.latest_full_date.isoformat(),
                )
            )
        else:
            usable.append(candidate)
    return usable, excluded


def _draw(
    pool: Sequence[Candidate], size: int, stage: str, seed: int, role: str
) -> list[Candidate]:
    if size > len(pool):
        raise SamplingError(f"role {role} needs {size} tickets but the pool holds {len(pool)}")
    return stage_rng(seed, stage).sample(sorted(pool, key=lambda item: item.card_id), size)


def _selected(candidate: Candidate, role: Role) -> SelectedTicket:
    return SelectedTicket(
        card_id=candidate.card_id,
        split=candidate.split,
        role=role,
        latest_bound=candidate.latest_bound,
        earliest_full_date=candidate.earliest_full_date,
    )


def sample_roles(
    deck: Sequence[DeckTicket],
    config: WorldConfig,
    inputs: dict[str, str] | None = None,
    version: str = "",
) -> SampleManifest:
    """Draw the tickets of each role; ``dev`` is drawn before ``history`` so they stay disjoint.

    ``current`` and ``dev`` tickets may not cite an old date (they would look stale when opened
    days before the end of the window); ``history`` tickets may.
    """
    candidates = build_candidates(deck)
    current_pool, current_out = _exclusions(
        [c for c in candidates if c.split in CURRENT_SPLITS], config, "current", check_age=True
    )
    dev_pool, dev_out = _exclusions(
        [c for c in candidates if c.split in DEV_SPLITS], config, "dev", check_age=True
    )
    sample, seed = config.sample, config.seed
    current = _draw(current_pool, sample.current, "sample:current", seed, "current")
    dev = _draw(dev_pool, sample.dev, "sample:dev", seed, "dev")
    dev_ids = {c.card_id for c in dev}
    history_pool, history_out = _exclusions(
        [c for c in candidates if c.split in HISTORY_SPLITS and c.card_id not in dev_ids],
        config,
        "history",
        check_age=False,
    )
    history = _draw(history_pool, sample.history, "sample:history", seed, "history")
    tickets = tuple(
        sorted(
            (
                *(_selected(c, "current") for c in current),
                *(_selected(c, "history") for c in history),
                *(_selected(c, "dev") for c in dev),
            ),
            key=lambda item: (item.role, item.card_id),
        )
    )
    draft = SampleManifest(
        seed=seed,
        reference_date=config.reference_date,
        sizes={"current": sample.current, "history": sample.history, "dev": sample.dev},
        pool_sizes={
            "current": len(current_pool),
            "history": len(history_pool),
            "dev": len(dev_pool),
        },
        inputs=inputs or {},
        tickets=tickets,
        excluded=(*current_out, *dev_out, *history_out),
        code_version=version,
        content_hash="",
    )
    return draft.model_copy(update={"content_hash": _hash(draft)})


def _hash(manifest: SampleManifest) -> str:
    """Hash the outputs and the declared inputs; the code version is volatile and left out."""
    payload = manifest.model_dump(mode="json", exclude={"content_hash", "code_version"})
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def write_manifest(manifest: SampleManifest, path: Path) -> None:
    """Write the manifest atomically as sorted, indented JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(
        manifest.model_dump(mode="json"), sort_keys=True, indent=2, ensure_ascii=False
    )
    temporary.write_text(payload + "\n", encoding="utf-8")
    temporary.replace(path)
    LOGGER.info("sample manifest written: %s (%d tickets)", path, len(manifest.tickets))


def main() -> None:
    """Sample the deck and write ``sample_manifest.json`` next to the audit report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    arguments = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    config = load_world_config(arguments.config)
    deck_dir = config.resolve(config.paths.deck_dir)
    manifest = sample_roles(
        load_deck(deck_dir, config.text_newline),
        config,
        inputs=input_hashes(deck_dir, arguments.config),
        version=code_version(arguments.config.parent),
    )
    target = config.resolve(config.paths.artifacts_dir) / "reports" / "sample_manifest.json"
    write_manifest(manifest, target)
    LOGGER.info("content hash: %s; excluded: %d", manifest.content_hash, len(manifest.excluded))


if __name__ == "__main__":
    main()
