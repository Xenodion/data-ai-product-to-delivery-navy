"""Shared deterministic quality/compliance rules for nodes 10 and 14."""

import hashlib
import re
from decimal import Decimal, InvalidOperation
from typing import Literal

from pydantic import BaseModel, ConfigDict

from flow.contracts import Draft, EvidenceFact, PolicyCheckResult, PolicyFindingCode

Author = Literal["model", "human"]


class PolicyContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    merchant_id: str
    allowed_figures: tuple[str, ...] = ()
    approved_source_ids: tuple[str, ...] = ()
    foreign_identifiers: tuple[str, ...] = ()
    evidence_facts: tuple[EvidenceFact, ...] = ()


_PRICE_COMMITMENT = re.compile(
    r"\b(?:our\s+)?(?:price|pricing|tariff|cost|charge|fee)\s+(?:is|will\s+be|costs|of)\s*"
    r"(?:[€$£]\s*)?\d|\b(?:prix|tarif)\s+(?:est|sera|de)\s*(?:\d|[€$])|"
    r"\b(?:frais)\s+(?:est|sont|sera|de)\s*(?:\d|[€$])|"
    r"\b(?:co[uû]te|facturera)\s+(?:\d|[€$])",
    re.IGNORECASE,
)
_REFUND_PROMISE = re.compile(
    r"\b(?:we\s+will\s+refund|we(?:'ll|\s+shall)\s+refund|refund\s+is\s+guaranteed|"
    r"we\s+guarantee\s+(?:a\s+)?refund|we\s+will\s+reimburse|"
    r"nous\s+vous\s+rembourserons|nous\s+allons\s+vous\s+rembourser|"
    r"remboursement\s+garanti|nous\s+garantissons\s+le\s+remboursement)\b",
    re.IGNORECASE,
)
_LEGAL_ADVICE = re.compile(
    r"\b(?:you\s+are\s+legally\s+entitled|you\s+should\s+sue|"
    r"you\s+have\s+the\s+legal\s+right|legal\s+advice\s+is|"
    r"vous\s+avez\s+le\s+droit\s+juridique|vous\s+devriez\s+porter\s+plainte|"
    r"conform[eé]ment\s+[àa]\s+la\s+loi,?\s+vous\s+avez\s+droit)\b",
    re.IGNORECASE,
)
_ACCOUNT_STATE = re.compile(
    r"\b(?:your|the)\s+account\s+(?:is|has\s+been|was|remains|will\s+be)\s+(?:currently\s+)?"
    r"(?:restricted|suspended|frozen|blocked|closed|on\s+hold|under\s+review)\b|"
    r"\b(?:your|the)\s+(?:funds|payouts?)\s+(?:are|is|have\s+been)\s+(?:currently\s+)?"
    r"(?:frozen|blocked|on\s+hold|withheld)\b|"
    r"\b(?:votre|le)\s+compte\s+(?:est|a\s+[ée]t[ée]|reste|sera)\s+(?:actuellement\s+)?"
    r"(?:restreint|suspendu|gel[ée]|bloqu[ée]|cl[ôo]tur[ée]|en\s+cours\s+d.examen)\b|"
    r"\b(?:vos|les)\s+(?:fonds|virements)\s+(?:sont|ont\s+[ée]t[ée])\s+(?:actuellement\s+)?"
    r"(?:gel[ée]s|bloqu[ée]s|retenus)\b",
    re.IGNORECASE,
)
# A draft may ask for a document or a result; it must not say that one exists or will be delivered.
_AVAILABILITY_CLAIM = re.compile(
    r"\bwe\s+(?:can|will|shall|are\s+able\s+to)\s+(?:provide|issue|send|supply|deliver|share)\b|"
    r"\b(?:is|are|will\s+be)\s+(?:now\s+)?available\b|\bhas\s+been\s+(?:issued|sent)\b|"
    r"\bnous\s+(?:pouvons|allons|pourrons)\s+(?:vous\s+)?(?:fournir|[ée]mettre|envoyer|transmettre)\b|"
    r"\bnous\s+vous\s+(?:fournirons|enverrons|transmettrons)\b|\b(?:est|sera)\s+disponible\b",
    re.IGNORECASE,
)
_FIGURE = re.compile(
    r"(?<![\w])(?:\d{1,3}(?:[ ,.\u00a0]\d{3})+|\d+)(?:[,.]\d{1,2})?(?:\s?[kK])?(?![\w])"
)
# The T and Z of an ISO stamp glue digits to letters; without this the day and hour are lost.
_ISO_STAMP_SEPARATOR = re.compile(r"(?<=\d)T(?=\d)|(?<=\d)Z\b")
_TRANSACTION_TOKEN = re.compile(r"\bTX[- ]?\d{6}\b", re.IGNORECASE)
_MERCHANT_TOKEN = re.compile(r"\bM-\d+\b", re.IGNORECASE)
_MERCHANT_ID = re.compile(r"^M-\d+$", re.IGNORECASE)

