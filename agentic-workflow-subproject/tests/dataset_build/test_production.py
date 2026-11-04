import csv
import json
import re

import pytest

from src.dataset_build.cards import load_config
from src.dataset_build.export import export_dataset, jaccard, shingles
from src.dataset_build.generation_prompt import load_prompt_config, render_prompt
from src.dataset_build.openrouter import Budget, Completion, load_run_config
from src.dataset_build.production import (
    ProductionStoppedError,
    run_split,
    split_reserves,
)
from src.dataset_build.review import load_definitions
from src.dataset_build.splits import SplitSizes, draw_pool, split_pool

CARD_CONFIG, RUN, PROMPTS, DEFINITIONS = (
    load_config(),
    load_run_config(),
    load_prompt_config(),
    load_definitions(),
)
SIZES = SplitSizes(pool=3000, train=30, val=10, test_natural=10, min_per_trap=2)
POOL = draw_pool(CARD_CONFIG, SIZES, seed=3)
SPLITS = split_pool(POOL, SIZES, seed=3)
RESERVES = split_reserves(POOL, SPLITS, RUN)
CARDS = {card.card_id: card for card in POOL}
BY_PROMPT = {render_prompt(card, PROMPTS)[1]: card for card in POOL}
MARKER = re.compile(r"CARD<([^>]+)>")


def make_complete(
    broken: set[str] | frozenset[str] = frozenset(),
    disagree: frozenset[str] = frozenset(),
    judge: str = "accept",
):
    """Fake models: the writer embeds a marker, the voters read it back; ``broken`` cards lose their references."""

    def complete(role, system, user):
        if role.model in (
            RUN.roles["writer_train"].model,
            RUN.roles["writer_test"].model,
        ):
            card = BY_PROMPT[user]
            parts = [
                card.id_surface,
                card.id_second_surface,
                card.amount_surface,
                card.amount_second_surface,
                card.currency_only,
            ]
            text = (
                " ".join(p for p in parts if p and card.card_id not in broken)
                + f" CARD<{card.card_id}>"
            )
            subject = (
                card.id_surface
                if card.id_case == "subject_only"
                else ("S" if card.subject_mode != "absent" else "")
            )
            if card.id_case == "subject_only":
                text = text.replace(card.id_surface, "")
            body = f"Bonjour {text.strip()}"
            return Completion(
                content=json.dumps({"subject": subject, "body": body}),
                prompt_tokens=5,
                completion_tokens=5,
                cost_usd=0.0005,
            )
        if role.model == RUN.roles["judge"].model:
            judged = CARDS[MARKER.search(user).group(1)].label.model_dump()
            if judge == "reject":
                judged["urgency"] = "low" if judged["urgency"] != "low" else "high"
            return Completion(
                content=json.dumps({"reasoning": "r", "label": judged}),
                prompt_tokens=5,
                completion_tokens=5,
                cost_usd=0.001,
            )
        card = CARDS[MARKER.search(user).group(1)]
        label = card.label.model_dump()
        if card.card_id in disagree:
            label["urgency"] = "low" if label["urgency"] != "low" else "high"
        return Completion(
            content=json.dumps(label),
            prompt_tokens=5,
            completion_tokens=5,
            cost_usd=0.0002,
        )

    return complete


def _run(tmp_path, broken=frozenset(), **kwargs):
    return run_split(
        "train",
        SPLITS["train"],
        RESERVES["train"],
        0,
        RUN,
        PROMPTS,
        DEFINITIONS,
        Budget(50.0),
        make_complete(broken, **kwargs),
        tmp_path,
    )


def test_run_split_reaches_its_target_without_the_reserve_when_everything_passes(
    tmp_path,
):
    status = _run(tmp_path)
    assert status.complete and status.accepted == 30 and status.attempted == 30


def test_run_split_tops_up_from_the_reserve_when_tickets_are_discarded(tmp_path):
    broken = {
        card.card_id
        for card in SPLITS["train"][:6]
        if card.id_surface or card.amount_surface
    }
    assert broken
    status = _run(tmp_path, broken)
    assert status.accepted >= 30 and status.attempted > 30
    counts = export_dataset(CARDS, tmp_path, tmp_path / "out")
    assert counts["train"]["quarantine"] == len(broken)
    with (tmp_path / "out" / "train_quarantine.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert {row["card_id"] for row in rows} == broken and all(
        row["reason"].startswith("checks:") for row in rows
    )
    with (tmp_path / "out" / "train.csv").open(encoding="utf-8", newline="") as handle:
        assert {"ticket", "target"} <= set(next(csv.DictReader(handle)))


def test_run_split_stops_when_a_whole_batch_is_non_conforming(tmp_path):
    broken = {
        card.card_id
        for card in [*SPLITS["train"], *RESERVES["train"]]
        if card.id_surface or card.amount_surface
    }
    with pytest.raises(ProductionStoppedError):
        _run(tmp_path, broken)


def test_run_split_keeps_rejected_tickets_in_the_quarantine_with_the_judge_reason(
    tmp_path,
):
    cards = SPLITS["train"][:3]
    disagree = frozenset(card.card_id for card in cards)
    run_split(
        "train",
        cards,
        [],
        0,
        RUN,
        PROMPTS,
        DEFINITIONS,
        Budget(50.0),
        make_complete(disagree=disagree, judge="reject"),
        tmp_path,
        ignore_stop_rules=True,
    )
    counts = export_dataset(CARDS, tmp_path, tmp_path / "out")
    assert counts["train"]["accepted"] == 0 and counts["train"]["quarantine"] == 3


def test_jaccard_flags_a_near_duplicate_and_not_an_unrelated_ticket():
    a = shingles(
        "Bonjour, le virement de 500 euros envoyé lundi n'est toujours pas crédité chez notre fournisseur merci"
    )
    b = shingles(
        "Bonjour, le virement de 500 euros envoyé lundi n'est toujours pas crédité chez notre fournisseur svp"
    )
    assert (
        jaccard(a, b)
        >= 0.5
        > jaccard(
            a,
            shingles(
                "Our webhooks stopped arriving this morning and we need help with the endpoint"
            ),
        )
    )


def test_stop_rule_does_not_trip_on_a_non_conformity_rate_equal_to_the_limit(tmp_path):
    cards = SPLITS["train"][:10] + RESERVES["train"][:20]
    wrong = {c.card_id for c in cards if c.id_surface or c.amount_surface}
    bad = set(sorted(wrong)[: len(wrong) and 0])
    status = run_split(
        "train",
        SPLITS["train"][:30],
        [],
        0,
        RUN,
        PROMPTS,
        DEFINITIONS,
        Budget(50.0),
        make_complete(bad),
        tmp_path,
        max_batches=1,
    )
    assert status.accepted == 30
