"""Typed records exchanged between the flow steps."""

import os
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, Protocol

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

from ml.qualifier.src.dataset_build.schema import TicketLabel

CONFIG_PATH = Path(__file__).parent / "config.toml"
WORLD_DATABASE_ENV = "NAVY_WORLD_DB"
QUALIFIER_URL_ENV = "NAVY_QUALIFIER_URL"
COPILOT_MODE_ENV = "NAVY_COPILOT_MODE"
QUALIFIER_PROVIDER_ENV = "NAVY_QUALIFIER_PROVIDER"
QUALIFIER_VERTEX_ENDPOINT_ENV = "NAVY_QUALIFIER_VERTEX_ENDPOINT_ID"
QUALIFIER_VERTEX_PROJECT_ENV = "NAVY_QUALIFIER_VERTEX_PROJECT_ID"
QUALIFIER_VERTEX_REGION_ENV = "NAVY_QUALIFIER_VERTEX_REGION"
FROZEN = ConfigDict(extra="forbid", frozen=True)

Desk = Literal["payments", "disputes", "technical_api", "compliance"]
Route = Literal["payments", "disputes", "technical_api", "compliance", "triage"]
CopilotMode = Literal[
    "full", "judge_off", "l1_drafting_off", "l2_routing_off", "l3_copilot_off",
]
Priority = Literal["high", "medium", "low", "unknown"]
Status = Literal[
    "awaiting_validation", "awaiting_reroute", "manual_handling",
    "ready_to_send", "sent_open", "sent_closed", "closed_manual",
]
SendDisposition = Literal["leave_open", "close"]
ContextStatus = Literal["planned", "clarification", "no_tools", "human_only"]
ToolStatus = Literal[
    "not_run", "not_required", "exact_id", "candidate_selection", "not_found",
    "conflict", "wrong_merchant", "unavailable", "found", "empty", "blocked",
]
PreparationMode = Literal["factual", "documentary", "clarification", "no_draft"]
PolicyStatus = Literal["pass", "blocked"]
PolicyFindingCode = Literal[
    "PRICE_COMMITMENT",
    "REFUND_PROMISE",
    "LEGAL_ADVICE",
    "UNSUPPORTED_FIGURE",
    "FOREIGN_MERCHANT_IDENTIFIER",
    "SOURCE_STATUS_CONFLICT",
    "ACCOUNT_STATE_CLAIM",
    "AVAILABILITY_CLAIM",
    "POLICY_CHECK_ERROR",
]
ReasonCode = Literal[
    "COPILOT_OFF",
    "DESK_FROM_SUPPORTED_INTENT",
    "DRAFTING_OFF",
    "DRAFTER_UNAVAILABLE",
    "DRAFT_REJECTED",
    "HUMAN_ONLY_TOPIC",
    "EVIDENCE_BLOCKED",
    "EVIDENCE_READY",
    "CONTENT_POLICY_BLOCK",
    "POLICY_CHECK_ERROR",
    "FIRST_REROUTE_RECOMPUTE",
    "HIGH_PRIORITY_SURFACE_ONLY",
    "LATER_TURN_DESK_KEPT",
    "LOOKUP_UNAVAILABLE",
    "INTENT_UNDECIDABLE",
    "INTENT_UNSUPPORTED",
    "PAYMENT_CANDIDATES_REQUIRE_SELECTION",
    "PAYMENT_ID_ABSENT",
    "PAYMENT_ID_UNVERIFIED",
    "PAYMENT_NOT_FOUND",
    "PAYMENT_WRONG_MERCHANT",
    "PRIORITY_UNKNOWN",
    "QUALIFIER_INVALID",
    "QUALIFIER_UNAVAILABLE",
    "RETRIEVAL_UNAVAILABLE",
    "ROUTING_OFF",
    "SECOND_REROUTE_MANUAL",
    "SENTIMENT_NEUTRAL_FALLBACK",
    "SOURCE_MISSING",
    "LOOKUP_RESULT_MISMATCH",
    "TURN_LIMIT_REACHED",
]


