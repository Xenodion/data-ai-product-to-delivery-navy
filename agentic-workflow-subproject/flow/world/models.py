"""Typed rows of the merchant world, mirroring ``schema.sql`` column for column."""

from datetime import date
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

Sector = Literal["retail", "saas", "marketplace", "education", "logistics", "hospitality", "travel"]
VolumeTier = Literal["small", "medium", "large"]
KycStatus = Literal["verified", "pending", "under_review"]
RiskLevel = Literal["low", "medium", "high"]
Persona = Literal[
    "small_shop_owner",
    "accountant",
    "developer",
    "operations_manager",
    "founder",
    "compliance_officer",
]
TransactionStatus = Literal[
    "settled", "processing", "under_review", "failed", "refunded", "disputed"
]
RefundStatus = Literal["pending", "completed", "failed"]
DisputeStatus = Literal["open", "under_review", "won", "lost"]
PayoutStatus = Literal["scheduled", "paid", "held", "failed"]
Channel = Literal["formal_email", "short_email", "forwarded_thread", "chat_message"]
TicketRole = Literal["current", "history", "dev"]
ThreadState = Literal["open_awaiting_agent", "open_awaiting_merchant", "closed"]
Desk = Literal["payments", "disputes", "technical_api", "compliance"]
OutcomeDesk = Literal["payments", "disputes", "technical_api", "compliance", "triage"]
Direction = Literal["inbound", "outbound"]
AuthorKind = Literal["merchant", "agent"]
PolicyStatus = Literal["approved", "draft", "retired"]

LanguageCode = Annotated[str, Field(min_length=2, max_length=2)]
CountryCode = Annotated[str, Field(min_length=2, max_length=2)]
CurrencyCode = Annotated[str, Field(pattern=r"^[A-Z]{3}$")]


class _Row(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Merchant(_Row):
    merchant_id: str
    name: str
    sector: Sector
    preferred_language: LanguageCode
    country: CountryCode
    settlement_currency: CurrencyCode
    volume_tier: VolumeTier
    plan: str
    fee_bps: int = Field(ge=0)
    kyc_status: KycStatus
    risk_level: RiskLevel
    onboarded_at: date


class MerchantCurrency(_Row):
    merchant_id: str
    currency: CurrencyCode


class Contact(_Row):
    contact_id: str
    merchant_id: str
    persona: Persona
    language: LanguageCode


class Transaction(_Row):
    transaction_id: str
    merchant_id: str
    amount_minor: int = Field(gt=0)
    currency: CurrencyCode
    status: TransactionStatus
    payment_method: str
    created_at: AwareDatetime
    settled_at: AwareDatetime | None = None


class Refund(_Row):
    refund_id: str
    transaction_id: str
    amount_minor: int = Field(gt=0)
    status: RefundStatus
    created_at: AwareDatetime


class Dispute(_Row):
    dispute_id: str
    transaction_id: str
    status: DisputeStatus
    reason: str
    opened_at: AwareDatetime
    due_at: AwareDatetime


class Payout(_Row):
    payout_id: str
    merchant_id: str
    amount_minor: int = Field(gt=0)
    currency: CurrencyCode
    status: PayoutStatus
    scheduled_at: AwareDatetime
    paid_at: AwareDatetime | None = None
    held_reason: str | None = None


class Ticket(_Row):
    ticket_id: str
    merchant_id: str
    contact_id: str
    opened_at: AwareDatetime
    channel: Channel
    language: LanguageCode
    role: TicketRole
    thread_state: ThreadState


class TicketOutcome(_Row):
    ticket_id: str
    desk: OutcomeDesk
    resolution: str
    closed_at: AwareDatetime


class Message(_Row):
    message_id: str
    ticket_id: str
    turn_index: int = Field(ge=1)
    direction: Direction
    sent_at: AwareDatetime
    body: str
    author_kind: AuthorKind


class Policy(_Row):
    source_id: str
    version: str
    desk: Desk
    language: LanguageCode
    status: PolicyStatus
    valid_from: date
    valid_until: date | None = None
    owner: str
    title: str
    text: str


class PolicySubIntent(_Row):
    source_id: str
    version: str
    sub_intent: str


TABLE_MODELS: dict[str, type[_Row]] = {
    "merchants": Merchant,
    "merchant_currencies": MerchantCurrency,
    "contacts": Contact,
    "transactions": Transaction,
    "refunds": Refund,
    "disputes": Dispute,
    "payouts": Payout,
    "tickets": Ticket,
    "ticket_outcomes": TicketOutcome,
    "messages": Message,
    "policies": Policy,
    "policy_sub_intents": PolicySubIntent,
}
