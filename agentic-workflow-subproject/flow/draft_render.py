"""Turn the Drafter's JSON answer into the reply text: parse, check, then add greeting and closing.

The model writes the body only, as segments that each name the sources they rest on. The code owns
everything else: the greeting and closing in the merchant's language, the removal of quotes, and the
rules that keep placeholders, bare references and ungrounded figures out of the reply.
"""

import json
import re

from pydantic import BaseModel, ConfigDict, ValidationError

from flow.contracts import FlowConfig, PreparationMode
from flow.llm import DraftRejected

DEFAULT_LANGUAGE = "en"
REFERENCE_REASONS = frozenset(
    {
        "PAYMENT_ID_ABSENT",
        "PAYMENT_ID_UNVERIFIED",
        "PAYMENT_NOT_FOUND",
        "PAYMENT_CANDIDATES_REQUIRE_SELECTION",
    }
)

OUTPUT_CONTRACT = (
    "Output format (this overrides any earlier instruction about citations or layout): answer with one "
    'JSON object only, no code fence: {"language": "<en|fr|es|de|it>", "segments": '
    '[{"text": "<one or two sentences>", "source_ids": ["<allowed source id>"]}]}. '
    "Write the body of the reply only: no greeting, no sign-off, no quotation marks, no placeholder. "
    "Put in source_ids the allowed source IDs that support the segment; use an empty list for a "
    "question or a neutral sentence. Never write a source ID inside the text. A segment without a "
    "source must not state a figure, a reference or the state of an account. Do not repeat numbers "
    "from the ticket; say \"your payment\" or \"this case\" instead."
)
LANGUAGE_SENTENCE = " The ticket language is {language}: write the text in it and set language to {language}."

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)
_PLACEHOLDER = re.compile(r"[\[\]{}<>]|\b(?:your\s+name|xxx+|lorem)\b", re.IGNORECASE)
_REFERENCE = re.compile(r"\b(?:TX|M)-\d+\b", re.IGNORECASE)
_GREETING_PREFIX = re.compile(
    r"^(?:hello|hi|dear|bonjour|bonsoir|cher|ch[èe]re|hola|estimad[oa]|hallo|guten\s+(?:tag|morgen|abend)|"
    r"sehr\s+geehrte[rn]?|buongiorno|buonasera|gentile|ciao)\b[^,.!:?\n]{0,40}[,.!:]\s*",
    re.IGNORECASE,
)
_SIGN_OFF = re.compile(
    r"^(?:best\s+regards|kind\s+regards|regards|sincerely|cordialement|bien\s+cordialement|"
    r"saludos|atentamente|un\s+saludo|mit\s+freundlichen\s+gr[üu](?:ß|ss)en|viele\s+gr[üu](?:ß|ss)e|"
    r"cordiali\s+saluti|distinti\s+saluti|keelpay)\b[^.?!]{0,40}[,.!]?$",
    re.IGNORECASE,
)
MAX_SEGMENTS = 4
# The reply speaks for the team: "we", never "I" / "je" / "me".
_FIRST_PERSON_EN = re.compile(r"\bI\b|\bI['’](?:m|ll|ve|d)\b")
_FIRST_PERSON = re.compile(r"\b(?:je|j['’]\w+|me|m['’]\w+|ich)\b", re.IGNORECASE)
_QUOTES = "\"'“”«»"


class Segment(BaseModel):
    """One sentence or two of the reply and the sources it rests on."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    text: str
    source_ids: tuple[str, ...] = ()


class _Reply(BaseModel):
    model_config = ConfigDict(extra="ignore")

    language: str = ""
    segments: list[Segment]


def _strip_quotes(text: str) -> str:
    text = text.strip()
    while len(text) > 1 and text[0] in _QUOTES and text[-1] in _QUOTES:
        text = text[1:-1].strip()
    return text


def parse_reply(raw: str) -> tuple[str, tuple[Segment, ...]]:
    """Declared language and cleaned segments of the model's answer.

    Raises:
        DraftRejected: the answer is not the expected JSON, or nothing is left after clean-up.
    """
    try:
        reply = _Reply.model_validate(json.loads(_FENCE.sub("", raw.strip())))
    except (ValueError, ValidationError) as exc:
        raise DraftRejected("Drafter answer is not the expected JSON") from exc
    segments = []
    for index, segment in enumerate(reply.segments):
        text = _strip_quotes(segment.text)
        if index == 0:
            text = _GREETING_PREFIX.sub("", text, count=1).strip()  # the code adds its own greeting
        if not text or (index == len(reply.segments) - 1 and _SIGN_OFF.match(text)):
            continue
        segments.append(Segment(text=text, source_ids=segment.source_ids))
    if not segments:
        raise DraftRejected("Drafter answer has no body")
    if len(segments) > MAX_SEGMENTS:
        raise DraftRejected(f"Drafter wrote {len(segments)} segments, at most {MAX_SEGMENTS}")
    return reply.language.strip().lower(), tuple(segments)


def check_segments(
    segments: tuple[Segment, ...],
    mode: PreparationMode,
    allowed_source_ids: frozenset[str],
    known_text: str = "",
) -> tuple[str, ...]:
    """Rules of the output contract; returns the sources used, in order of first use.

    Raises:
        DraftRejected: a placeholder, an unknown source, a bare reference, or no grounding.
    """
    grounded = mode == "factual"  # facts must cite their source; guidance may simply shape a question
    used: dict[str, None] = {}
    for segment in segments:
        if _FIRST_PERSON_EN.search(segment.text) or _FIRST_PERSON.search(segment.text):
            raise DraftRejected("Drafter wrote in the first person singular: write as we")
        if _PLACEHOLDER.search(segment.text):
            raise DraftRejected("Drafter left a placeholder or a bracket in the reply")
        if any(source not in allowed_source_ids for source in segment.source_ids):
            raise DraftRejected("Drafter cited an unknown source")
        known = known_text.casefold()
        if any(ref.casefold() not in known for ref in _REFERENCE.findall(segment.text)):
            raise DraftRejected("Drafter wrote a reference that is neither in the ticket nor in the evidence")
        used.update(dict.fromkeys(segment.source_ids))
    if grounded and not used:
        raise DraftRejected("Drafter used no supplied source")
    return tuple(used)


def pick_language(ticket_language: str | None, declared: str, config: FlowConfig) -> str:
    """The ticket's language when known, else the one the model declared, else English."""
    for candidate in (ticket_language, declared):
        if candidate and candidate.lower() in config.drafter_greeting:
            return candidate.lower()
    return DEFAULT_LANGUAGE


def render(language: str, segments: tuple[Segment, ...], config: FlowConfig) -> str:
    """Greeting, body and closing in the chosen language."""
    body = " ".join(segment.text for segment in segments)
    return f"{config.drafter_greeting[language]}\n\n{body}\n\n{config.drafter_closing[language]}"


def template_question(language: str, reason_codes: tuple[str, ...], config: FlowConfig) -> str:
    """Code-written clarification used when the model cannot produce a valid one."""
    kind = "reference" if REFERENCE_REASONS & set(reason_codes) else "details"
    question = config.drafter_fallback_question[language][kind]
    return f"{config.drafter_greeting[language]}\n\n{question}\n\n{config.drafter_closing[language]}"
