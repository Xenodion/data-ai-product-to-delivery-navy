"""Routing Node: a pure decision from the Qualifier result to a desk and a priority."""

from typing import Final

from flow.contracts import Priority, QualifierResult, ReasonCode, Route, RoutingDecision
from ml.qualifier.src.dataset_build.schema import OTHER, UNDEFINED
from ml.qualifier.src.scoring import desk_of

DECISION_VERSION: Final = "routing-node-v1"
# The historical scorer says "technical"; the routing contract says "technical_api".
_CONTRACT_DESK: Final[dict[str, Route]] = {
    "payments": "payments",
    "disputes": "disputes",
    "technical": "technical_api",
    "compliance": "compliance",
    "triage": "triage",
}


def decide_route(result: QualifierResult, policy_version: str) -> RoutingDecision:
    """Map a Qualifier result to a desk or the Re-router; urgency never changes the path."""
    label = result.label
    if label is None:
        reason: ReasonCode = "QUALIFIER_UNAVAILABLE" if result.status == "unavailable" else "QUALIFIER_INVALID"
        return RoutingDecision(
            decision_version=DECISION_VERSION,
            policy_version=policy_version,
            desk="triage",
            priority="unknown",
            reason_codes=(reason,),
        )

    reasons: list[ReasonCode] = []
    if label.intent == UNDEFINED:
        reasons.append("INTENT_UNDECIDABLE")
    elif label.intent == OTHER:
        reasons.append("INTENT_UNSUPPORTED")
    else:
        reasons.append("DESK_FROM_SUPPORTED_INTENT")

    priority: Priority
    match label.urgency:
        case "high" | "medium" | "low" as urgency:
            priority = urgency
        case _:
            priority = "unknown"
            reasons.append("PRIORITY_UNKNOWN")
    if priority == "high":
        reasons.append("HIGH_PRIORITY_SURFACE_ONLY")
    if label.sentiment == UNDEFINED:
        reasons.append("SENTIMENT_NEUTRAL_FALLBACK")

    return RoutingDecision(
        decision_version=DECISION_VERSION,
        policy_version=policy_version,
        desk=_CONTRACT_DESK[desk_of(label)],
        priority=priority,
        reason_codes=tuple(reasons),
    )
