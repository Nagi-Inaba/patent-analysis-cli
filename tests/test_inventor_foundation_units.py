from dataclasses import FrozenInstanceError, replace
from fractions import Fraction

import pytest

from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_identity import IdentityResolver
from patent_analysis.inventor_models import PatentObservation, parse_observation_date
from patent_analysis.inventor_units import aggregate_contributions, form_units


def obs(record, people, **kwargs):
    resolver = IdentityResolver()
    return PatentObservation(record, tuple(resolver.resolve(inventor_id=p) for p in people),
                             parse_observation_date('2024', kind='filing'), **kwargs)


def test_family_counts_once_real_pairs_only_and_conservation():
    observations = (obs('r1', ('A', 'B', 'B'), family_id='f1'),
                    obs('r2', ('B', 'C'), family_id='f1'),
                    obs('r3', ('D',), family_id='f2'),
                    obs('r4', (), family_id='f3'))
    units = form_units(observations, unit='family')
    assert units[0].inventor_keys == (('id', 'A'), ('id', 'B'), ('id', 'C'))
    assert units[0].observed_pairs == ((('id', 'A'), ('id', 'B')),
                                      (('id', 'B'), ('id', 'C')))
    assert units[0].pair_evidence == (
        ((('id', 'A'), ('id', 'B')), ('r1',)),
        ((('id', 'B'), ('id', 'C')), ('r2',)))
    full = aggregate_contributions(units)
    assert dict(full.people) == {('id', p): Fraction(1) for p in 'ABCD'}
    fractional = aggregate_contributions(units, person_weight='fractional',
                                        pair_weight='unit_pair_fractional')
    assert sum(v for _, v in fractional.people) == 2
    assert sum(v for _, v in fractional.pairs) == 1
    assert dict(fractional.people)[('id', 'B')] == Fraction(1, 3)
    assert fractional.person_denominator_units == 2
    assert fractional.pair_denominator_units == 1
    assert fractional.missing_inventor_units == 1
    with pytest.raises(FrozenInstanceError):
        units[0].unit_id = 'fake'
    three = form_units((obs('r', ('A', 'B', 'C')),), unit='records')
    assert set(v for _, v in aggregate_contributions(
        three, pair_weight='unit_pair_fractional').pairs) == {Fraction(1, 3)}


@pytest.mark.parametrize('unit', ['records', 'publication', 'application', 'family'])
def test_strict_unit_ids_duplicates_and_conflicts(unit):
    field = {'records': 'record_id', 'publication': 'publication_id',
             'application': 'application_id', 'family': 'family_id'}[unit]
    o = obs('r', ('A',), publication_id='p', application_id='US:a', family_id='f')
    units = form_units((o, o), unit=unit)
    assert len(units) == 1
    assert units[0].observation_ids == ('r',)
    with pytest.raises(DatasetInputError):
        form_units((o, replace(o, inventors=obs('x', ('B',)).inventors)), unit=unit)
    if field != 'record_id':
        with pytest.raises(DatasetInputError):
            form_units((replace(o, **{field: None}),), unit=unit)
    with pytest.raises(DatasetInputError):
        form_units((o,), unit=unit, family_mode='earliest')


@pytest.mark.parametrize('field', ['record_id', 'publication_id', 'application_id', 'family_id'])
def test_patent_unit_ids_must_not_be_empty_or_whitespace_only(field):
    original = obs('r', ('A',), publication_id='p', application_id='a', family_id='f')
    for value in ('', '   ', '\u3000'):
        with pytest.raises(DatasetInputError):
            replace(original, **{field: value})


def test_publication_conflicts_are_not_hidden_in_application_or_family():
    a = obs('r1', ('A',), publication_id='p', application_id='a', family_id='f')
    b = obs('r2', ('B',), publication_id='p', application_id='a', family_id='f')
    for unit in ('publication', 'application', 'family'):
        with pytest.raises(DatasetInputError):
            form_units((a, b), unit=unit)
    equivalent = replace(a, record_id='r3')
    assert form_units((a, equivalent), unit='publication')[0].observation_ids == ('r1', 'r3')


def test_row_and_value_reordering_semantics_and_pair_evidence():
    a = obs('r1', ('A', 'B'), application_id='a')
    b = obs('r2', ('B', 'C'), application_id='a')
    original = form_units((a, b), unit='application')
    reordered = form_units((replace(b, inventors=b.inventors[::-1]),
                            replace(a, inventors=a.inventors[::-1])), unit='application')
    assert original == reordered
    assert aggregate_contributions(original) == aggregate_contributions(reordered)


def test_unit_constructor_cannot_add_unwitnessed_pairs_or_mutable_members():
    unit = form_units((obs('r1', ('A', 'B')),), unit='records')[0]
    for changes in ({'inventor_keys': list(unit.inventor_keys)},
                    {'inventor_keys': unit.inventor_keys * 2},
                    {'observed_pairs': ((('id', 'A'), ('id', 'C')),)},
                    {'pair_evidence': ((unit.observed_pairs[0], ('unknown',)),)}):
        with pytest.raises(DatasetInputError):
            replace(unit, **changes)


def test_expansion_budget_is_checked_before_pair_enumeration(monkeypatch):
    import patent_analysis.inventor_units as module

    monkeypatch.setattr(module, 'MAX_PAIR_EXPANSIONS', 2)
    with pytest.raises(DatasetInputError):
        form_units((obs('r', ('A', 'B', 'C')),), unit='records')
