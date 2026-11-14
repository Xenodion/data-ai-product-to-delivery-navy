"""Typed configuration of the merchant world builder.

Every tunable value lives in ``data/world/world.toml``; none appears in builder logic.
"""

import tomllib
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from flow.world.errors import ConfigError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "data" / "world" / "world.toml"
EXCHANGE_COUNTS = (0, 1, 2)
WEIGHT_TOLERANCE = 1e-6


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _check_weights(name: str, weights: dict) -> None:
    if any(weight < 0 for weight in weights.values()):
        raise ValueError(f"{name} must not contain negative weights")
    if abs(sum(weights.values()) - 1.0) > WEIGHT_TOLERANCE:
        raise ValueError(f"{name} must sum to 1")


class SampleConfig(_Strict):
    """Sizes of the sampled ticket roles (design section 3)."""

    current: int = Field(gt=0)
    history: int = Field(gt=0)
    dev: int = Field(gt=0)


class DatesConfig(_Strict):
    """Role windows inside the simulated period, in days counted back from its end."""

    history_gap_days: int = Field(gt=0)  # history ends this long before the window end
    open_days: int = Field(gt=0)  # current and dev tickets fall in the last days of the window
    max_cited_age_days: int = Field(gt=0)  # a current/dev ticket may not cite an older date


class PlanConfig(_Strict):
    """Commercial plan attached to a volume tier."""

    name: str
    fee_bps: int = Field(ge=0)


class MerchantsConfig(_Strict):
    """Draw weights and word lists of merchant attributes that the tickets cannot determine."""

    tier_weights_without_amount: dict[Literal["small", "medium", "large"], float]
    plans: dict[Literal["small", "medium", "large"], PlanConfig]
    kyc_weights: dict[Literal["verified", "pending", "under_review"], float]
    risk_weights: dict[Literal["low", "medium", "high"], float]
    country_by_language: dict[str, str]
    ticket_count_alpha: float = Field(gt=0)  # Pareto shape of the tickets per merchant
    onboarding_days_before: tuple[int, int]  # onboarding precedes the earliest cited date
    name_first: tuple[str, ...] = Field(min_length=2)
    name_second: tuple[str, ...] = Field(min_length=2)

    @model_validator(mode="after")
    def _check(self) -> "MerchantsConfig":
        tiers = {"small", "medium", "large"}
        if set(self.tier_weights_without_amount) != tiers or set(self.plans) != tiers:
            raise ValueError("tier_weights_without_amount and plans must define every tier")
        if set(self.kyc_weights) != {"verified", "pending", "under_review"}:
            raise ValueError("kyc_weights must define verified, pending and under_review")
        if set(self.risk_weights) != {"low", "medium", "high"}:
            raise ValueError("risk_weights must define low, medium and high")
        for name in ("tier_weights_without_amount", "kyc_weights", "risk_weights"):
            _check_weights(name, getattr(self, name))
        low, high = self.onboarding_days_before
        if not 0 < low <= high:
            raise ValueError("onboarding_days_before must be an increasing pair of positive days")
        if len(self.name_first) * len(self.name_second) < 400:
            raise ValueError("name word lists must allow at least 400 distinct names")
        return self


class LedgerConfig(_Strict):
    """Rules of the ledger (design section 6): cited rows, realism rules, filler, money objects."""

    amount_mismatch_pct: float = Field(gt=0, lt=1)
    duplicate_gap_minutes: int = Field(gt=0)
    default_status: Literal[
        "settled", "processing", "under_review", "failed", "refunded", "disputed"
    ]
    status_by_sub_intent: dict[
        str, Literal["settled", "processing", "under_review", "failed", "refunded", "disputed"]
    ]
    payment_methods: dict[str, float]
    filler_status_weights: dict[
        Literal["settled", "processing", "under_review", "failed", "refunded", "disputed"], float
    ]
    amount_range_minor: dict[Literal["small", "medium", "large"], tuple[int, int]]
    cited_age_days: tuple[int, int]  # a cited transaction is this old when its ticket opens
    pending_max_days: int = Field(gt=0)  # filler older than this is no longer processing
    partial_refund_share: float = Field(ge=0, le=1)
    partial_refund_fraction: float = Field(gt=0, lt=1)
    dispute_days: int = Field(gt=0)
    dispute_reasons: tuple[str, ...] = Field(min_length=1)
    closed_dispute_rate: float = Field(ge=0, le=1)  # settled filler with a won or lost dispute
    payout_hold_reason: str

    @model_validator(mode="after")
    def _check(self) -> "LedgerConfig":
        _check_weights("payment_methods", self.payment_methods)
        _check_weights("filler_status_weights", self.filler_status_weights)
        if set(self.amount_range_minor) != {"small", "medium", "large"}:
            raise ValueError("amount_range_minor must define every tier")
        if any(low <= 0 or low > high for low, high in self.amount_range_minor.values()):
            raise ValueError("amount_range_minor needs 0 < low <= high")
        low, high = self.cited_age_days
        if not 2 <= low <= high:
            raise ValueError("cited_age_days must be an increasing pair starting at 2 or more")
        return self


