"""Known bad Drafter outputs must never reach the Validator as an acceptable draft."""

import json

import pytest

from flow.contracts import EvidenceFact
from flow.draft_render import MAX_SEGMENTS, check_segments, parse_reply
from flow.llm import DraftRejected
from flow.policy import PolicyContext, check_draft

SOURCE = "kb_compliance_documents_v1"
POLICY = PolicyContext(merchant_id="m1", approved_source_ids=(SOURCE,))


def _findings(text: str) -> tuple[str, ...]:
    return check_draft(text, POLICY).findings


@pytest.mark.parametrize(
    "text",
    [
        "We can provide a statement confirming your account's status.",
        "A statement is now available in your dashboard.",
        "Nous pouvons vous fournir une attestation.",
        "Votre relevé sera disponible demain.",
        "We will send you the certificate.",
    ],
)
def test_a_draft_that_says_a_document_exists_or_will_be_delivered_is_blocked(text: str) -> None:
    assert "AVAILABILITY_CLAIM" in _findings(text)


@pytest.mark.parametrize(
    "text",
    [
        "The team will check what can be issued.",
        "Which document do your auditors need, and for which period?",
        "Pouvez-vous nous indiquer le type de document souhaité ?",
    ],
)
def test_a_question_about_a_document_is_not_blocked(text: str) -> None:
    assert "AVAILABILITY_CLAIM" not in _findings(text)


@pytest.mark.parametrize(
    "text",
    ["Pouvez-vous me donner la référence ?", "I will check this.", "J'ai besoin de la date.", "I'll look into it."],
)
def test_a_first_person_singular_reply_is_rejected(text: str) -> None:
    segments = parse_reply(json.dumps({"segments": [{"text": text, "source_ids": []}]}))[1]
    with pytest.raises(DraftRejected, match="first person"):
        check_segments(segments, "clarification", frozenset())


@pytest.mark.parametrize(
    "text", ["Pouvez-vous nous donner la référence ?", "We will look into it.", "That is, i.e. the case."]
)
def test_a_team_voice_reply_is_accepted(text: str) -> None:
    segments = parse_reply(json.dumps({"segments": [{"text": text, "source_ids": []}]}))[1]
    assert check_segments(segments, "clarification", frozenset()) == ()


def test_an_answer_with_too_many_segments_is_rejected() -> None:
    answer = json.dumps({"segments": [{"text": f"Point {n}.", "source_ids": []} for n in range(MAX_SEGMENTS + 1)]})
    with pytest.raises(DraftRejected, match="segments"):
        parse_reply(answer)


def test_the_policy_fact_of_a_clarification_can_be_cited_but_is_not_required() -> None:
    fact = EvidenceFact(field="approved_guidance", value="v", source_id=SOURCE, source_version="1.1")
    cited = parse_reply(json.dumps({"segments": [{"text": "Which document?", "source_ids": [SOURCE]}]}))[1]
    plain = parse_reply(json.dumps({"segments": [{"text": "Which document?", "source_ids": []}]}))[1]
    allowed = frozenset({fact.source_id})
    assert check_segments(cited, "clarification", allowed) == (SOURCE,)
    assert check_segments(plain, "clarification", allowed) == ()
