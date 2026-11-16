"""Human-only topics get no draft; account-state claims are blocked; a human edit drops model sources."""

from datetime import UTC, datetime

import pytest

from flow.context import plan_context
from flow.contracts import Draft, FlowDeps, QualifierResult, Ticket, load_config
from flow.evidence import decide_evidence
from flow.human_actions import edit_draft
from flow.pipeline import process
from flow.policy import PolicyContext, check_draft
from flow.tools import gather_evidence  # noqa: F401  (import check: the tools still load)
from ml.qualifier.src.dataset_build.schema import TicketLabel

TICKET = Ticket(ticket_id="t1", merchant_id="m1", text="my account", created_at=datetime(2026, 11, 5, tzinfo=UTC))


def _label(sub_intent: str, intent: str = "compliance") -> TicketLabel:
    return TicketLabel(
        intent=intent, sub_intent=sub_intent, transaction_id="", amount="", currency="",
        urgency="high", sentiment="negative",
    )


def _qualifier(sub_intent: str) -> QualifierResult:
    return QualifierResult(
        status="valid", label=_label(sub_intent), raw="{}", model_version="m", latency_seconds=0
    )


def test_account_hold_is_planned_as_human_only_without_any_lookup() -> None:
    plan = plan_context("compliance", _label("account_hold"), "m1", None, load_config())
    assert plan.status == "human_only" and not plan.knowledge_required and not plan.ledger_required
    decision = decide_evidence(plan, None)  # type: ignore[arg-type]  # the gate stops before the results
    assert decision.mode == "no_draft" and decision.reason_codes == ("HUMAN_ONLY_TOPIC",)


def test_other_compliance_sub_intents_are_still_planned() -> None:
    assert plan_context("compliance", _label("kyc_update"), "m1", None, load_config()).status == "planned"


def test_the_flow_writes_no_draft_for_account_hold_and_tells_the_validator_why() -> None:
    def never(*_: object) -> Draft:
        raise AssertionError("no draft may be requested for a human-only topic")

    deps = FlowDeps(
        qualify=lambda _: _qualifier("account_hold"), draft=never, policy_version="p1",
        flow_config=load_config(),
    )
    run = process(TICKET, deps)
    assert run.drafts == () and "HUMAN_ONLY_TOPIC" in run.reason_codes


@pytest.mark.parametrize(
    "sentence",
    [
        "Our records show your account is currently restricted.",
        "Your account has been suspended.",
        "Your funds are on hold.",
        "Votre compte est actuellement bloque.".replace("bloque", "bloqué"),
        "Vos fonds sont gelés.",
    ],
)
def test_a_claim_about_the_state_of_the_account_is_blocked(sentence: str) -> None:
    assert "ACCOUNT_STATE_CLAIM" in check_draft(sentence, PolicyContext(merchant_id="m1")).findings


@pytest.mark.parametrize(
    "sentence",
    ["Could you tell us which account you mean?", "Please check your account settings.", "Is your account restricted?"],
)
def test_neutral_sentences_about_an_account_are_not_blocked(sentence: str) -> None:
    assert "ACCOUNT_STATE_CLAIM" not in check_draft(sentence, PolicyContext(merchant_id="m1")).findings


def test_a_human_edit_drops_the_sources_of_the_model_text() -> None:
    draft = Draft(
        version=1, text="A [kb_x].", desk="compliance", model="m", prompt_version="p", cost_usd=0,
        latency_seconds=0, source_ids=("kb_x",), source_versions=(("kb_x", "1"),),
    )
    deps = FlowDeps(
        qualify=lambda _: _qualifier("kyc_update"), draft=lambda *a: draft, policy_version="p1",
        flow_config=load_config(),
    )
    run = process(TICKET, deps)
    assert run.status == "awaiting_validation"
    edited = edit_draft(run, "Hello", actor="agent").drafts[-1]
    assert edited.source_ids == () and edited.source_versions == () and edited.model == "human-edit"


@pytest.mark.parametrize(
    "text",
    [
        "Please treat this as a firm complaint.",
        "Sonst wende ich mich an die Aufsichtsbehörde.",
        "Nous avons une échéance réglementaire demain.",
        "My lawyer will contact you.",
        "Vos fonds sont gelés depuis lundi.",
    ],
)
def test_a_ticket_with_a_human_only_keyword_gets_no_plan_and_no_draft(text: str) -> None:
    label = _label("status_inquiry", "payment_status")
    plan = plan_context("payments", label, "m1", None, load_config(), text)
    assert plan.status == "human_only" and plan.reason_codes == ("HUMAN_ONLY_TOPIC",)


def test_an_ordinary_ticket_is_not_caught_by_the_keywords() -> None:
    label = _label("status_inquiry", "payment_status")
    text = "Where is my payment of 125.50 EUR? It was sent on Monday."
    assert plan_context("payments", label, "m1", None, load_config(), text).status != "human_only"
