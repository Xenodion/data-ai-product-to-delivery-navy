"""Deterministic signals read from ticket text: cited transaction references and absolute dates.

These are heuristics used offline by the world builder. References are validated against the deck
annotations by the audit; dates are reviewed on samples.
"""

import calendar
import re
import unicodedata
from datetime import date

from pydantic import BaseModel, ConfigDict

_PREFIXED_REFERENCE = re.compile(r"\bTX\s?-?\s?(\d(?:\s*\d){5})(?!\d)", re.IGNORECASE)

_YEAR = re.compile(
    r"(?<![\d.,])(?<![A-Za-z]-)(20[2-3]\d)(?!\d|[.,]\d|-\d|/\d)"
)  # not an amount or an id
_ISO_DATE = re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b")
_NUMERIC_DATE = re.compile(r"\b(\d{1,2})[/.](\d{1,2})[/.](20\d{2})\b")
_DAY_MONTH_YEAR = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th|er)?\.?\s+([^\W\d_]{3,10})\.?,?\s+(20\d{2})\b"
)
_MONTH_DAY_YEAR = re.compile(r"\b([^\W\d_]{3,10})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(20\d{2})\b")
_MONTHS = {
    "january": 1, "janvier": 1, "jan": 1, "janv": 1,
    "february": 2, "fevrier": 2, "feb": 2, "fev": 2, "fevr": 2,
    "march": 3, "mars": 3, "mar": 3,
    "april": 4, "avril": 4, "apr": 4, "avr": 4,
    "may": 5, "mai": 5,
    "june": 6, "juin": 6, "jun": 6,
    "july": 7, "juillet": 7, "jul": 7, "juil": 7,
    "august": 8, "aout": 8, "aug": 8,
    "september": 9, "septembre": 9, "sep": 9, "sept": 9,
    "october": 10, "octobre": 10, "oct": 10,
    "november": 11, "novembre": 11, "nov": 11,
    "december": 12, "decembre": 12, "dec": 12,
    "januar": 1, "enero": 1, "gennaio": 1, "februar": 2, "febrero": 2, "febbraio": 2,
    "marz": 3, "maerz": 3, "marzo": 3, "aprile": 4, "abril": 4, "mayo": 5, "maggio": 5,
    "juni": 6, "junio": 6, "giugno": 6, "juli": 7, "julio": 7, "luglio": 7,
    "agosto": 8, "septiembre": 9, "settembre": 9, "oktober": 10, "octubre": 10, "ottobre": 10,
    "noviembre": 11, "dezember": 12, "diciembre": 12, "dicembre": 12,
}  # fmt: skip


class TextDates(BaseModel):
    """Absolute dates and years cited in a ticket."""

    model_config = ConfigDict(frozen=True)

    full_dates: tuple[date, ...]
    years: tuple[int, ...]

    @property
    def latest_bound(self) -> date | None:
        """Latest date the text allows: no ticket may be dated before it."""
        candidates = [*self.full_dates, *(date(year, 1, 1) for year in self.years)]
        return max(candidates) if candidates else None

    @property
    def latest_full_date(self) -> date | None:
        """Latest complete date cited, used to keep current tickets from citing stale events."""
        return max(self.full_dates) if self.full_dates else None

    @property
    def earliest_full_date(self) -> date | None:
        """Earliest complete date cited; years alone are too vague to bound anything."""
        return min(self.full_dates) if self.full_dates else None


def extract_references(text: str) -> tuple[str, ...]:
    """Return the canonical ``TX-dddddd`` references cited with a TX prefix, in order, unique."""
    found: list[str] = []
    for match in _PREFIXED_REFERENCE.finditer(text):
        reference = "TX-" + re.sub(r"\D", "", match.group(1))
        if reference not in found:
            found.append(reference)
    return tuple(found)


def _month_number(name: str) -> int | None:
    stripped = unicodedata.normalize("NFKD", name.lower())
    key = "".join(char for char in stripped if not unicodedata.combining(char))
    return _MONTHS.get(key)


def _valid_date(year: int, month: int, day: int) -> date | None:
    if not 1 <= month <= 12:
        return None
    if not 1 <= day <= calendar.monthrange(year, month)[1]:
        return None
    return date(year, month, day)


def extract_text_dates(text: str) -> TextDates:
    """Collect complete dates (ISO, numeric day-first, day-month-year, month-day-year) and years."""
    dates: set[date] = set()
    for year, month, day in _ISO_DATE.findall(text):
        found = _valid_date(int(year), int(month), int(day))
        if found:
            dates.add(found)
    for day, month, year in _NUMERIC_DATE.findall(text):
        found = _valid_date(int(year), int(month), int(day))
        if found:
            dates.add(found)
    for day, name, year in _DAY_MONTH_YEAR.findall(text):
        month = _month_number(name)
        found = _valid_date(int(year), month, int(day)) if month else None
        if found:
            dates.add(found)
    for name, day, year in _MONTH_DAY_YEAR.findall(text):
        month = _month_number(name)
        found = _valid_date(int(year), month, int(day)) if month else None
        if found:
            dates.add(found)
    years = sorted({int(year) for year in _YEAR.findall(text)} | {found.year for found in dates})
    return TextDates(full_dates=tuple(sorted(dates)), years=tuple(years))
