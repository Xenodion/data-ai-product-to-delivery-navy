"""Langfuse prompt retrieval shared by the LLM nodes."""

import logging
from dataclasses import dataclass
from typing import Any, Literal

from langfuse import get_client

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _LocalPrompt:
    template: str | list[dict[str, str]]

    def compile(self, **variables: str) -> str | list[dict[str, str]]:
        def render(value: str) -> str:
            compiled = value
            for key, replacement in variables.items():
                compiled = compiled.replace("{{" + key + "}}", replacement)
            return compiled

        if isinstance(self.template, str):
            return render(self.template)
        return [
            {"role": message["role"], "content": render(message["content"])}
            for message in self.template
        ]


@dataclass(frozen=True)
class PromptRelease:
    prompt: Any
    name: str
    label: str
    version: str

    @property
    def source(self) -> str:
        return "langfuse" if self.version != "local-fallback" else "local-fallback"

    def compile(self, **variables: str) -> Any:
        return self.prompt.compile(**variables)


def fetch_prompt(
    *,
    name: str,
    label: str,
    prompt_type: Literal["chat", "text"],
    fallback: str | list[dict[str, str]],
) -> PromptRelease:
    """Fetch a labelled immutable Langfuse prompt, with the local template as outage fallback."""
    try:
        prompt = get_client().get_prompt(
            name,
            label=label,
            type=prompt_type,
            fallback=fallback,
            max_retries=1,
            fetch_timeout_seconds=3,
        )
        version = getattr(prompt, "version", None)
    except Exception as exc:
        logger.warning("Langfuse prompt %s/%s unavailable; using local fallback: %s", name, label, exc)
        prompt = _LocalPrompt(fallback)
        version = None
    return PromptRelease(
        prompt=prompt,
        name=name,
        label=label,
        version=str(version) if version is not None else "local-fallback",
    )


def record_prompt_release(release: PromptRelease) -> None:
    """Attach prompt identity to the active node span without recording prompt variables."""
    get_client().update_current_span(
        metadata={
            "prompt_name": release.name,
            "prompt_label": release.label,
            "prompt_version": release.version,
            "prompt_source": release.source,
        }
    )