class ThreadConfig(_Strict):
    """Draw weights of the history thread plans (design section 7)."""

    exchange_weights: dict[int, float]
    end_state_weights: dict[Literal["closed", "open_awaiting_merchant"], float]
    role: str = "writer_train"  # role of the dataset-build run.toml that writes the replies
    max_tokens: int = Field(default=1400, gt=0)
    max_chars: int = Field(default=1500, gt=0)  # longest accepted message
    reply_hours: tuple[int, int] = (1, 12)  # agent reply delay
    chase_days: tuple[int, int] = (1, 3)  # merchant follow-up delay
    resolution: str = "resolved"
    fallback_question: dict[str, str] = {}  # closing question of a fallback thread, by language

    @model_validator(mode="after")
    def _check(self) -> "ThreadConfig":
        if tuple(sorted(self.exchange_weights)) != EXCHANGE_COUNTS:
            raise ValueError(f"exchange_weights must define exactly {EXCHANGE_COUNTS}")
        if set(self.end_state_weights) != {"closed", "open_awaiting_merchant"}:
            raise ValueError("end_state_weights must define closed and open_awaiting_merchant")
        _check_weights("exchange_weights", self.exchange_weights)
        _check_weights("end_state_weights", self.end_state_weights)
        return self


class BudgetConfig(_Strict):
    """Spending caps of the paid generation and the folder of its call log."""

    cap_usd: float = Field(gt=0)
    pilot_cap_usd: float = Field(gt=0)
    calls_dir: Path

    @model_validator(mode="after")
    def _pilot_within_cap(self) -> "BudgetConfig":
        if self.pilot_cap_usd > self.cap_usd:
            raise ValueError("pilot_cap_usd must not exceed cap_usd")
        return self


class PathsConfig(_Strict):
    """Locations relative to the subproject root."""

    deck_dir: Path
    knowledge_path: Path
    database_path: Path
    artifacts_dir: Path
    oracle_dir: Path


class PoliciesConfig(_Strict):
    """How the knowledge documents of the flow are stored as policies."""

    language: str = Field(min_length=2, max_length=2)
    owner: str


class WorldConfig(_Strict):
    """Whole configuration of one world build."""

    seed: int
    reference_date: date
    window_start: date
    window_end: date
    text_newline: Literal["lf", "crlf"]
    merchant_target: int = Field(gt=0)
    transactions_per_merchant: int = Field(gt=0)
    fx_to_eur: dict[str, float]
    sample: SampleConfig
    dates: DatesConfig
    merchants: MerchantsConfig
    ledger: LedgerConfig
    threads: ThreadConfig
    policies: PoliciesConfig
    budget: BudgetConfig
    paths: PathsConfig

    @model_validator(mode="after")
    def _check_consistency(self) -> "WorldConfig":
        if not self.window_start < self.window_end <= self.reference_date:
            raise ValueError("window_start < window_end <= reference_date must hold")
        if self.fx_to_eur.get("EUR") != 1.0:
            raise ValueError("fx_to_eur must define EUR = 1.0")
        if any(rate <= 0 for rate in self.fx_to_eur.values()):
            raise ValueError("fx_to_eur rates must be positive")
        window_days = (self.window_end - self.window_start).days
        if not self.dates.open_days < self.dates.history_gap_days < window_days:
            raise ValueError("open_days < history_gap_days < window length must hold")
        return self

    def resolve(self, path: Path) -> Path:
        """Resolve a configured relative path against the subproject root."""
        return path if path.is_absolute() else PROJECT_ROOT / path


def load_world_config(path: Path = DEFAULT_CONFIG_PATH) -> WorldConfig:
    """Load and validate the world configuration.

    Raises:
        ConfigError: the file is missing or is not valid TOML.
        pydantic.ValidationError: a value is missing, unknown or inconsistent.
    """
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ConfigError(f"world configuration not found: {path}") from error
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"world configuration is not valid TOML: {path}: {error}") from error
    return WorldConfig.model_validate(raw)
