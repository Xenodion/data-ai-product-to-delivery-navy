"""The Drafter answers in JSON segments; the code checks them and builds the reply."""

import json
from collections import deque
from datetime import UTC, datetime

import httpx
import pytest

from flow.contracts import EvidenceDecision, EvidenceFact, QualifierResult, Ticket, load_config
from flow.draft_render import check_segments, parse_reply, pick_language, render, template_question
from flow.drafter import _request_body, write_draft
from flow.llm import DraftRejected

CONFIG = load_config().model_copy(update={"retry_wait_seconds": 0.0})
SOURCE = "kb_compliance_kyc_v1"
FACT = EvidenceFact(field="approved_guidance", value="Send the KYC form.", source_id=SOURCE, source_version="1")
DOCUMENTARY = EvidenceDecision(mode="documentary", reason_codes=("EVIDENCE_READY",), source_ids=(SOURCE,), facts=(FACT,))
CLARIFY = EvidenceDecision(mode="clarification", reason_codes=("PAYMENT_ID_ABSENT",))
QUALIFIER = QualifierResult(status="invalid", label=None, raw="x", model_version="m", latency_seconds=0)


def _ticket(language: str | None = None) -> Ticket:
    return Ticket(
        ticket_id="t1", merchant_id="m1", text="help", created_at=datetime(2026, 11, 5, tzinfo=UTC),
        language=language,
    )


def _answer(*segments: dict[str, object], language: str = "en") -> str:
    return json.dumps({"language": language, "segments": list(segments)})


def _run(contents: list[str], evidence: EvidenceDecision, language: str | None = None):
    queue, bodies = deque(contents), []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        choice = {"message": {"content": queue.popleft()}, "finish_reason": "stop"}
        return httpx.Response(200, json={"choices": [choice], "usage": {"cost": 0.001}})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        draft = write_draft(
            _ticket(language), QUALIFIER, "compliance", 1, client=client, config=CONFIG, evidence=evidence
        )
    return draft, bodies


def test_quotes_greeting_and_sign_off_are_removed_and_rebuilt_by_the_code() -> None:
    raw = _answer(
        {"text": "Hello,", "source_ids": []},
        {"text": '"Please send the KYC form."', "source_ids": [SOURCE]},
        {"text": "Best regards", "source_ids": []},
    )
    _, segments = parse_reply(raw)
    assert [s.text for s in segments] == ["Please send the KYC form."]
    assert render("en", segments, CONFIG) == "Hello,\n\nPlease send the KYC form.\n\nKind regards,\nKeelpay Support"


def test_a_code_fence_around_the_json_is_tolerated() -> None:
    fenced = "```json\n" + _answer({"text": "Ok.", "source_ids": []}) + "\n```"
    assert parse_reply(fenced)[1][0].text == "Ok."


@pytest.mark.parametrize("raw", ["plain prose", "{}", '{"segments": []}', '{"segments": [{"text": "Hello,"}]}'])
def test_an_answer_that_is_not_the_contract_is_rejected(raw: str) -> None:
    with pytest.raises(DraftRejected):
        parse_reply(raw)


def _segments(*items: tuple[str, tuple[str, ...]]):
    return parse_reply(_answer(*({"text": t, "source_ids": list(s)} for t, s in items)))[1]


@pytest.mark.parametrize(
    "text",
    ["Send it to [Your Name].", "Use {merchant}.", "See <link>.", "Signed XXX.", "Thanks, your name"],
)
def test_placeholders_and_brackets_are_rejected(text: str) -> None:
    with pytest.raises(DraftRejected):
        check_segments(_segments((text, (SOURCE,))), "documentary", frozenset({SOURCE}))


def test_an_unknown_source_and_a_documentary_draft_without_source_are_rejected() -> None:
    with pytest.raises(DraftRejected):
        check_segments(_segments(("Fine.", ("kb_other",))), "documentary", frozenset({SOURCE}))
    with pytest.raises(DraftRejected):
        check_segments(_segments(("Fine.", ())), "factual", frozenset({SOURCE}))


def test_a_source_is_rejected_when_no_evidence_was_supplied() -> None:
    with pytest.raises(DraftRejected):
        check_segments(_segments(("Fine.", (SOURCE,))), "clarification", frozenset())


@pytest.mark.parametrize("text", ["Your payment TX-123456 is late.", "See M-0007."])
def test_a_reference_that_is_not_in_the_ticket_or_the_evidence_is_rejected(text: str) -> None:
    with pytest.raises(DraftRejected):
        check_segments(
            _segments(("Per the guidance.", (SOURCE,)), (text, ())), "documentary", frozenset({SOURCE})
        )


def test_a_valid_documentary_answer_returns_the_sources_in_order() -> None:
    segments = _segments(("Send the KYC form.", (SOURCE,)), ("Which entity is it for?", ()))
    assert check_segments(segments, "documentary", frozenset({SOURCE})) == (SOURCE,)


