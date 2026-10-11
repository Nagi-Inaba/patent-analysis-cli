"""Deterministic explicit patent units, witnessed pairs, exact contribution allocation."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations

from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_identity import MAX_IDENTITIES, PersonKey, text_ok
from patent_analysis.inventor_inputs import MAX_OBSERVATIONS
from patent_analysis.inventor_models import PatentObservation

MAX_UNITS = 5000
MAX_PAIR_EXPANSIONS = 50000
PairKey = tuple[PersonKey, PersonKey]
_UNIT_FIELDS = {'records': 'record_id', 'publication': 'publication_id',
                'application': 'application_id', 'family': 'family_id'}


@dataclass(frozen=True, slots=True)
class InventorUnit:
    unit: str
    unit_id: str
    observation_ids: tuple[str, ...]
    inventor_keys: tuple[PersonKey, ...]
    observed_pairs: tuple[PairKey, ...]
    pair_evidence: tuple[tuple[PairKey, tuple[str, ...]], ...]
    classifications: tuple[tuple[str, str], ...]
    applicant_ids: tuple[str, ...]
    source_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        def person_ok(key: object) -> bool:
            return (isinstance(key, tuple) and len(key) == 2
                    and key[0] in {'id', 'name', 'ambiguous_id', 'ambiguous_name'}
                    and text_ok(key[1]))

        if (self.unit not in _UNIT_FIELDS or not text_ok(self.unit_id)
                or not isinstance(self.inventor_keys, tuple)
                or not all(person_ok(p) for p in self.inventor_keys)
                or tuple(sorted(set(self.inventor_keys))) != self.inventor_keys
                or any(not isinstance(v, tuple) or not all(text_ok(s) for s in v)
                       or tuple(sorted(set(v))) != v
                       for v in (self.observation_ids, self.applicant_ids, self.source_ids))
                or not self.observation_ids
                or not isinstance(self.classifications, tuple)
                or any(not isinstance(c, tuple) or len(c) != 2 or not all(text_ok(s) for s in c)
                       for c in self.classifications)
                or not isinstance(self.observed_pairs, tuple)
                or any(not isinstance(p, tuple) or len(p) != 2 or not all(person_ok(k) for k in p)
                       or p[0] >= p[1] or not set(p) <= set(self.inventor_keys)
                       for p in self.observed_pairs)
                or tuple(sorted(set(self.observed_pairs))) != self.observed_pairs
                or not isinstance(self.pair_evidence, tuple)
                or len(self.pair_evidence) != len(self.observed_pairs)):
            raise DatasetInputError('input is invalid')
        for pair, evidence in zip(self.observed_pairs, self.pair_evidence, strict=True):
            if (not isinstance(evidence, tuple) or len(evidence) != 2 or evidence[0] != pair
                    or not isinstance(evidence[1], tuple) or not evidence[1]
                    or not all(text_ok(s) for s in evidence[1])
                    or tuple(sorted(set(evidence[1]))) != evidence[1]
                    or not set(evidence[1]) <= set(self.observation_ids)):
                raise DatasetInputError('input is invalid')


@dataclass(frozen=True, slots=True)
class Contributions:
    people: tuple[tuple[PersonKey, Fraction], ...]
    pairs: tuple[tuple[PairKey, Fraction], ...]
    unit_count: int
    person_denominator_units: int
    pair_denominator_units: int
    missing_inventor_units: int
    person_weight: str
    pair_weight: str


def form_units(observations: tuple[PatentObservation, ...], *, unit: str,
               family_mode: str = 'records') -> tuple[InventorUnit, ...]:
    """Reject conflicts rather than silently selecting a representative publication.

    Observations remain in PreparedInventorInputs. Unit evidence names explicit record IDs,
    never row positions; pairs come only from within one observation.
    """
    if (unit not in _UNIT_FIELDS or family_mode != 'records'
            or not isinstance(observations, tuple) or len(observations) > MAX_OBSERVATIONS
            or not all(isinstance(o, PatentObservation) for o in observations)):
        raise DatasetInputError('input is invalid')
    records: dict[str, PatentObservation] = {}
    publications: dict[str, tuple] = {}
    groups: dict[str, list[PatentObservation]] = defaultdict(list)
    all_people = set()
    expansions = 0
    for observation in observations:
        identifier = getattr(observation, _UNIT_FIELDS[unit])
        if identifier is None:
            raise DatasetInputError('input is invalid')
        previous = records.get(observation.record_id)
        if previous is not None:
            if previous.semantic_key() != observation.semantic_key():
                raise DatasetInputError('input is invalid')
            continue
        records[observation.record_id] = observation
        if observation.publication_id is not None:
            signature = observation.semantic_key()
            old = publications.setdefault(observation.publication_id, signature)
            if old != signature:
                raise DatasetInputError('input is invalid')
        people = observation.inventor_keys
        all_people.update(people)
        expansions += len(people) * (len(people) - 1) // 2
        if len(all_people) > MAX_IDENTITIES or expansions > MAX_PAIR_EXPANSIONS:
            raise DatasetInputError('input is invalid')
        groups[identifier].append(observation)
        if len(groups) > MAX_UNITS:
            raise DatasetInputError('input is invalid')
    result = []
    for identifier, rows in sorted(groups.items()):
        evidence: dict[PairKey, set[str]] = defaultdict(set)
        for row in rows:
            for pair in combinations(row.inventor_keys, 2):
                evidence[pair].add(row.record_id)
        result.append(InventorUnit(
            unit, identifier, tuple(sorted(r.record_id for r in rows)),
            tuple(sorted({p for r in rows for p in r.inventor_keys})),
            tuple(sorted(evidence)), tuple((p, tuple(sorted(ids)))
                                           for p, ids in sorted(evidence.items())),
            tuple(sorted({c for r in rows for c in r.classifications})),
            tuple(sorted({a for r in rows for a in r.applicant_ids})),
            tuple(sorted({s for r in rows for s in r.source_ids}))))
    return tuple(result)


def aggregate_contributions(units: tuple[InventorUnit, ...], *, person_weight: str = 'full',
                            pair_weight: str = 'joint_unit_count') -> Contributions:
    if (not isinstance(units, tuple) or len(units) > MAX_UNITS
            or not all(isinstance(u, InventorUnit) for u in units)
            or len({(u.unit, u.unit_id) for u in units}) != len(units)
            or len({u.unit for u in units}) > 1
            or person_weight not in {'full', 'fractional'}
            or pair_weight not in {'joint_unit_count', 'unit_pair_fractional'}):
        raise DatasetInputError('input is invalid')
    people: dict[PersonKey, Fraction] = defaultdict(Fraction)
    pairs: dict[PairKey, Fraction] = defaultdict(Fraction)
    for unit in units:
        for person in unit.inventor_keys:
            people[person] += (Fraction(1) if person_weight == 'full'
                               else Fraction(1, len(unit.inventor_keys)))
        for pair in unit.observed_pairs:
            pairs[pair] += (Fraction(1) if pair_weight == 'joint_unit_count'
                           else Fraction(1, len(unit.observed_pairs)))
    person_units = sum(bool(u.inventor_keys) for u in units)
    return Contributions(tuple(sorted(people.items())), tuple(sorted(pairs.items())),
                         len(units), person_units, sum(bool(u.observed_pairs) for u in units),
                         len(units) - person_units, person_weight, pair_weight)
