"""Minimal OpenRouter client with a hard budget guard. The API key is passed in, never logged."""

import json
import re
import tomllib
from pathlib import Path

import httpx
from pydantic import BaseModel, ConfigDict
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

RUN_CONFIG_PATH = Path(__file__).parent / "config" / "run.toml"


class BudgetExhaustedError(RuntimeError):
    """Raised before a call that could cross the budget, or when the API answers 'payment required'."""


class ApiError(RuntimeError):
    """A non-recoverable API answer (bad request, unexpected response shape)."""


class _TransientError(RuntimeError):
    """Network error, 429 or 5xx: worth a short retry."""


class RoleConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    model: str
    temperature: float
    max_tokens: int
    price_in: float
    price_out: float


class ProductionConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    batch_sizes: list[int]
    max_nonconformity: float
    min_batch_for_rates: int
    trap_min_attempts: int
    trap_max_failure: float
    cost_per_ticket_estimate: float
    cost_factor: float
    attempts_factor: float
    accepted_floor: float
    voter_b_fraction: dict[str, float]
    writer_role: dict[str, str]
    reserve_buckets: dict[str, list[int]]


class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_url: str
    budget_usd: float
    timeout_seconds: float
    transient_retries: int
    max_consecutive_errors: int
    production: ProductionConfig
    roles: dict[str, RoleConfig]


class Completion(BaseModel):
    content: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


def load_run_config(path: Path = RUN_CONFIG_PATH) -> RunConfig:
    with path.open("rb") as handle:
        return RunConfig.model_validate(tomllib.load(handle))


class Budget:
    """Running total of the money spent, rebuilt from the call logs so that a resumed run keeps counting."""

    def __init__(self, limit_usd: float, spent_usd: float = 0.0) -> None:
        self.limit_usd = limit_usd
        self.spent_usd = spent_usd

    @classmethod
    def from_logs(cls, limit_usd: float, log_dir: Path) -> "Budget":
        spent = 0.0
        for log in log_dir.rglob("*.jsonl"):
            for line in log.read_text(encoding="utf-8").splitlines():
                spent += json.loads(line).get("cost_usd", 0.0)
        return cls(limit_usd, spent)

    def ensure(self, estimate_usd: float) -> None:
        if self.spent_usd + estimate_usd > self.limit_usd:
            raise BudgetExhaustedError(
                f"spent {self.spent_usd:.4f} + next call about {estimate_usd:.4f} would exceed {self.limit_usd:.2f} USD"
            )

    def add(self, cost_usd: float) -> None:
        self.spent_usd += cost_usd


def estimate_call_cost(role: RoleConfig, system: str, user: str) -> float:
    """Prudent estimate of one call: prompt at 3 characters per token, the full max_tokens as output."""
    prompt_tokens = (len(system) + len(user)) / 3.0
    return (prompt_tokens * role.price_in + role.max_tokens * role.price_out) / 1e6


def complete(
    client: httpx.Client,
    config: RunConfig,
    role: RoleConfig,
    api_key: str,
    system: str,
    user: str,
) -> Completion:
    """One chat completion; BudgetExhaustedError on 'payment required', ApiError on other client errors."""
    body = {
        "model": role.model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": role.temperature,
        "max_tokens": role.max_tokens,
        "response_format": {"type": "json_object"},
        "reasoning": {"enabled": False},
        "usage": {"include": True},
    }

    @retry(
        retry=retry_if_exception_type(_TransientError),
        stop=stop_after_attempt(config.transient_retries),
        wait=wait_exponential(multiplier=1, max=10),
        reraise=True,
    )
    def post() -> dict:
        try:
            response = client.post(
                f"{config.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=body,
                timeout=config.timeout_seconds,
            )
        except httpx.TransportError as error:
            raise _TransientError(type(error).__name__) from error
        if response.status_code == 402:
            raise BudgetExhaustedError(
                "OpenRouter answered 402 (payment required): key limit reached"
            )
        if response.status_code == 429 or response.status_code >= 500:
            raise _TransientError(f"HTTP {response.status_code}")
        if response.status_code >= 400:
            raise ApiError(f"HTTP {response.status_code}: {response.text[:300]}")
        return response.json()

    payload = post()
    try:
        content = payload["choices"][0]["message"]["content"] or ""
        usage = payload.get("usage", {})
        prompt_tokens = int(usage.get("prompt_tokens", 0))
        completion_tokens = int(usage.get("completion_tokens", 0))
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise ApiError(f"unexpected response shape: {str(payload)[:300]}") from error
    cost = usage.get("cost")
    if cost is None:
        cost = (
            prompt_tokens * role.price_in + completion_tokens * role.price_out
        ) / 1e6
    return Completion(
        content=content,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=float(cost),
    )


def parse_json_object(content: str) -> dict[str, object]:
    """Parse a model answer into a JSON object; tolerates a markdown fence around it."""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # some models write JSON strings as JavaScript concatenations: "part one" + "part two"
        data = json.loads(re.sub(r'"\s*\+\s*"', "", text))
    if not isinstance(data, dict):
        raise TypeError("answer is not a JSON object")
    return data


def parse_ticket_json(content: str) -> tuple[str, str]:
    """Extract (subject, body) from the writer's answer."""
    data = parse_json_object(content)
    subject, body = data.get("subject", ""), data.get("body")
    if not isinstance(subject, str) or not isinstance(body, str):
        raise TypeError("answer is not an object with string subject and body")
    return subject, body
