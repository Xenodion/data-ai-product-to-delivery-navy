"""Typed records exchanged between the flow steps."""

import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict

from research.qualifier.src.dataset_build.schema import TicketLabel

CONFIG_PATH = Path(__file__).parent / "config.toml"
FROZEN = ConfigDict(extra="forbid", frozen=True)

Desk = Literal["payments", "disputes", "technical_api", "compliance"]
Route = Literal["payments", "disputes", "technical_api", "compliance", "triage"]
Priority = Literal["high", "medium", "low", "unknown"]
Status = Literal["awaiting_validation", "awaiting_reroute", "manual_handling"]
ReasonCode = Literal[
    "DESK_FROM_SUPPORTED_INTENT",
    "DRAFTER_UNAVAILABLE",
    "FIRST_REROUTE_RECOMPUTE",
    "HIGH_PRIORITY_SURFACE_ONLY",
    "INTENT_UNDECIDABLE",
    "INTENT_UNSUPPORTED",
    "PRIORITY_UNKNOWN",
    "QUALIFIER_INVALID",
    "QUALIFIER_UNAVAILABLE",
    "SECOND_REROUTE_MANUAL",
    "SENTIMENT_NEUTRAL_FALLBACK",
]


class FlowConfig(BaseModel):
    """Values of ``flow/config.toml``."""

    model_config = FROZEN

    qualifier_url: str
    qualifier_model_version: str
    qualifier_max_tokens: int
    qualifier_timeout_seconds: float
    drafter_url: str
    drafter_model: str
    drafter_prompt_version: str
    drafter_temperature: float
    drafter_max_tokens: int
    drafter_timeout_seconds: float
    policy_version: str
    transient_retries: int
    retry_wait_seconds: float
    merchant_id: str


class Ticket(BaseModel):
    """One incoming ticket. Unknown fields are refused, so expected labels cannot ride along."""

    model_config = FROZEN

    ticket_id: str
    merchant_id: str
    text: str
    created_at: datetime


class QualifierResult(BaseModel):
    """Validated outcome of the Qualifier; only a ``valid`` result carries a label."""

    model_config = FROZEN

    status: Literal["valid", "invalid", "unavailable"]
    label: TicketLabel | None
    raw: str | None
    model_version: str
    latency_seconds: float
    error: str | None = None


class RoutingDecision(BaseModel):
    """Initial decision of the Routing Node."""

    model_config = FROZEN

    decision_version: str
    policy_version: str
    desk: Route
    priority: Priority
    reason_codes: tuple[ReasonCode, ...]


class Draft(BaseModel):
    """One version of a proposed reply. A stale draft belongs to an older desk."""

    model_config = FROZEN

    version: int
    text: str
    desk: Route
    model: str
    prompt_version: str
    cost_usd: float
    latency_seconds: float
    stale: bool = False


class TicketRun(BaseModel):
    """State of a ticket at the first human step."""

    model_config = FROZEN

    ticket: Ticket
    qualifier: QualifierResult
    decision: RoutingDecision  # the initial decision, kept unchanged after corrections
    desk: Route
    status: Status
    drafts: tuple[Draft, ...]
    reroute_count: int = 0
    reason_codes: tuple[ReasonCode, ...]
    draft_error: str | None = None


class DraftWriter(Protocol):
    """Writes one draft version; raises ``LLMError`` when none can be produced."""

    def __call__(self, ticket: Ticket, qualifier: QualifierResult, desk: Route, version: int) -> Draft: ...


@dataclass(frozen=True)
class FlowDeps:
    """External steps of the flow, passed in so that tests can replace them."""

    qualify: Callable[[Ticket], QualifierResult]
    draft: DraftWriter
    policy_version: str


def load_config(path: Path = CONFIG_PATH) -> FlowConfig:
    with path.open("rb") as handle:
        return FlowConfig.model_validate(tomllib.load(handle))
