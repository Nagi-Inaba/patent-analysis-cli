"""Local strict sidecar bundle/CSV tables with immutable verified-byte snapshots."""

from __future__ import annotations

import csv
import hashlib
import io
import ntpath
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from importlib.resources import files
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType

from jsonschema import Draft202012Validator

from patent_analysis.access import read_verified_bytes
from patent_analysis.canonical_v2 import CanonicalizationError, parse_strict_json_bytes
from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_identity import Alias, IdentityResolver, name_key, text_ok
from patent_analysis.inventor_inputs import string_array
from patent_analysis.inventor_models import PatentObservation, parse_observation_date

SIDECAR_VERSION = '1.0.0'
MAX_SIDECAR_BYTES = 1024 * 1024  # total per bundle or all CSV files together
MAX_SIDECAR_ROWS = 5000  # total, not per table
MAX_SIDECAR_DEPTH = 12
MAX_SIDECAR_NODES = 100000
MAX_CSV_FIELD = 16384
MAX_TEMPORAL_OPERATIONS = 200000
TABLE_IDS = MappingProxyType({
    'sources': 'source_id', 'identities': 'alias_id', 'entities': 'entity_id',
    'entity_aliases': 'alias_id', 'groups': 'group_id', 'events': 'event_id',
    'personal_evidence': 'evidence_id', 'reviews': 'review_id', 'citations': 'citation_id',
})
_ARRAY_FIELDS = frozenset({'source_ids', 'entity_ids', 'record_ids', 'evidence_ids', 'event_ids',
                            'citing_ids'})
_DATE_KINDS = {'checked_date': 'checked', 'valid_from': 'valid_from', 'valid_to': 'valid_to',
               'announcement_date': 'announcement', 'effective_date': 'effective',
               'reviewed_date': 'checked', 'snapshot_date': 'citation_snapshot'}


def sidecar_schema() -> dict:
    """A fresh schema copy for internal callers; no remote resolver or network."""
    raw = files('patent_analysis').joinpath('schemas', 'inventor-sidecar-v1.schema.json')
    return parse_strict_json_bytes(raw.read_bytes())


def _invalid() -> None:
    raise DatasetInputError('input is invalid')


def _relative(value: object) -> str:
    if not isinstance(value, str) or not value or '\x00' in value:
        raise DatasetInputError('input path is not permitted')
    posix = PurePosixPath(value.replace('\\', '/'))
    windows = PureWindowsPath(value)
    if (posix.is_absolute() or windows.is_absolute() or ntpath.splitdrive(value)[0]
            or ':' in value or '..' in posix.parts or '..' in windows.parts):
        raise DatasetInputError('input path is not permitted')
    return value


def _bounded_structure(document: object) -> None:
    stack = [(document, 1)]
    nodes = 0
    while stack:
        value, depth = stack.pop()
        nodes += 1
        if depth > MAX_SIDECAR_DEPTH or nodes > MAX_SIDECAR_NODES:
            _invalid()
        if isinstance(value, dict):
            stack.extend((v, depth + 1) for v in value.values())
        elif isinstance(value, list):
            stack.extend((v, depth + 1) for v in value)


def _parse(raw: bytes, *, allow_bom: bool = False) -> object:
    try:
        document = parse_strict_json_bytes(raw, allow_bom=allow_bom)
    except CanonicalizationError:
        raise DatasetInputError('input is invalid') from None
    _bounded_structure(document)
    return document