_STATUS_CLAIMS = {
    "settled": re.compile(r"\b(?:settled|completed|paid|credited|réglé|terminé|crédité|versé)\b", re.I),
    "processing": re.compile(r"\b(?:processing|pending|in progress|en cours|en traitement)\b", re.I),
    "refunded": re.compile(r"\b(?:refunded|reimbursed|remboursé|remboursée)\b", re.I),
    "failed": re.compile(r"\b(?:failed|declined|échec|échoué|refusé|refusée)\b", re.I),
}

_STATUS_VALUES = {
    "settled": "settled",
    "completed": "settled",
    "paid": "settled",
    "credited": "settled",
    "processing": "processing",
    "pending": "processing",
    "refunded": "refunded",
    "failed": "failed",
    "declined": "failed",
}


def _source_status_conflict(text: str, facts: tuple[EvidenceFact, ...]) -> bool:
    source_statuses = {
        _STATUS_VALUES[fact.value.casefold()]
        for fact in facts
        if fact.field == "transaction_status" and fact.value.casefold() in _STATUS_VALUES
    }
    if len(source_statuses) != 1:
        return False
    source_status = next(iter(source_statuses))
    claims = {status for status, pattern in _STATUS_CLAIMS.items() if pattern.search(text)}
    # Negated status statements (for example, “not yet settled”) do not assert
    # the status. This conservative phrase filter only catches direct claims.
    for match in re.finditer(r"\b(?:not|never|pas encore|pas|non)\b.{0,24}\b(settled|completed|paid|credited|processing|pending|refunded|failed|declined)\b", text, re.I):
        word = match.group(1).casefold()
        claims.discard(_STATUS_VALUES.get(word, ""))
    return bool(claims - {source_status})


def _number(value: str) -> Decimal | None:
    compact = value.lower().replace("\u00a0", "").replace(" ", "")
    multiplier = Decimal("1000") if compact.endswith("k") else Decimal("1")
    if compact.endswith("k"):
        compact = compact[:-1]
    if "," in compact and "." in compact:
        decimal_mark = "," if compact.rfind(",") > compact.rfind(".") else "."
        thousands_mark = "." if decimal_mark == "," else ","
        compact = compact.replace(thousands_mark, "").replace(decimal_mark, ".")
    elif "," in compact or "." in compact:
        mark = "," if "," in compact else "."
        if len(compact.rsplit(mark, 1)[1]) == 3:
            compact = compact.replace(mark, "")
        else:
            compact = compact.replace(mark, ".")
    try:
        return Decimal(compact) * multiplier
    except InvalidOperation:
        return None


def _figures(text: str, source_ids: tuple[str, ...]) -> set[Decimal]:
    text = _ISO_STAMP_SEPARATOR.sub(" ", text)
    cleaned = _TRANSACTION_TOKEN.sub(" ", text)
    cleaned = _MERCHANT_TOKEN.sub(" ", cleaned)
    for source_id in source_ids:
        cleaned = cleaned.replace(source_id, " ")
    return {number for match in _FIGURE.findall(cleaned) if (number := _number(match)) is not None}