class FlowConfig(BaseModel):
    """Values of ``flow/config.toml``."""

    model_config = FROZEN

    qualifier_model_uri: str
    qualifier_model_md5: str
    qualifier_url: str
    qualifier_provider: Literal["openai_compatible", "vertex_raw_predict"] = "openai_compatible"
    qualifier_vertex_endpoint_id: str = ""
    qualifier_vertex_project_id: str = ""
    qualifier_vertex_region: str = "europe-west2"
    qualifier_model_version: str
    qualifier_max_tokens: int
    qualifier_timeout_seconds: float
    qualifier_temperature: float
    qualifier_prompt_name: str
    qualifier_prompt_label: str
    routing_version: str
    drafter_url: str
    drafter_model: str
    drafter_prompt_name: str
    drafter_prompt_label: str
    drafter_temperature: float
    drafter_max_tokens: int
    drafter_timeout_seconds: float
    drafter_response_format: str = "json_object"  # "json_object" or "none"
    drafter_require_parameters: bool = True  # OpenRouter must not silently drop response_format
    drafter_greeting: dict[str, str] = {}
    drafter_closing: dict[str, str] = {}
    drafter_fallback_question: dict[str, dict[str, str]] = {}
    policy_version: str
    transient_retries: int
    retry_wait_seconds: float
    merchant_id: str
    max_automated_turns: int
    max_reroutes: int
    copilot_mode: CopilotMode = "full"
    ledger_enabled: bool
    knowledge_enabled: bool
    tool_timeout_seconds: float
    max_knowledge_results: int
    knowledge_min_overlap_tokens: int
    ledger_fixture_path: str
    knowledge_fixture_path: str
    metrics_enabled: bool
    metrics_db_path: str
    payment_fact_sub_intents: tuple[str, ...]
    dispute_fact_sub_intents: tuple[str, ...]
    human_only_sub_intents: tuple[str, ...] = ()
    human_only_keywords: tuple[str, ...] = ()
    api_db_path: str
    api_checkpoint_db_path: str
    api_max_page_size: int
    api_worker_count: int
    api_cors_origins: tuple[str, ...]
    # Optional merchant world database (read-only); a relative path is read from the project
    # root. When unset, the fixture files above stay the only source.
    world_database_path: str | None = None
    # Final-run switch: list the held-back `current` tickets in the merchant history.
    world_show_current: bool = False

    @field_validator("max_automated_turns", "max_reroutes", "max_knowledge_results", "knowledge_min_overlap_tokens")
    @classmethod
    def _positive_limits(cls, value: int) -> int:
        if value < 1:
            raise ValueError("flow limits must be positive")
        return value

    @field_validator("tool_timeout_seconds")
    @classmethod
    def _positive_tool_timeout(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("tool_timeout_seconds must be positive")
        return value

    @field_validator("api_max_page_size", "api_worker_count")
    @classmethod
    def _positive_api_limits(cls, value: int) -> int:
        if value < 1:
            raise ValueError("API limits must be positive")
        return value


class AttachmentMetadata(BaseModel):
    """V1 stores attachment descriptors only; file contents are not ingested."""

    model_config = FROZEN

    name: str
    media_type: str | None = None
    size_bytes: int | None = None

    @field_validator("size_bytes")
    @classmethod
    def _non_negative_size(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("size_bytes must be non-negative")
        return value


class Ticket(BaseModel):
    """One conversation turn. The external envelope calls ``text`` ``body``."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    ticket_id: str
    merchant_id: str
    body: str = Field(validation_alias=AliasChoices("body", "text"))
    created_at: datetime
    turn: int = 1
    channel: Literal[
        "formal_email", "short_email", "forwarded_thread", "chat_message"
    ] = "formal_email"
    subject: str | None = None
    language: str | None = None
    attachments: tuple[AttachmentMetadata, ...] = ()

    @field_validator("turn")
    @classmethod
    def _positive_turn(cls, value: int) -> int:
        if value < 1:
            raise ValueError("turn must be a positive integer")
        return value

    @property
    def message_text(self) -> str:
        """Rebuild the optional subject in the stable Qualifier input format."""
        return f"Subject: {self.subject}\n\n{self.body}" if self.subject else self.body

    @property
    def text(self) -> str:
        """Compatibility accessor for the earlier flow contract."""
        return self.body


class FieldEvidence(BaseModel):
    model_config = FROZEN

    status: Literal["absent", "verified", "unverified"]
    value: str


class FieldCheckResult(BaseModel):
    """Non-blocking evidence annotations for extracted merchant references."""

    model_config = FROZEN

    transaction_id: FieldEvidence
    amount: FieldEvidence
    currency: FieldEvidence


class ContextPlan(BaseModel):
    """Allowlisted read operations selected by the deterministic Context Plan."""

    model_config = FROZEN

    desk: Desk
    merchant_id: str
    sub_intent: str
    ledger_required: bool
    knowledge_required: bool
    transaction_id: str | None = None
    status: ContextStatus
    reason_codes: tuple[str, ...] = ()


class EvidenceFact(BaseModel):
    """One permitted factual value with a stable source and version reference."""

    model_config = FROZEN

    field: str
    value: str
    source_id: str
    source_version: str


class LedgerToolResult(BaseModel):
    """Result returned by the SQL ledger tool only."""

    model_config = FROZEN

    status: ToolStatus = "not_run"
    merchant_id: str | None = None
    source_ids: tuple[str, ...] = ()
    facts: tuple[EvidenceFact, ...] = ()
    allowed_figures: tuple[str, ...] = ()
    foreign_identifiers: tuple[str, ...] = ()
    verified_transaction_id: str | None = None


class RetrievalToolResult(BaseModel):
    """Legacy-named result contract for deterministic approved-document Text Search."""

    model_config = FROZEN

    status: ToolStatus = "not_run"
    source_ids: tuple[str, ...] = ()
    facts: tuple[EvidenceFact, ...] = ()


class EvidenceResult(BaseModel):
    """Join point for independent SQL and Text Search tools; provenance stays separate."""

    model_config = FROZEN

    ledger: LedgerToolResult = LedgerToolResult()
    retrieval: RetrievalToolResult = RetrievalToolResult()


class EvidenceDecision(BaseModel):
    model_config = FROZEN

    mode: PreparationMode
    reason_codes: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    facts: tuple[EvidenceFact, ...] = ()
    allowed_figures: tuple[str, ...] = ()


class QualifierResult(BaseModel):
    """Validated outcome of the Qualifier; only a ``valid`` result carries a label."""

    model_config = FROZEN

    status: Literal["valid", "invalid", "unavailable"]
    label: TicketLabel | None
    raw: str | None
    model_version: str
    prompt_name: str = ""
    prompt_version: str = "local-fallback"
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
    prompt_name: str = ""
    prompt_version: str
    cost_usd: float
    latency_seconds: float
    evidence_mode: PreparationMode = "clarification"
    source_ids: tuple[str, ...] = ()
    source_versions: tuple[tuple[str, str], ...] = ()
    stale: bool = False
    blocked: bool = False
    attempts: int = 1  # model calls this draft needed; 2 means the first answer was repaired


class PolicyCheckResult(BaseModel):
    model_config = FROZEN

    status: PolicyStatus
    findings: tuple[PolicyFindingCode, ...] = ()
    content_sha256: str = ""
    hard_block: bool = False
    overridden: bool = False
    override_reason: str | None = None


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
    field_check: FieldCheckResult | None = None
    context_plan: ContextPlan | None = None
    evidence_decision: EvidenceDecision | None = None
    policy_check: PolicyCheckResult | None = None
    foreign_identifiers: tuple[str, ...] = ()
    final_text: str | None = None
    final_author: Literal["model", "human"] | None = None
    approved_by: str | None = None
    human_actions: tuple["HumanActionEvent", ...] = ()
    send_key: str | None = None
    send_disposition: SendDisposition | None = None
    final_policy_check: PolicyCheckResult | None = None
    send_receipt: "SimulatedSendReceipt | None" = None
    send_receipts: tuple["SimulatedSendReceipt", ...] = ()

    @model_validator(mode="before")
    @classmethod
    def _upgrade_legacy_sent_status(cls, value: object) -> object:
        """Read old local checkpoints as sent-open; old sends never closed tickets."""
        if not isinstance(value, dict) or value.get("status") != "sent_simulated":
            return value
        upgraded = dict(value)
        upgraded["status"] = "sent_open"
        upgraded.setdefault("send_disposition", "leave_open")
        receipt = upgraded.get("send_receipt")
        if isinstance(receipt, dict):
            upgraded["send_receipt"] = {**receipt, "disposition": "leave_open"}
        receipts = upgraded.get("send_receipts", ())
        upgraded["send_receipts"] = tuple(
            {**item, "disposition": item.get("disposition", "leave_open")}
            if isinstance(item, dict) else item
            for item in receipts
        )
        return upgraded


class HumanActionEvent(BaseModel):
    """Append-only action metadata; reply content is kept in versioned ticket state."""

    model_config = FROZEN

    action: Literal["edit", "write", "approve", "handoff", "reroute", "close", "send", "send_blocked"]
    actor: str
    reason: str | None = None
    text_sha256: str | None = None
    send_disposition: SendDisposition | None = None
    created_at: datetime


class SimulatedSendReceipt(BaseModel):
    """Proof of one simulated send; it never represents an external delivery."""

    model_config = FROZEN

    send_key: str
    ticket_id: str
    text_sha256: str
    policy_version: str
    disposition: SendDisposition = "leave_open"
    created_at: datetime


TicketRun.model_rebuild()


class DraftWriter(Protocol):
    """Writes one draft version; raises ``LLMError`` when none can be produced."""

    def __call__(self, ticket: Ticket, qualifier: QualifierResult, desk: Route, version: int) -> Draft: ...


class GroundedDraftWriter(Protocol):
    """Writes from a finalized Evidence Gate decision, never from raw tool output."""

    def __call__(
        self,
        ticket: Ticket,
        qualifier: QualifierResult,
        desk: Route,
        version: int,
        *,
        evidence: EvidenceDecision,
    ) -> Draft: ...


@dataclass(frozen=True)
class FlowDeps:
    """External steps of the flow, passed in so that tests can replace them."""

    qualify: Callable[[Ticket], QualifierResult]
    draft: DraftWriter
    policy_version: str
    grounded_draft: GroundedDraftWriter | None = None
    gather_evidence: Callable[..., EvidenceResult] | None = None
    flow_config: FlowConfig | None = None


class PipelineWork(BaseModel):
    """Checkpointable intermediate state between deterministic flow nodes."""

    model_config = FROZEN

    ticket: Ticket
    previous_run: TicketRun | None = None
    early_run: TicketRun | None = None
    qualifier: QualifierResult | None = None
    field_check: FieldCheckResult | None = None
    decision: RoutingDecision | None = None
    context_plan: ContextPlan | None = None
    tool_results: EvidenceResult | None = None
    evidence_decision: EvidenceDecision | None = None
    draft: Draft | None = None
    draft_error: str | None = None
    policy_check: PolicyCheckResult | None = None


def load_config(path: Path = CONFIG_PATH) -> FlowConfig:
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    api = raw.pop("api", {})
    raw.update(
        api_db_path=api.get("db_path", ""),
        api_checkpoint_db_path=api.get("checkpoint_db_path", ""),
        api_max_page_size=api.get("max_page_size", 0),
        api_worker_count=api.get("worker_count", 0),
        api_cors_origins=tuple(api.get("cors_origins", ())),
    )
    copilot_mode = os.environ.get(COPILOT_MODE_ENV)
    if copilot_mode:  # override the copilot level without editing the committed config (#60)
        raw["copilot_mode"] = copilot_mode
    world = os.environ.get(WORLD_DATABASE_ENV)
    if world:  # run the flow on a world database without editing the committed config
        raw["world_database_path"] = world
    qualifier = os.environ.get(QUALIFIER_URL_ENV)
    if qualifier:  # containers reach the Qualifier by service name, not by 127.0.0.1
        raw["qualifier_url"] = qualifier
    raw["qualifier_provider"] = os.environ.get(
        QUALIFIER_PROVIDER_ENV, raw.get("qualifier_provider", "openai_compatible")
    )
    raw["qualifier_vertex_endpoint_id"] = os.environ.get(
        QUALIFIER_VERTEX_ENDPOINT_ENV, raw.get("qualifier_vertex_endpoint_id", "")
    )
    raw["qualifier_vertex_project_id"] = os.environ.get(
        QUALIFIER_VERTEX_PROJECT_ENV,
        os.environ.get("GCP_PROJECT_ID", raw.get("qualifier_vertex_project_id", "")),
    )
    raw["qualifier_vertex_region"] = os.environ.get(
        QUALIFIER_VERTEX_REGION_ENV,
        os.environ.get("GCP_REGION", raw.get("qualifier_vertex_region", "europe-west2")),
    )
    return FlowConfig.model_validate(raw)
