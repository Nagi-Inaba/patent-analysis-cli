"""Immutable inventor observations and strict calendar intervals (no inferred dates)."""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date

from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_identity import InventorIdentity, PersonKey, text_ok

DATE_KINDS = frozenset({'filing', 'publication', 'priority', 'observation', 'announcement',
                        'effective', 'valid_from', 'valid_to', 'checked', 'citation_snapshot'})
_DATE = re.compile(r'[0-9]{4}(?:-[0-9]{2}(?:-[0-9]{2})?)?\Z')


def _parts(raw: str | None) -> tuple[str, date | None, date | None]:
    if raw in (None, ''):
        return ('missing', None, None)
    if not isinstance(raw, str) or _DATE.fullmatch(raw) is None:
        raise DatasetInputError('input is invalid')
    parts = [int(p) for p in raw.split('-')]
    try:
        year = parts[0]
        if len(parts) == 1:
            return ('year', date(year, 1, 1), date(year, 12, 31))
        month = parts[1]
        if len(parts) == 2:
            return ('month', date(year, month, 1),
                    date(year, month, calendar.monthrange(year, month)[1]))
        day = date(year, month, parts[2])
        return ('day', day, day)
    except ValueError:
        raise DatasetInputError('input is invalid') from None


@dataclass(frozen=True, slots=True)
class ObservationDate:
    raw: str | None
    kind: str
    precision: str
    start: date | None
    end: date | None

    def __post_init__(self) -> None:
        if self.kind not in DATE_KINDS or _parts(self.raw) != (
                self.precision, self.start, self.end):
            raise DatasetInputError('input is invalid')


def parse_observation_date(raw: str | None, *, kind: str) -> ObservationDate:
    return ObservationDate(raw, kind, *_parts(raw))


@dataclass(frozen=True, slots=True)
class PatentObservation:
    record_id: str
    inventors: tuple[InventorIdentity, ...]
    observed_date: ObservationDate
    publication_id: str | None = None
    application_id: str | None = None
    family_id: str | None = None
    classifications: tuple[tuple[str, str], ...] = ()
    applicant_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    source_ordinal: int | None = None
    source_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if (not text_ok(self.record_id) or not self.record_id.strip()
                or not isinstance(self.inventors, tuple) or len(self.inventors) > 64
                or not all(isinstance(p, InventorIdentity) for p in self.inventors)
                or not isinstance(self.observed_date, ObservationDate)
                or any(v is not None and (not text_ok(v) or not v.strip()) for v in
                       (self.publication_id, self.application_id, self.family_id))
                or not isinstance(self.classifications, tuple)
                or len(self.classifications) > 64
                or any(not isinstance(v, tuple) or len(v) != 2
                       or not all(text_ok(s) for s in v) for v in self.classifications)
                or any(not isinstance(v, tuple) or len(v) > 64
                       or not all(text_ok(s) for s in v)
                       for v in (self.applicant_ids, self.source_ids))
                or not isinstance(self.source_fields, tuple)
                or not all(isinstance(s, str) for s in self.source_fields)
                or (self.source_ordinal is not None and
                    (type(self.source_ordinal) is not int or self.source_ordinal < 1))):
            raise DatasetInputError('input is invalid')
        for field in ('classifications', 'applicant_ids', 'source_ids'):
            object.__setattr__(self, field, tuple(sorted(set(getattr(self, field)))))

    @property
    def inventor_keys(self) -> tuple[PersonKey, ...]:
        return tuple(sorted({p.key for p in self.inventors}))

    def semantic_key(self) -> tuple:
        """Comparison independent of raw value order and row position, not of evidence IDs."""
        return (self.inventor_keys, self.observed_date.kind, self.observed_date.raw or '',
                self.publication_id, self.application_id, self.family_id,
                self.classifications, self.applicant_ids, self.source_ids)
