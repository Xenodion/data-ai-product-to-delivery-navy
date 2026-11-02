import json

import pytest

from src.dataset_build.cards import draw_cards, load_config
from src.dataset_build.checks import check_ticket
from src.dataset_build.generation_prompt import load_prompt_config
from src.dataset_build.openrouter import (
    ApiError,
    Budget,
    BudgetExhaustedError,
    Completion,
    load_run_config,
    parse_ticket_json,
)
from src.dataset_build.runner import read_log, write_tickets

CARDS = draw_cards(load_config(), "train", 400, seed=21)
PROMPTS = load_prompt_config()
RUN = load_run_config()


def _card(predicate):
    return next(card for card in CARDS if predicate(card))


def _good_ticket(card):
    parts = [
        card.id_surface,
        card.id_second_surface,
        card.amount_surface,
        card.amount_second_surface,
        card.currency_only,
    ]
    body = "Bonjour, " + " ".join(part for part in parts if part) + " merci."
    if card.id_case == "subject_only":
        return card.id_surface, " ".join(part for part in parts[1:] if part) + " merci."
    return ("Question" if card.subject_mode != "absent" else ""), body


def test_check_ticket_accepts_a_ticket_that_carries_its_surface_forms():
    card = _card(
        lambda c: (
            c.id_case == "canonical"
            and c.amount_case == "plain"
            and c.subject_mode == "present"
        )
    )
    assert check_ticket(card, *_good_ticket(card)) == []


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda card, s, b: (s, b.replace(card.id_surface, "")), "surface_missing"),
        (lambda card, s, b: (s, b + " voir aussi TX-111111"), "extra_reference"),
        (lambda card, s, b: (s, b + " soit 500 EUR de plus"), "extra_currency"),
        (lambda card, s, b: ("", b), "subject_mode_not_respected"),
    ],
)
def test_check_ticket_flags_bad_tickets(mutate, code):
    card = _card(
        lambda c: (
            c.id_case == "canonical"
            and c.amount_case == "plain"
            and c.subject_mode == "present"
        )
    )
    subject, body = _good_ticket(card)
    assert code in check_ticket(card, *mutate(card, subject, body))


def test_check_ticket_flags_a_subject_only_reference_repeated_in_the_body():
    card = _card(lambda c: c.id_case == "subject_only")
    subject, body = _good_ticket(card)
    assert "reference_not_in_subject_only" in check_ticket(
        card, subject, body + " " + card.id_surface
    )


def test_parse_ticket_json_tolerates_a_markdown_fence_and_rejects_garbage():
    assert parse_ticket_json('```json\n{"subject": "s", "body": "b"}\n```') == (
        "s",
        "b",
    )
    with pytest.raises(TypeError):
        parse_ticket_json('{"subject": "s"}')


def test_budget_ensure_raises_before_crossing_the_limit():
    budget = Budget(limit_usd=1.0, spent_usd=0.9)
    budget.ensure(0.05)
    with pytest.raises(BudgetExhaustedError):
        budget.ensure(0.2)


def test_write_tickets_logs_keeps_good_discards_bad_and_resumes_without_new_calls(
    tmp_path,
):
    cards = [c for c in CARDS if c.id_case == "canonical" and c.amount_case == "plain"][
        :6
    ]
    calls: list[str] = []

    def fake_complete(role, system, user):
        calls.append(user)
        card = cards[len(calls) - 1]
        subject, body = _good_ticket(card)
        if len(calls) == 2:
            body = "no reference at all"
        return Completion(
            content=json.dumps({"subject": subject, "body": body}),
            prompt_tokens=400,
            completion_tokens=100,
            cost_usd=0.001,
        )

    log = tmp_path / "calls.jsonl"
    budget = Budget(limit_usd=1.0)
    write_tickets(cards, "writer_train", RUN, PROMPTS, log, budget, fake_complete)
    records = read_log(log)
    assert len(records) == 6 and records[1].status == "discarded"
    assert abs(budget.spent_usd - 0.006) < 1e-9
    write_tickets(cards, "writer_train", RUN, PROMPTS, log, budget, fake_complete)
    assert len(calls) == 6


def test_write_tickets_stops_when_the_budget_is_too_small(tmp_path):
    with pytest.raises(BudgetExhaustedError):
        write_tickets(
            CARDS[:2],
            "writer_train",
            RUN,
            PROMPTS,
            tmp_path / "c.jsonl",
            Budget(limit_usd=0.0),
            lambda *a: None,
        )


def test_write_tickets_stops_after_consecutive_api_errors(tmp_path):
    def failing(role, system, user):
        raise ApiError("bad request")

    with pytest.raises(ApiError):
        write_tickets(
            CARDS[:10],
            "writer_train",
            RUN,
            PROMPTS,
            tmp_path / "c.jsonl",
            Budget(limit_usd=1.0),
            failing,
        )


def test_check_ticket_flags_urgency_wording_on_a_low_urgency_card():
    card = _card(
        lambda c: (
            c.label.urgency == "low"
            and c.id_case == "canonical"
            and c.amount_case == "plain"
        )
    )
    subject, body = _good_ticket(card)
    assert "urgency_wording_on_low" in check_ticket(
        card, subject, body + " C'est URGENT"
    )


def test_check_ticket_flags_a_truncated_card_whose_text_ends_cleanly():
    card = _card(
        lambda c: (
            c.sentinel_kind == "truncated"
            and not ({"signature", "disclaimer", "quoted_thread"} & set(c.noise))
        )
    )
    assert "not_truncated" in check_ticket(
        card, "S" if card.subject_mode != "absent" else "", "The message is complete."
    )
    assert "not_truncated" not in check_ticket(
        card,
        "S" if card.subject_mode != "absent" else "",
        "The message is cut in the mid",
    )


def test_check_ticket_accepts_an_ellipsis_as_a_truncation():
    card = _card(
        lambda c: (
            c.sentinel_kind == "truncated"
            and not ({"signature", "disclaimer", "quoted_thread"} & set(c.noise))
        )
    )
    subject = "S" if card.subject_mode != "absent" else ""
    assert "not_truncated" not in check_ticket(
        card, subject, "Nous allons être obligés de..."
    )


def test_parse_ticket_json_repairs_javascript_style_string_concatenation():
    content = '{"subject": "S", "body": "line one\\n" +\n  "line two"}'
    assert parse_ticket_json(content) == ("S", "line one\nline two")
