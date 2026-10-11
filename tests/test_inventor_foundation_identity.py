from dataclasses import FrozenInstanceError

import pytest

from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_identity import Alias, IdentityResolver


def test_opaque_ids_and_name_only_caveat():
    resolver = IdentityResolver()
    for raw in (' Ａ ', 'A', 'a', ' A ', ' '):
        person = resolver.resolve(inventor_id=raw, name=' Ａlice ')
        assert person.canonical_id == raw
        assert person.raw_id == raw
        assert person.status == 'provided_id'
        assert person.display_name == 'Alice'
    name = resolver.resolve(name=' Ａlice ')
    assert name.key == ('name', 'Alice')
    assert name.status == 'normalized_name_only'
    assert name.caveats == ('name_match_is_not_person_confirmation',)
    assert resolver.resolve() is None
    with pytest.raises(FrozenInstanceError):
        name.status = 'confirmed'


def test_identity_cannot_be_forged_or_canonical_id_remapped():
    from patent_analysis.inventor_identity import InventorIdentity

    with pytest.raises(DatasetInputError):
        InventorIdentity('A', 'Alice', 'provided_id', 'B', None)
    with pytest.raises(DatasetInputError):
        InventorIdentity(None, 'Alice', 'ambiguous', None, 'Alice', ['A'], ['s1'])
    with pytest.raises(DatasetInputError):
        IdentityResolver((Alias('id', 'A', 'B', 'Bob', ('s1',)),
                          Alias('id', 'B', 'C', 'Carol', ('s1',))))
    resolver = IdentityResolver((Alias('id', 'Bob', 'A', 'Alice', ('s1',), 'candidate'),
                                 Alias('name', 'Bob', 'B', 'Bob', ('s1',), 'candidate')))
    assert resolver.resolve(inventor_id='Bob').key != resolver.resolve(name='Bob').key


def test_curated_aliases_ambiguity_and_contradictions():
    resolver = IdentityResolver((
        Alias('id', ' Ａ ', 'person-1', 'Alice', ('s1',)),
        Alias('name', 'Bob', 'p2', 'Bob 2', ('s2',), 'candidate'),
        Alias('name', 'Bob', 'p3', 'Bob 3', ('s3',), 'candidate'),
    ))
    person = resolver.resolve(inventor_id=' Ａ ')
    assert (person.canonical_id, person.raw_id, person.source_ids) == (
        'person-1', ' Ａ ', ('s1',))
    assert person.status == 'curated_mapping'
    assert resolver.resolve(inventor_id='A').canonical_id == 'A'
    ambiguous = resolver.resolve(name=' Bob ')
    assert ambiguous.status == 'ambiguous'
    assert ambiguous.canonical_id is None
    assert ambiguous.candidate_ids == ('p2', 'p3')
    row = Alias('name', 'Alice', 'p1', 'Alice', ('s1',))
    for aliases in ((row, row), (row, Alias('name', 'Ａlice', 'p2', 'Alice', ('s2',)))):
        with pytest.raises(DatasetInputError, match='input is invalid'):
            IdentityResolver(aliases)
    with pytest.raises(DatasetInputError):
        IdentityResolver((Alias('id', 'x', 'p', 'A', ()),))
