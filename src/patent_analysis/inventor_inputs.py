"""Dedicated raw-ID/day-precision preparation; existing earliest is never applied."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from patent_analysis.canonical_v2 import (
    CanonicalizationError,
    canonical_sha256,
    parse_strict_json_bytes,
)
from patent_analysis.column_resolution import resolve_roles
from patent_analysis.dataset_v2 import DatasetV2, read_dataset_v2
from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_identity import IdentityResolver, text_ok
from patent_analysis.inventor_models import PatentObservation, parse_observation_date
from patent_analysis.normalization import (
    NormalizationReceipt,
    NormalizedDataset,
    NormalizedRow,
    derive_classification_values,
    split_patent_values,
)
from patent_analysis.population import PopulationError, PopulationReceipt, apply_population

MAX_OBSERVATIONS = 5000
MAX_VALUES = 64
_ROLES = frozenset({'record_id', 'inventor_ids', 'inventor_names', 'date', 'publication_id',
                    'application_id', 'family_id', 'classification', 'applicant_ids', 'source_ids'})


def string_array(raw: str) -> tuple[str, ...]:
    """IDs are JSON arrays in a cell, never delimiter-split/trimmed/inferred."""
    if raw == '':
        return ()
    try:
        values = parse_strict_json_bytes(raw.encode('utf-8'))
    except (CanonicalizationError, UnicodeError):
        raise DatasetInputError('input is invalid') from None
    if (not isinstance(values, list) or len(values) > MAX_VALUES
            or not all(text_ok(v) for v in values)):
        raise DatasetInputError('input is invalid')
    return tuple(values)


@dataclass(frozen=True, slots=True)
class PreparedInventorInputs:
    dataset: DatasetV2
    observations: tuple[PatentObservation, ...]
    coverage: tuple[tuple[str, int], ...]
    population_receipt: PopulationReceipt


def prepare_inventor_inputs(
    source: str | Path, *, allowed_root: str | Path, bindings: Mapping[str, str],
    resolver: IdentityResolver | None = None, date_kind: str = 'filing',
    classification_scheme: str = 'IPC', classification_level: str = 'full',
    population: Mapping[str, object] | None = None,
) -> PreparedInventorInputs:
    """Explicit column bindings; core population filters operate on prepared identity values.

    inventor_ids/applicant_ids/source_ids cells contain JSON string arrays. Names use
    existing patent-name delimiters only in name-only mode. No positional ID/name pairing.
    """
    dataset = read_dataset_v2(source, allowed_root=allowed_root)
    return prepare_inventor_dataset(
        dataset, bindings=bindings, resolver=resolver, date_kind=date_kind,
        classification_scheme=classification_scheme,
        classification_level=classification_level, population=population)


def prepare_inventor_dataset(
    dataset: DatasetV2, *, bindings: Mapping[str, str],
    resolver: IdentityResolver | None = None, date_kind: str = 'filing',
    classification_scheme: str = 'IPC', classification_level: str = 'full',
    population: Mapping[str, object] | None = None,
) -> PreparedInventorInputs:
    """Prepare an already verified immutable dataset; never re-open patent input."""
    pop = {'family_mode': 'records', 'filters': []} if population is None else population
    if (not isinstance(bindings, Mapping) or not set(bindings) <= _ROLES
            or 'record_id' not in bindings
            or not {'inventor_ids', 'inventor_names'} & set(bindings)
            or {'inventor_ids', 'inventor_names'} <= set(bindings)
            or not isinstance(pop, Mapping) or pop.get('family_mode') != 'records'
            or not text_ok(classification_scheme)):
        raise DatasetInputError('input is invalid')
    resolver = resolver or IdentityResolver()
    if not isinstance(dataset, DatasetV2) or len(dataset.rows) > MAX_OBSERVATIONS:
        raise DatasetInputError('input is invalid')
    try:
        resolution = resolve_roles(dataset.manifest, {'bindings': dict(bindings)},
                                   required_roles=tuple(bindings))
    except ValueError:
        raise DatasetInputError('input is invalid') from None
    ordinals = {role: b.source_header_ordinal for role, b in resolution.mapping.items()}
    observations = []
    normalized_rows = []
    roles = ('inventor_id', 'inventor_name', 'year', 'record_id', 'publication_id',
             'application_id', 'family_id', 'applicant_id', 'classification')
    for row in dataset.rows:
        raw = {role: row.values[index] for role, index in ordinals.items()}
        try:
            if 'inventor_ids' in raw:
                people = tuple(resolver.resolve(inventor_id=v)
                               for v in string_array(raw['inventor_ids']))
            else:
                names = split_patent_values(raw['inventor_names'], role='inventor')
                if len(names) > MAX_VALUES:
                    raise DatasetInputError('input is invalid')
                people = tuple(resolver.resolve(name=v) for v in names)
            codes = derive_classification_values(
                split_patent_values(raw.get('classification', ''), role='classification'),
                level=classification_level)
            observation = PatentObservation(
                record_id=raw['record_id'], inventors=tuple(p for p in people if p is not None),
                observed_date=parse_observation_date(raw.get('date'), kind=date_kind),
                publication_id=raw.get('publication_id') or None,
                application_id=raw.get('application_id') or None,
                family_id=raw.get('family_id') or None,
                classifications=tuple((classification_scheme, code) for code in codes),
                applicant_ids=string_array(raw.get('applicant_ids', '')),
                source_ids=string_array(raw.get('source_ids', '')),
                source_ordinal=row.source_ordinal, source_fields=row.values)
        except ValueError:
            raise DatasetInputError('input is invalid') from None
        observations.append(observation)
        values = {
            'inventor_id': tuple(sorted({p.canonical_id for p in observation.inventors
                                         if p.canonical_id is not None})),
            'inventor_name': tuple(sorted({p.display_name for p in observation.inventors})),
            'year': () if observation.observed_date.start is None else
                    (str(observation.observed_date.start.year).zfill(4),),
            'applicant_id': observation.applicant_ids,
            'classification': tuple(code for _, code in observation.classifications),
        }
        for role in ('record_id', 'publication_id', 'application_id', 'family_id'):
            value = getattr(observation, role)
            values[role] = () if value is None else (value,)
        normalized_rows.append(NormalizedRow(row.source_ordinal, row.values, values))
    # Reuse the closed population validator and filtering semantics, bypassing only
    # generic ID trimming and year-only date normalization. Receipt is foundation-specific.
    receipt = NormalizationReceipt(
        'inventor-foundation.1', dataset.manifest.source_input_sha256,
        resolution.receipt.resolved_role_mapping_sha256, roles, 'all', {},
        len(observations), len(observations),
        sum(len(v) for r in normalized_rows for v in r.values_by_role.values()),
        canonical_sha256([r.to_dict() for r in normalized_rows]))
    try:
        selected = apply_population(NormalizedDataset(tuple(normalized_rows), receipt), pop)
    except PopulationError:
        raise DatasetInputError('input is invalid') from None
    included = {r.source_ordinal for r in selected.rows}
    kept = tuple(sorted((o for o in observations if o.source_ordinal in included),
                        key=lambda o: o.record_id))
    coverage = (('input_rows', len(observations)), ('included_rows', len(kept)),
                ('filtered_rows', len(observations) - len(kept)),
                ('missing_inventors', sum(not o.inventors for o in kept)),
                ('missing_date', sum(o.observed_date.precision == 'missing' for o in kept)),
                ('missing_applicants', sum(not o.applicant_ids for o in kept)),
                ('missing_classification', sum(not o.classifications for o in kept)))
    return PreparedInventorInputs(dataset, kept, coverage, selected.receipt)