def test_language_comes_from_the_ticket_then_the_model_then_english() -> None:
    assert pick_language("fr", "en", CONFIG) == "fr"
    assert pick_language(None, "de", CONFIG) == "de"
    assert pick_language("pt", "xx", CONFIG) == "en"


def test_every_configured_language_has_a_greeting_a_closing_and_both_template_questions() -> None:
    for language in CONFIG.drafter_greeting:
        assert language in CONFIG.drafter_closing
        assert template_question(language, (), CONFIG).count("\n\n") == 2
        assert "TX-123456" in template_question(language, ("PAYMENT_ID_ABSENT",), CONFIG)


def test_the_request_asks_for_json_and_forbids_dropping_the_parameter() -> None:
    body = _request_body(CONFIG, [{"role": "user", "content": "x"}])
    assert body["response_format"] == {"type": "json_object"}
    assert body["provider"] == {"require_parameters": True}
    off = _request_body(CONFIG.model_copy(update={"drafter_response_format": "none"}), [])
    assert "response_format" not in off and "provider" not in off


def test_write_draft_documentary_success_records_sources_and_versions() -> None:
    good = _answer({"text": "Send the KYC form.", "source_ids": [SOURCE]}, language="fr")
    draft, bodies = _run([good], DOCUMENTARY)
    assert draft.source_ids == (SOURCE,) and draft.source_versions == ((SOURCE, "1"),)
    assert draft.attempts == 1
    assert draft.text.startswith("Bonjour,") and "[" not in draft.text
    assert "JSON object only" in bodies[0]["messages"][-1]["content"]  # the code states the format


def test_a_bad_first_answer_is_repaired_once() -> None:
    good = _answer({"text": "Send the KYC form.", "source_ids": [SOURCE]})
    draft, bodies = _run(["plain prose", good], DOCUMENTARY)
    assert len(bodies) == 2 and draft.model == CONFIG.drafter_model and draft.attempts == 2
    assert draft.cost_usd == pytest.approx(0.002)
    assert bodies[1]["messages"][-2]["content"] == "plain prose"
    assert "rejected" in bodies[1]["messages"][-1]["content"]


def test_two_bad_answers_in_documentary_mode_are_rejected_not_unavailable() -> None:
    with pytest.raises(DraftRejected, match="after repair"):
        _run(["plain prose", "still prose"], DOCUMENTARY)


def test_two_bad_answers_in_clarification_mode_fall_back_to_a_template_question() -> None:
    draft, bodies = _run(["plain prose", "still prose"], CLARIFY, language="fr")
    assert len(bodies) == 2
    assert (draft.model, draft.prompt_version, draft.source_ids) == ("template", "template-v1", ())
    assert draft.attempts == 2
    assert "TX-123456" in draft.text and draft.text.startswith("Bonjour,")
    assert draft.cost_usd == pytest.approx(0.002)


def test_a_reference_copied_from_the_ticket_is_allowed() -> None:
    segments = _segments(("Please check TX-123456.", ()))
    assert check_segments(segments, "clarification", frozenset(), "ticket: TX-123456") == ()


@pytest.mark.parametrize(
    ("raw", "kept"),
    [
        ("Guten Tag,", None),
        ("Estimado cliente,", None),
        ("Gentile cliente,", None),
        ("Bonjour, merci pour votre message.", "merci pour votre message."),
        ("Hello Anna, we are looking into it.", "we are looking into it."),
    ],
)
def test_a_greeting_prefix_is_removed_but_the_content_after_it_is_kept(raw: str, kept: str | None) -> None:
    answer = _answer({"text": raw, "source_ids": []}, {"text": "Which payment?", "source_ids": []})
    texts = [s.text for s in parse_reply(answer)[1]]
    assert texts == ([kept, "Which payment?"] if kept else ["Which payment?"])


@pytest.mark.parametrize("closing", ["Atentamente,", "Distinti saluti", "Mit freundlichen Grüßen", "Keelpay Support"])
def test_a_final_sign_off_segment_is_removed(closing: str) -> None:
    answer = _answer({"text": "Which payment?", "source_ids": []}, {"text": closing, "source_ids": []})
    assert [s.text for s in parse_reply(answer)[1]] == ["Which payment?"]


def test_a_figure_that_is_not_in_the_evidence_is_repaired_by_the_policy_check() -> None:
    bad = _answer({"text": "Your payout of 98765 EUR is late.", "source_ids": [SOURCE]})
    good = _answer({"text": "Send the KYC form.", "source_ids": [SOURCE]})
    draft, bodies = _run([bad, good], DOCUMENTARY)
    assert len(bodies) == 2 and "98765" not in draft.text
    assert "policy check blocks" in bodies[1]["messages"][-1]["content"]


def test_the_ticket_language_is_stated_to_the_model() -> None:
    good = _answer({"text": "Send the KYC form.", "source_ids": [SOURCE]}, language="fr")
    _, bodies = _run([good], DOCUMENTARY, language="fr")
    assert "The ticket language is fr" in bodies[0]["messages"][-1]["content"]
