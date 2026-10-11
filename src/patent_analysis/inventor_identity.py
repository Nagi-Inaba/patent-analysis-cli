"""Explicit inventor identity; never repair or normalize opaque identifiers."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from types import MappingProxyType

from patent_analysis.errors import DatasetInputError

MAX_IDENTITIES = 1000
MAX_ALIASES = 5000
MAX_TEXT = 2048
PersonKey = tuple[str, str]


def text_ok(value: object, *, empty: bool = False) -> bool:
    return (isinstance(value, str) and (empty or bool(value)) and len(value) <= MAX_TEXT
            and not any(0xD800 <= ord(c) <= 0xDFFF or ord(c) < 32 for c in value))


def name_key(value: str) -> str:
    if not text_ok(value, empty=True):
        raise DatasetInputError('input is invalid')
    return unicodedata.normalize('NFKC', value).strip()


@dataclass(frozen=True, slots=True)
class Alias:
    kind: str
    raw_alias: str
    inventor_id: str
    display_name: str
    source_ids: tuple[str, ...]
    status: str = 'confirmed'

    def __post_init__(self) -> None:
        if (self.kind not in {'id', 'name'} or self.status not in {'confirmed', 'candidate'}
                or not all(text_ok(v) for v in
                           (self.raw_alias, self.inventor_id, self.display_name))
                or not isinstance(self.source_ids, tuple) or not self.source_ids
                or len(self.source_ids) > 64 or len(set(self.source_ids)) != len(self.source_ids)
                or not all(text_ok(v) for v in self.source_ids)
                or (self.kind == 'name' and not name_key(self.raw_alias))):
            raise DatasetInputError('input is invalid')


@dataclass(frozen=True, slots=True)
class InventorIdentity:
    canonical_id: str | None
    display_name: str
    status: str
    raw_id: str | None
    raw_name: str | None
    candidate_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    caveats: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if (self.status not in {'provided_id', 'curated_mapping', 'normalized_name_only',
                               'ambiguous'} or not text_ok(self.display_name)
                or any(v is not None and not text_ok(v, empty=True)
                       for v in (self.canonical_id, self.raw_id, self.raw_name))
                or any(not isinstance(v, tuple) or len(v) > 64
                       or not all(text_ok(s) for s in v) or len(set(v)) != len(v)
                       for v in (self.candidate_ids, self.source_ids, self.caveats))):
            raise DatasetInputError('input is invalid')
        if self.status == 'provided_id':
            valid = bool(self.raw_id) and self.canonical_id == self.raw_id
        elif self.status == 'curated_mapping':
            valid = bool(self.canonical_id) and bool(self.source_ids)
        elif self.status == 'normalized_name_only':
            valid = (self.canonical_id is None and self.raw_id in (None, '')
                     and bool(name_key(self.raw_name or ''))
                     and self.display_name == name_key(self.raw_name or '')
                     and self.caveats == ('name_match_is_not_person_confirmation',))
        else:
            valid = (self.canonical_id is None and bool(self.candidate_ids)
                     and bool(self.source_ids))
        if not valid or (self.status != 'ambiguous' and self.candidate_ids):
            raise DatasetInputError('input is invalid')

    @property
    def key(self) -> PersonKey:
        if self.canonical_id is not None:
            return ('id', self.canonical_id)
        if self.status == 'ambiguous':
            return (('ambiguous_id', self.raw_id) if self.raw_id not in (None, '')
                    else ('ambiguous_name', self.display_name))
        return ('name', self.display_name)


@dataclass(frozen=True, slots=True, init=False)
class IdentityResolver:
    _aliases: object

    def __init__(self, aliases: tuple[Alias, ...] = ()) -> None:
        if (not isinstance(aliases, tuple) or len(aliases) > MAX_ALIASES
                or not all(isinstance(a, Alias) for a in aliases)):
            raise DatasetInputError('input is invalid')
        grouped: dict[tuple[str, str], list[Alias]] = {}
        labels: dict[str, str] = {}
        seen = set()
        for alias in aliases:
            key = (alias.kind, name_key(alias.raw_alias) if alias.kind == 'name'
                   else alias.raw_alias)
            duplicate = (*key, alias.inventor_id)
            if duplicate in seen:
                raise DatasetInputError('input is invalid')
            seen.add(duplicate)
            if labels.setdefault(alias.inventor_id, alias.display_name) != alias.display_name:
                raise DatasetInputError('input is invalid')
            grouped.setdefault(key, []).append(alias)
        if len(labels) > MAX_IDENTITIES:
            raise DatasetInputError('input is invalid')
        for canonical_id in labels:
            if any(a.inventor_id != canonical_id
                   for a in grouped.get(('id', canonical_id), ())):
                raise DatasetInputError('input is invalid')
        for rows in grouped.values():
            if any(a.status == 'confirmed' for a in rows) and len(rows) != 1:
                raise DatasetInputError('input is invalid')
        object.__setattr__(self, '_aliases', MappingProxyType({
            k: tuple(sorted(v, key=lambda a: a.inventor_id)) for k, v in grouped.items()
        }))

    def resolve(self, *, inventor_id: str | None = None,
                name: str | None = None) -> InventorIdentity | None:
        if ((inventor_id is not None and not text_ok(inventor_id, empty=True))
                or (name is not None and not text_ok(name, empty=True))):
            raise DatasetInputError('input is invalid')
        supplied = inventor_id not in (None, '')
        label = name_key(name or '')
        if not supplied and not label:
            return None
        lookup = ('id', inventor_id) if supplied else ('name', label)
        rows = self._aliases.get(lookup, ())
        sources = tuple(sorted({s for a in rows for s in a.source_ids}))
        if rows and len(rows) == 1 and rows[0].status == 'confirmed':
            alias = rows[0]
            return InventorIdentity(alias.inventor_id, alias.display_name, 'curated_mapping',
                                    inventor_id, name, source_ids=sources)
        if rows:
            return InventorIdentity(None, str(inventor_id) if supplied else label, 'ambiguous',
                                    inventor_id, name, tuple(a.inventor_id for a in rows), sources,
                                    ('unresolved_alias_not_confirmed',))
        return InventorIdentity(inventor_id if supplied else None,
                                label or str(inventor_id),
                                'provided_id' if supplied else 'normalized_name_only',
                                inventor_id, name, caveats=() if supplied else
                                ('name_match_is_not_person_confirmation',))
