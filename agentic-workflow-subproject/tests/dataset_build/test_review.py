import json

from src.dataset_build.cards import draw_cards, load_config
from src.dataset_build.openrouter import Budget, Completion, load_run_config
from src.dataset_build.review import (
    differing_fields,
    judge_prompts,
    load_definitions,
    read_reviews,
    review_tickets,
    uses_voter_b,
    voter_prompts,
)
from src.dataset_build.runner import TicketRecord

RUN = load_run_config()
DEFINITIONS = load_definitions()
CARDS = draw_cards(load_config(), "train", 40, seed=31)


def _record(card):
    return TicketRecord(
        card_id=card.card_id,
        role="writer_train",
        model="m",
        status="ok",
        reasons=[],
        subject="",
        body="b",
        ticket="Hello",
        prompt_tokens=1,
        completion_tokens=1,
        cost_usd=0.0,
        prompt_version="v",
    )


def _completion(payload):
    return Completion(
        content=json.dumps(payload),
        prompt_tokens=10,
        completion_tokens=10,
        cost_usd=0.001,
    )


def _fake(card_by_ticket, answers):
    """answers: role model -> callable(card) -> payload; the judge answers a fixed verdict."""

    def complete(role, system, user):
        if role.model == RUN.roles["judge"].model:
            return _completion(answers["judge"])
        return _completion(answers[role.model])

    return complete


def test_voter_prompts_never_contain_the_card_label():
    card = CARDS[0]
    system, user = voter_prompts(DEFINITIONS, "Subject: x\n\nbody")
    assert card.label.model_dump_json() not in system + user


def test_judge_prompts_show_the_ticket_and_never_the_card_label():
    card = CARDS[0]
    system, user = judge_prompts(DEFINITIONS, "My ticket")
    assert "My ticket" in user and card.label.model_dump_json() not in system + user


def _judge_reads(card, same: bool, reasoning: str = "r") -> dict:
    label = card.label.model_dump()
    if not same:
        label["urgency"] = "low" if label["urgency"] != "low" else "high"
    return {"reasoning": reasoning, "label": label}


def test_differing_fields_lists_exactly_the_mismatching_fields():
    card = CARDS[0]
    other = card.label.model_copy(
        update={"urgency": "low" if card.label.urgency != "low" else "high"}
    )
    assert differing_fields(card.label, other) == ["urgency"]


def test_uses_voter_b_is_deterministic_and_respects_the_extremes():
    assert uses_voter_b("x", 1.0) and not uses_voter_b("x", 0.0)
    assert uses_voter_b("abc", 0.5) == uses_voter_b("abc", 0.5)


def test_review_tickets_accepts_without_a_judge_when_every_voter_agrees(tmp_path):
    card = CARDS[0]
    agree = card.label.model_dump()
    answers = {
        RUN.roles["voter_a"].model: agree,
        RUN.roles["voter_b"].model: agree,
        "judge": _judge_reads(card, same=False),
    }
    [record] = review_tickets(
        [(card, _record(card))],
        1.0,
        RUN,
        tmp_path / "r.jsonl",
        Budget(1.0),
        _fake(None, answers),
        DEFINITIONS,
    )
    assert record.final == "accepted" and record.judge_verdict == ""


def test_review_tickets_calls_the_judge_on_disagreement_and_follows_its_verdict(
    tmp_path,
):
    card = CARDS[1]
    wrong = {
        **card.label.model_dump(),
        "urgency": "low" if card.label.urgency != "low" else "high",
    }
    base = {
        RUN.roles["voter_a"].model: card.label.model_dump(),
        RUN.roles["voter_b"].model: wrong,
    }
    rejected = review_tickets(
        [(card, _record(card))],
        1.0,
        RUN,
        tmp_path / "a.jsonl",
        Budget(1.0),
        _fake(None, {**base, "judge": _judge_reads(card, same=False)}),
        DEFINITIONS,
    )
    accepted = review_tickets(
        [(card, _record(card))],
        1.0,
        RUN,
        tmp_path / "b.jsonl",
        Budget(1.0),
        _fake(None, {**base, "judge": _judge_reads(card, same=True)}),
        DEFINITIONS,
    )
    assert rejected[0].final == "rejected" and accepted[0].final == "accepted"


def test_review_tickets_treats_an_unusable_voter_as_an_abstention_and_resumes(tmp_path):
    card = CARDS[2]
    calls = []

    def complete(role, system, user):
        calls.append(role.model)
        if role.model == RUN.roles["voter_a"].model:
            return Completion(
                content="not json", prompt_tokens=1, completion_tokens=1, cost_usd=0.0
            )
        return _completion(card.label.model_dump())

    log = tmp_path / "r.jsonl"
    [record] = review_tickets(
        [(card, _record(card))], 1.0, RUN, log, Budget(1.0), complete, DEFINITIONS
    )
    assert record.votes[0].label is None and record.final == "accepted"
    review_tickets(
        [(card, _record(card))], 1.0, RUN, log, Budget(1.0), complete, DEFINITIONS
    )
    assert len(calls) == 2 and len(read_reviews(log)) == 1


def test_review_tickets_asks_the_judge_again_when_its_first_answer_is_unusable(
    tmp_path,
):
    card = CARDS[3]
    wrong = {
        **card.label.model_dump(),
        "urgency": "low" if card.label.urgency != "low" else "high",
    }
    judge_answers = iter(
        ['{"reasoning": "cut', json.dumps(_judge_reads(card, same=True))]
    )

    def complete(role, system, user):
        if role.model == RUN.roles["judge"].model:
            return Completion(
                content=next(judge_answers),
                prompt_tokens=1,
                completion_tokens=1,
                cost_usd=0.0,
            )
        return _completion(wrong)

    [record] = review_tickets(
        [(card, _record(card))],
        1.0,
        RUN,
        tmp_path / "r.jsonl",
        Budget(1.0),
        complete,
        DEFINITIONS,
    )
    assert record.judge_verdict == "accept" and record.final == "accepted"


def test_rejudge_rejected_recovers_a_ticket_the_new_judge_reads_as_labelled(tmp_path):
    from src.dataset_build.review import rejudge_rejected

    card = CARDS[4]
    wrong = {
        **card.label.model_dump(),
        "urgency": "low" if card.label.urgency != "low" else "high",
    }
    log = tmp_path / "r.jsonl"
    voters = {RUN.roles["voter_a"].model: wrong, RUN.roles["voter_b"].model: wrong}
    review_tickets(
        [(card, _record(card))],
        1.0,
        RUN,
        log,
        Budget(1.0),
        _fake(None, {**voters, "judge": _judge_reads(card, same=False)}),
        DEFINITIONS,
    )
    assert read_reviews(log)[-1].final == "rejected"
    rejudge_rejected(
        [(card, _record(card))],
        RUN,
        log,
        Budget(1.0),
        _fake(None, {"judge": _judge_reads(card, same=True)}),
        DEFINITIONS,
    )
    assert read_reviews(log)[-1].final == "accepted" and len(read_reviews(log)) == 2