def _foreign_merchant_ids(text: str, merchant_id: str, forbidden: tuple[str, ...]) -> bool:
    current = merchant_id.upper()
    found = {value.upper() for value in _MERCHANT_TOKEN.findall(text)}
    known_foreign_match = any(
        re.search(
            rf"(?<![A-Za-z0-9]){re.escape(value)}(?![A-Za-z0-9])",
            text,
            re.IGNORECASE,
        )
        for value in forbidden
    )
    return known_foreign_match or any(
        _MERCHANT_ID.fullmatch(value) and value != current for value in found
    )


def _evaluate(
    text: str,
    context: PolicyContext,
    *,
    author: Author,
    stage: Literal["draft", "final"],
    override_reason: str | None = None,
) -> PolicyCheckResult:
    findings: list[PolicyFindingCode] = []
    hard_block = _foreign_merchant_ids(text, context.merchant_id, context.foreign_identifiers)
    status_conflict = _source_status_conflict(text, context.evidence_facts)
    if hard_block:
        findings.append("FOREIGN_MERCHANT_IDENTIFIER")
    if status_conflict:
        findings.append("SOURCE_STATUS_CONFLICT")
    if _PRICE_COMMITMENT.search(text):
        findings.append("PRICE_COMMITMENT")
    if _REFUND_PROMISE.search(text):
        findings.append("REFUND_PROMISE")
    if _LEGAL_ADVICE.search(text):
        findings.append("LEGAL_ADVICE")
    if _ACCOUNT_STATE.search(text):
        findings.append("ACCOUNT_STATE_CLAIM")
    if _AVAILABILITY_CLAIM.search(text):
        findings.append("AVAILABILITY_CLAIM")

    # Human-authored final text is not subject to a numeric evidence match, but
    # the other shared rules still run and require an explicit logged override.
    if author == "model" or stage == "draft":
        permitted = _figures(" ".join(context.allowed_figures), ())
        cited_numbers = _figures(text, context.approved_source_ids)
        if cited_numbers - permitted:
            findings.append("UNSUPPORTED_FIGURE")

    findings_tuple = tuple(dict.fromkeys(findings))
    can_override = author == "human" and stage == "final" and bool(override_reason and override_reason.strip())
    overridden = bool(findings_tuple) and can_override and not hard_block
    hard_block = hard_block or status_conflict
    blocked = hard_block or (bool(findings_tuple) and not overridden)
    return PolicyCheckResult(
        status="blocked" if blocked else "pass",
        findings=findings_tuple,
        content_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        hard_block=hard_block,
        overridden=overridden,
        override_reason=override_reason.strip() if overridden and override_reason else None,
    )


def _fail_closed(check) -> PolicyCheckResult:
    try:
        return check()
    except Exception:  # noqa: BLE001 - compliance failures must not fail open
        return PolicyCheckResult(
            status="blocked",
            findings=("POLICY_CHECK_ERROR",),
            content_sha256="",
            hard_block=True,
        )


def check_draft(text: str, context: PolicyContext) -> PolicyCheckResult:
    """Node 10: any finding or checker failure blocks model draft approval."""
    return _fail_closed(lambda: _evaluate(text, context, author="model", stage="draft"))


def check_final_text(
    text: str,
    context: PolicyContext,
    *,
    author: Author,
    override_reason: str | None = None,
) -> PolicyCheckResult:
    """Node 14: recheck final text; human overrides require a reason, foreign IDs never pass."""
    return _fail_closed(
        lambda: _evaluate(
            text,
            context,
            author=author,
            stage="final",
            override_reason=override_reason,
        )
    )


def can_approve_model_draft(draft: Draft | None, result: PolicyCheckResult) -> bool:
    """Node 13 precondition: a non-empty, current, unblocked draft with a passing check."""
    return bool(
        draft is not None
        and draft.text.strip()
        and not draft.stale
        and not draft.blocked
        and result.status == "pass"
        and result.content_sha256 == hashlib.sha256(draft.text.encode("utf-8")).hexdigest()
    )