def _freeze(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


@dataclass(frozen=True, slots=True)
class SidecarReceipt:
    table: str
    format: str
    schema_version: str
    byte_size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class SidecarSnapshot:
    version: str
    tables: Mapping[str, tuple[Mapping[str, object], ...]]
    receipts: tuple[SidecarReceipt, ...]
    raw_snapshots: tuple[tuple[str, bytes], ...]

    def identity_resolver(self) -> IdentityResolver:
        return IdentityResolver(tuple(Alias(
            r['kind'], r['raw_alias'], r['inventor_id'], r['display_name'],
            tuple(r['source_ids']), r['status']) for r in self.tables['identities']))

    def group_parents(self, entity_id: str, *, on: str) -> tuple[str, ...]:
        """Explicit controlling relationships only; never employment or current backfill."""
        day = parse_observation_date(on, kind='observation')
        if day.precision != 'day' or entity_id not in {
                r['entity_id'] for r in self.tables['entities']}:
            _invalid()
        return tuple(sorted({r['parent_id'] for r in self.tables['groups']
                             if r['child_id'] == entity_id and r['relation'] != 'minority_interest'
                             and _interval(r)[0] <= day.start <= _interval(r)[1]}))


def _interval(row: Mapping) -> tuple[date, date]:
    start = parse_observation_date(row['valid_from'], kind='valid_from').start or date.min
    end = parse_observation_date(row['valid_to'], kind='valid_to').end or date.max
    if start > end:
        _invalid()
    return start, end


def _check_chains(links: dict[str, str]) -> None:
    finished = set()
    for origin in links:
        chain = set()
        node = origin
        while node in links and node not in finished:
            if node in chain:
                _invalid()
            chain.add(node)
            node = links[node]
        finished.update(chain)


def _validate_history(tables: dict) -> None:
    groups = [(r, _interval(r)) for r in tables['groups']]
    aliases = [(r, _interval(r)) for r in tables['entity_aliases']]
    if len(groups) ** 2 + len(aliases) ** 2 > MAX_TEMPORAL_OPERATIONS:
        _invalid()
    for row, _ in groups:
        if row['child_id'] == row['parent_id']:
            _invalid()
    for index, (row, bounds) in enumerate(aliases):
        key = name_key(row['raw_alias'])
        if not key:
            _invalid()
        for other, other_bounds in aliases[index + 1:]:
            if (key == name_key(other['raw_alias'])
                    and max(bounds[0], other_bounds[0]) <= min(bounds[1], other_bounds[1])):
                _invalid()
    controlling = [(r, bounds) for r, bounds in groups if r['relation'] != 'minority_interest']
    # An active graph can change only when an interval starts/ends. A new cycle
    # must first appear at some start; closed endpoints also catch same-day overlap.
    for day in sorted({bounds[0] for _, bounds in controlling}):
        links = {}
        for row, bounds in controlling:
            if bounds[0] <= day <= bounds[1]:
                if row['child_id'] in links:
                    _invalid()
                links[row['child_id']] = row['parent_id']
        _check_chains(links)
    evidence = {r['evidence_id']: r for r in tables['personal_evidence']}
    for row in evidence.values():
        _interval(row)
        if row['from_entity_id'] is None and row['to_entity_id'] is None:
            _invalid()
    reviews = {r['review_id']: r for r in tables['reviews']}
    links = {}
    for row in reviews.values():
        if any(evidence[e]['inventor_id'] != row['inventor_id'] for e in row['evidence_ids']):
            _invalid()
        predecessor = row['supersedes_review_id']
        if predecessor is not None:
            other = reviews[predecessor]
            if (other['inventor_id'], other['claim']) != (row['inventor_id'], row['claim']):
                _invalid()
            links[row['review_id']] = predecessor
    _check_chains(links)


def _validate(document: object, *, inventor_ids: tuple[str, ...],
              record_ids: tuple[str, ...]) -> dict:
    _bounded_structure(document)
    validator = Draft202012Validator(sidecar_schema())
    if next(validator.iter_errors(document), None) is not None:
        _invalid()
    tables = document['tables']
    if sum(len(rows) for rows in tables.values()) > MAX_SIDECAR_ROWS:
        _invalid()
    registries = {}
    for table, key in TABLE_IDS.items():
        ids = [r[key] for r in tables[table]]
        if len(ids) != len(set(ids)):
            _invalid()
        registries[table] = set(ids)
    if (not isinstance(inventor_ids, tuple) or not isinstance(record_ids, tuple)
            or not all(text_ok(v) for v in (*inventor_ids, *record_ids))):
        _invalid()
    inventors = set(inventor_ids) | {r['inventor_id'] for r in tables['identities']}
    entities = registries['entities']
    if len(inventors) > 1000 or len(entities) > 1000:
        _invalid()
    refs = {'source_ids': registries['sources'], 'entity_ids': entities,
            'record_ids': set(record_ids), 'evidence_ids': registries['personal_evidence'],
            'event_ids': registries['events'], 'citing_ids': None}
    scalar_refs = {'entity_id': entities, 'child_id': entities, 'parent_id': entities,
                   'from_entity_id': entities, 'to_entity_id': entities,
                   'inventor_id': inventors, 'record_id': set(record_ids),
                   'supersedes_review_id': registries['reviews']}
    for table, rows in tables.items():
        for row in rows:
            for field, value in row.items():
                # Python regex '$' also matches before a final newline. Enforce
                # the complete literal text, including reference-array values.
                if isinstance(value, str) and not text_ok(value):
                    _invalid()
                if isinstance(value, list) and not all(text_ok(v) for v in value):
                    _invalid()
                if field in _DATE_KINDS:
                    parse_observation_date(value, kind=_DATE_KINDS[field])
                if field in refs and value is not None and refs[field] is not None:
                    if not set(value) <= refs[field]:
                        _invalid()
                # Declaration IDs are checked for duplicates above, not as references.
                if (field in scalar_refs and value is not None
                        and not (table == 'entities' and field == 'entity_id')
                        and value not in scalar_refs[field]):
                    _invalid()
            if table == 'citations':
                if row['count'] is not None and type(row['count']) is not int:
                    _invalid()
                if row['citing_ids'] is not None and row['count'] != len(row['citing_ids']):
                    _invalid()
    IdentityResolver(tuple(Alias(r['kind'], r['raw_alias'], r['inventor_id'],
                                 r['display_name'], tuple(r['source_ids']), r['status'])
                           for r in tables['identities']))
    _validate_history(tables)
    return tables


def _snapshot(document: object, raw: tuple[tuple[str, bytes], ...], *, format: str,
              inventor_ids: tuple[str, ...], record_ids: tuple[str, ...]) -> SidecarSnapshot:
    tables = _validate(document, inventor_ids=inventor_ids, record_ids=record_ids)
    ordered = {}
    for table, key in TABLE_IDS.items():
        rows = []
        for row in sorted(tables[table], key=lambda r: r[key]):
            # References are sets semantically; raw bytes retain supplied order.
            rows.append({k: sorted(v) if k in _ARRAY_FIELDS and v is not None else v
                         for k, v in row.items()})
        ordered[table] = rows
    receipts = tuple(SidecarReceipt(table, format, SIDECAR_VERSION, len(content),
                                    hashlib.sha256(content).hexdigest())
                     for table, content in raw)
    return SidecarSnapshot(SIDECAR_VERSION, _freeze(ordered), receipts, raw)


def read_inventor_sidecar(source: str | Path, *, allowed_root: str | Path,
                          inventor_ids: tuple[str, ...] = (),
                          record_ids: tuple[str, ...] = ()) -> SidecarSnapshot:
    path = _relative(str(source))
    raw = read_verified_bytes(path, allowed_root=allowed_root, max_bytes=MAX_SIDECAR_BYTES)
    return _snapshot(_parse(raw, allow_bom=True), (('bundle', raw),), format='json',
                     inventor_ids=inventor_ids, record_ids=record_ids)


def validate_observation_references(snapshot: SidecarSnapshot,
                                    observations: tuple[PatentObservation, ...], *,
                                    inventor_ids: tuple[str, ...] = ()) -> None:
    """Explicit join gate before aggregation when sidecar registries are supplied.

    Name-only/unresolved people are retained, not promoted to registered inventor IDs.
    Missing sidecar is a caller-visible input-not-provided state, not an empty registry.
    """
    if (not isinstance(snapshot, SidecarSnapshot) or not isinstance(observations, tuple)
            or not all(isinstance(o, PatentObservation) for o in observations)
            or not isinstance(inventor_ids, tuple) or not all(text_ok(v) for v in inventor_ids)):
        _invalid()
    sources = {r['source_id'] for r in snapshot.tables['sources']}
    entities = {r['entity_id'] for r in snapshot.tables['entities']}
    people = set(inventor_ids) | {r['inventor_id'] for r in snapshot.tables['identities']}
    for observation in observations:
        if (not set(observation.source_ids) <= sources
                or not set(observation.applicant_ids) <= entities
                or any(not set(p.source_ids) <= sources
                       or (p.canonical_id is not None and p.canonical_id not in people)
                       for p in observation.inventors)):
            _invalid()


def _csv_rows(raw: bytes, table: str, schema: dict) -> list[dict]:
    properties = schema['$defs'][table]['items']['properties']
    failed = False
    try:
        text = raw.decode('utf-8-sig')
        reader = csv.reader(io.StringIO(text, newline=''), strict=True)
        header = next(reader)
        if len(header) != len(set(header)) or set(header) != set(properties):
            _invalid()
        rows = []
        for values in reader:
            if (len(rows) >= MAX_SIDECAR_ROWS or len(values) != len(header)
                    or any(len(v) > MAX_CSV_FIELD for v in values)):
                _invalid()
            row = {}
            for key, value in zip(header, values, strict=True):
                definition = properties[key]
                if key in _ARRAY_FIELDS:
                    if value == '' and key != 'citing_ids':
                        _invalid()
                    row[key] = (None if key == 'citing_ids' and value == ''
                                else list(string_array(value)))
                elif key == 'count':
                    row[key] = None if value == '' else _parse(value.encode('utf-8'))
                elif value == '' and (key in _DATE_KINDS
                                     or definition.get('$ref') == '#/$defs/nullable_text'):
                    row[key] = None
                else:
                    row[key] = value
            rows.append(row)
        return rows
    except (UnicodeError, csv.Error, StopIteration, ValueError):
        failed = True
    if failed:
        raise DatasetInputError('input is invalid') from None
    raise AssertionError('unreachable')


def read_inventor_sidecar_csv(paths: Mapping[str, str], *, version: str,
                              allowed_root: str | Path, inventor_ids: tuple[str, ...] = (),
                              record_ids: tuple[str, ...] = ()) -> SidecarSnapshot:
    if not isinstance(paths, Mapping) or set(paths) != set(TABLE_IDS) or version != SIDECAR_VERSION:
        _invalid()
    # Validate all auxiliary paths before opening any file.
    approved = {table: _relative(paths[table]) for table in TABLE_IDS}
    raw = []
    tables = {}
    remaining = MAX_SIDECAR_BYTES
    schema = sidecar_schema()
    for table, path in approved.items():
        content = read_verified_bytes(path, allowed_root=allowed_root, max_bytes=remaining)
        remaining -= len(content)
        raw.append((table, content))
        tables[table] = _csv_rows(content, table, schema)
    return _snapshot({'version': version, 'tables': tables}, tuple(raw), format='csv',
                     inventor_ids=inventor_ids, record_ids=record_ids)
