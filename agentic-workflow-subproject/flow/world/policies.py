"""Load the knowledge documents of the flow as policies."""

import json
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from flow.world.config import WorldConfig
from flow.world.errors import DeckContractError
from flow.world.models import Desk, Policy, PolicyStatus, PolicySubIntent


class _Document(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    source_id: str
    version: str
    desk: Desk
    sub_intents: tuple[str, ...]
    title: str
    content: str
    status: PolicyStatus
    valid_from: date
    valid_until: date | None


def load_policies(
    path: Path, config: WorldConfig
) -> tuple[tuple[Policy, ...], tuple[PolicySubIntent, ...]]:
    """Read ``knowledge.json`` into ``policies`` and ``policy_sub_intents`` rows.

    Raises:
        DeckContractError: the file is unreadable or a document breaks the contract.
    """
    try:
        documents = json.loads(path.read_text(encoding="utf-8"))["documents"]
        parsed = [_Document.model_validate(document) for document in documents]
    except (OSError, KeyError, ValueError) as error:
        raise DeckContractError(f"knowledge file {path.name}: {error}") from error
    policies = tuple(
        Policy(
            source_id=item.source_id,
            version=item.version,
            desk=item.desk,
            language=config.policies.language,
            status=item.status,
            valid_from=item.valid_from,
            valid_until=item.valid_until,
            owner=config.policies.owner,
            title=item.title,
            text=item.content,
        )
        for item in parsed
    )
    links = tuple(
        PolicySubIntent(source_id=item.source_id, version=item.version, sub_intent=sub_intent)
        for item in parsed
        for sub_intent in item.sub_intents
    )
    return policies, links
