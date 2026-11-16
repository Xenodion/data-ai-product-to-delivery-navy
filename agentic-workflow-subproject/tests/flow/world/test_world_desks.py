import pytest

from flow.world.desks import OUTCOME_DESKS, outcome_desk
from ml.qualifier.src.dataset_build.schema import TicketLabel


def _label(intent: str, sub_intent: str) -> TicketLabel:
    return TicketLabel(
        intent=intent,
        sub_intent=sub_intent,
        transaction_id="",
        amount="",
        currency="",
        urgency="medium",
        sentiment="neutral",
    )


@pytest.mark.parametrize(
    ("intent", "sub_intent", "expected"),
    [
        ("payment_status", "status_inquiry", "payments"),
        ("dispute", "chargeback", "disputes"),
        ("technical_api", "api_error", "technical_api"),
        ("compliance", "kyc_update", "compliance"),
        ("OTHER", "OTHER", "triage"),
        ("UNDEFINED", "UNDEFINED", "triage"),
    ],
)
def test_outcome_desk_maps_every_intent_to_a_stored_desk(
    intent: str, sub_intent: str, expected: str
) -> None:
    desk = outcome_desk(_label(intent, sub_intent))
    assert desk == expected
    assert desk in OUTCOME_DESKS
