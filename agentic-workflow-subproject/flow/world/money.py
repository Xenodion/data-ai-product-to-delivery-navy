"""Amount conversion and the objects derived from transactions: refunds, disputes, payouts."""

from collections import defaultdict
from collections.abc import Collection, Sequence
from datetime import UTC, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from flow.world.config import WorldConfig
from flow.world.models import Dispute, Merchant, Payout, Refund, Transaction
from flow.world.rng import stage_rng

MINOR_PER_UNIT = Decimal(100)
PAID_AFTER = timedelta(days=1)
PAYOUT_HOUR = 6
HELD_RECENT_PAYOUTS = 2
HELD_KYC = "under_review"
SETTLED_LIKE = ("settled", "refunded", "disputed")


def to_minor(amount: str | Decimal) -> int:
    """Convert a decimal amount to integer minor units; the only conversion in the world."""
    return int((Decimal(amount) * MINOR_PER_UNIT).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def format_amount(minor: int) -> str:
    """Format minor units as the two-decimal string the ticket labels use."""
    return f"{Decimal(minor) / MINOR_PER_UNIT:.2f}"


def _reference_moment(config: WorldConfig) -> datetime:
    return datetime.combine(config.reference_date, time(0), tzinfo=UTC)


def build_refunds(
    transactions: Sequence[Transaction], pending: Collection[str], config: WorldConfig
) -> tuple[Refund, ...]:
    """One refund per refunded transaction; pending when a refund-status ticket asks about it."""
    rng = stage_rng(config.seed, "refunds")
    ledger, reference = config.ledger, _reference_moment(config)
    refunds = []
    for transaction in sorted(transactions, key=lambda item: item.transaction_id):
        if transaction.status != "refunded" or transaction.settled_at is None:
            continue
        partial = rng.random() < ledger.partial_refund_share
        amount = transaction.amount_minor
        if partial:
            amount = max(1, int(amount * ledger.partial_refund_fraction))
        refunds.append(
            Refund(
                refund_id=f"R-{len(refunds) + 1:06d}",
                transaction_id=transaction.transaction_id,
                amount_minor=amount,
                status="pending" if transaction.transaction_id in pending else "completed",
                created_at=min(transaction.settled_at + PAID_AFTER, reference),
            )
        )
    return tuple(refunds)


def build_disputes(
    transactions: Sequence[Transaction],
    cited: Collection[str],
    chargebacks: Collection[str],
    config: WorldConfig,
) -> tuple[Dispute, ...]:
    """Open disputes for disputed transactions, and a few won ones on settled filler rows."""
    rng = stage_rng(config.seed, "disputes")
    ledger, reference = config.ledger, _reference_moment(config)
    disputes = []
    for transaction in sorted(transactions, key=lambda item: item.transaction_id):
        if transaction.settled_at is None:
            continue
        if transaction.status == "disputed":
            status = (
                "open"
                if transaction.transaction_id in chargebacks
                else rng.choice(("open", "under_review"))
            )
        elif (
            transaction.status == "settled"
            and transaction.transaction_id not in cited
            and rng.random() < ledger.closed_dispute_rate
        ):
            status = "won"
        else:
            continue
        opened = min(transaction.settled_at + PAID_AFTER, reference)
        disputes.append(
            Dispute(
                dispute_id=f"D-{len(disputes) + 1:06d}",
                transaction_id=transaction.transaction_id,
                status=status,
                reason=rng.choice(ledger.dispute_reasons),
                opened_at=opened,
                due_at=opened + timedelta(days=ledger.dispute_days),
            )
        )
    return tuple(disputes)


def build_payouts(
    transactions: Sequence[Transaction], merchants: Sequence[Merchant], config: WorldConfig
) -> tuple[Payout, ...]:
    """Weekly payouts: settled amounts of a merchant and currency, net of its fee.

    A payout scheduled after the reference date is ``scheduled``. The latest payouts of a merchant
    whose KYC is under review are ``held``.
    """
    by_merchant = {merchant.merchant_id: merchant for merchant in merchants}
    weeks: dict[tuple[str, str, datetime], int] = defaultdict(int)
    for transaction in transactions:
        if transaction.status == "settled" and transaction.settled_at is not None:
            day = transaction.settled_at.date()
            monday = datetime.combine(day - timedelta(days=day.weekday()), time(0), tzinfo=UTC)
            weeks[(transaction.merchant_id, transaction.currency, monday)] += (
                transaction.amount_minor
            )
    reference = _reference_moment(config)
    payouts: list[Payout] = []
    latest_ids: dict[str, list[int]] = defaultdict(list)
    for merchant_id, currency, monday in sorted(weeks):
        fee_bps = by_merchant[merchant_id].fee_bps
        net = weeks[(merchant_id, currency, monday)] * (10_000 - fee_bps) // 10_000
        if net <= 0:
            continue
        scheduled = monday + timedelta(days=7, hours=PAYOUT_HOUR)
        paid = scheduled + PAID_AFTER
        pay_status = "paid" if paid <= reference else "scheduled"
        payouts.append(
            Payout(
                payout_id=f"P-{len(payouts) + 1:06d}",
                merchant_id=merchant_id,
                amount_minor=net,
                currency=currency,
                status=pay_status,
                scheduled_at=scheduled,
                paid_at=paid if pay_status == "paid" else None,
            )
        )
        latest_ids[merchant_id].append(len(payouts) - 1)
    for merchant_id, indexes in latest_ids.items():
        if by_merchant[merchant_id].kyc_status != HELD_KYC:
            continue
        for index in indexes[-HELD_RECENT_PAYOUTS:]:
            payouts[index] = payouts[index].model_copy(
                update={
                    "status": "held",
                    "paid_at": None,
                    "held_reason": config.ledger.payout_hold_reason,
                }
            )
    return tuple(payouts)
