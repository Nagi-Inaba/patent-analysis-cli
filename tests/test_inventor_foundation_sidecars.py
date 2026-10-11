import csv
import hashlib
import io
import json
from dataclasses import FrozenInstanceError

import pytest

from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_sidecars import read_inventor_sidecar, read_inventor_sidecar_csv

TABLES = ('sources', 'identities', 'entities', 'entity_aliases', 'groups', 'events',
          'personal_evidence', 'reviews', 'citations')


def bundle():
    tables = {name: [] for name in TABLES}
    tables['sources'] = [{'source_id': 's1', 'kind': 'local_document',
                          'citation': 'Synthetic source', 'checked_date': '2024-02', 'url': None}]
    tables['entities'] = [{'entity_id': e, 'display_name': e, 'source_ids': ['s1']}
                          for e in ('e1', 'e2', 'e3')]
    tables['identities'] = [{'alias_id': 'a1', 'kind': 'id', 'raw_alias': ' Ａ ',
                             'inventor_id': 'p1', 'display_name': 'Alice',
                             'source_ids': ['s1'], 'status': 'confirmed'}]
    tables['groups'] = [{'group_id': 'g1', 'child_id': 'e1', 'parent_id': 'e2',
                         'relation': 'subsidiary', 'valid_from': '2024-01-01',
                         'valid_to': '2024-12-31', 'source_ids': ['s1']}]
    tables['events'] = [{'event_id': 'ev1', 'type': 'acquisition', 'entity_ids': ['e1', 'e2'],
                         'record_ids': ['r1'], 'announcement_date': '2023',
                         'effective_date': '2024-01', 'status': 'completed',
                         'scope': 'whole_entity', 'source_ids': ['s1']}]
    return {'version': '1.0.0', 'tables': tables}


def save(tmp_path, document):
    raw = json.dumps(document, ensure_ascii=False).encode('utf-8')
    (tmp_path / 'sidecar.json').write_bytes(raw)
    return raw


def read(tmp_path):
    return read_inventor_sidecar('sidecar.json', allowed_root=tmp_path,
                                inventor_ids=('p1',), record_ids=('r1',))


def test_json_snapshot_hash_immutable_raw_references_and_no_employment_claim(tmp_path):
    raw = save(tmp_path, bundle())
    snapshot = read(tmp_path)
    assert snapshot.version == '1.0.0'
    assert snapshot.raw_snapshots == (('bundle', raw),)
    assert snapshot.receipts[0].sha256 == hashlib.sha256(raw).hexdigest()
    assert snapshot.receipts[0].byte_size == len(raw)
    assert snapshot.identity_resolver().resolve(inventor_id=' Ａ ').canonical_id == 'p1'
    assert snapshot.tables['events'][0]['type'] == 'acquisition'
    assert snapshot.tables['personal_evidence'] == ()
    assert str(tmp_path) not in repr(snapshot.receipts)
    with pytest.raises(TypeError):
        snapshot.tables['events'][0]['status'] = 'employment_confirmed'
    with pytest.raises(FrozenInstanceError):
        snapshot.version = 'other'
    (tmp_path / 'sidecar.json').write_text('{}', encoding='utf-8')
    assert snapshot.raw_snapshots == (('bundle', raw),)


def test_csv_matches_json_tables_and_reads_once_through_verified_bytes(tmp_path, monkeypatch):
    import patent_analysis.inventor_sidecars as module

    document = evidence_bundle()
    save(tmp_path, document)
    expected = read(tmp_path)
    paths = {}
    schema = module.sidecar_schema()
    for table, rows in document['tables'].items():
        fields = list(schema['$defs'][table]['items']['properties'])
        stream = io.StringIO(newline='')
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, list)
                             else '' if v is None else v for k, v in row.items()})
        paths[table] = f'{table}.csv'
        (tmp_path / paths[table]).write_bytes(stream.getvalue().encode('utf-8'))
    calls = []
    original = module.read_verified_bytes

    def spy(source, **kwargs):
        calls.append(source)
        return original(source, **kwargs)

    monkeypatch.setattr(module, 'read_verified_bytes', spy)
    actual = read_inventor_sidecar_csv(paths, version='1.0.0', allowed_root=tmp_path,
                                       inventor_ids=('p1',), record_ids=('r1',))
    assert actual.tables == expected.tables
    assert sorted(calls) == sorted(paths.values())
    assert len(actual.raw_snapshots) == len(TABLES)


@pytest.mark.parametrize('table,field', [('sources', 'citation'), ('sources', 'url'),
                                         ('reviews', 'reason')])
def test_sidecar_text_rejects_a_trailing_newline_without_echoing_it(tmp_path, table, field):
    document = evidence_bundle()
    document['tables'][table][0][field] = 'private-value\n'
    save(tmp_path, document)
    with pytest.raises(DatasetInputError, match='input is invalid') as caught:
        read(tmp_path)
    assert 'private-value' not in str(caught.value)


@pytest.mark.parametrize('raw', [
    b'{"version":"1.0.0","version":"1.0.0","tables":{}}',
    b'{"version":NaN,"tables":{}}', b'{"version":Infinity,"tables":{}}',
    b'{"version":1e999,"tables":{}}', b'[' * 40 + b'0' + b']' * 40,
])
def test_strict_json_rejections(tmp_path, raw):
    (tmp_path / 'sidecar.json').write_bytes(raw)
    with pytest.raises(DatasetInputError):
        read(tmp_path)


@pytest.mark.parametrize('change', [
    lambda d: d.update(version='2.0.0'),
    lambda d: d.update(unknown=True),
    lambda d: d['tables']['entities'][0].update(unknown=True),
    lambda d: d['tables']['entities'][0].update(source_ids=['missing']),
    lambda d: d['tables']['groups'][0].update(parent_id='unknown'),
    lambda d: d['tables']['events'][0].update(record_ids=['missing']),
    lambda d: d['tables']['sources'][0].update(checked_date='2023-02-29'),
    lambda d: d['tables']['sources'].append(d['tables']['sources'][0].copy()),
    lambda d: d['tables']['entities'][0].update(source_ids=['s1', 's1']),
])
def test_closed_fields_invalid_dates_duplicate_ids_unknown_refs(tmp_path, change):
    document = bundle()
    change(document)
    save(tmp_path, document)
    with pytest.raises(DatasetInputError, match='input is invalid'):
        read(tmp_path)


@pytest.mark.parametrize('source', ['/outside.json', 'C:/private/input.json', '../sidecar.json',
                                    '..\\sidecar.json', '\\\\host\\file.json',
                                    'sidecar.json:stream', '//?/C:/file.json'])
def test_relative_only_paths_and_safe_errors(tmp_path, source):
    with pytest.raises(DatasetInputError) as caught:
        read_inventor_sidecar(source, allowed_root=tmp_path)
    assert source not in str(caught.value)
    assert str(tmp_path) not in str(caught.value)
    assert caught.value.__cause__ is None


def group(identifier, child, parent, start, end):
    return {'group_id': identifier, 'child_id': child, 'parent_id': parent,
            'relation': 'subsidiary', 'valid_from': start, 'valid_to': end,
            'source_ids': ['s1']}


def test_time_valid_groups_and_nonconcurrent_cycle_allowed(tmp_path):
    document = bundle()
    document['tables']['groups'] = [
        group('g1', 'e1', 'e2', '2020-01-01', '2020-12-31'),
        group('g2', 'e2', 'e1', '2021-01-01', None),
        group('g3', 'e1', 'e3', '2021-01-01', None),
    ]
    save(tmp_path, document)
    snapshot = read(tmp_path)
    assert snapshot.group_parents('e1', on='2020-06-01') == ('e2',)
    assert snapshot.group_parents('e1', on='2021-06-01') == ('e3',)
    assert snapshot.group_parents('e1', on='2019-06-01') == ()
    with pytest.raises(DatasetInputError):
        snapshot.group_parents('e1', on='2020')


@pytest.mark.parametrize('groups', [
    [group('g1', 'e1', 'e1', None, None)],
    [group('g1', 'e1', 'e2', None, None), group('g2', 'e2', 'e1', None, None)],
    [group('g1', 'e1', 'e2', None, None), group('g2', 'e2', 'e3', None, None),
     group('g3', 'e3', 'e1', None, None)],
    [group('g1', 'e1', 'e2', '2024', '2024'),
     group('g2', 'e1', 'e3', '2024-12-31', None)],
    [group('g1', 'e1', 'e2', '2025-01-01', '2024-12-31')],
    [group('g1', 'e1', 'e2', '2024-01-01', '2024-12-31'),
     group('g2', 'e1', 'e2', '2024-12-31', None)],
])
def test_group_cycles_overlaps_reversed_intervals_rejected(tmp_path, groups):
    document = bundle()
    document['tables']['groups'] = groups
    save(tmp_path, document)
    with pytest.raises(DatasetInputError):
        read(tmp_path)


def test_entity_alias_overlap_and_identity_duplicates(tmp_path):
    document = bundle()
    aliases = [{'alias_id': 'ea1', 'raw_alias': ' Ａcme ', 'entity_id': 'e1',
                'valid_from': '2024', 'valid_to': '2024', 'source_ids': ['s1']},
               {'alias_id': 'ea2', 'raw_alias': 'Acme', 'entity_id': 'e2',
                'valid_from': '2025', 'valid_to': None, 'source_ids': ['s1']}]
    document['tables']['entity_aliases'] = aliases
    save(tmp_path, document)
    read(tmp_path)
    aliases[1]['valid_from'] = '2024-12'
    save(tmp_path, document)
    with pytest.raises(DatasetInputError):
        read(tmp_path)
    document = bundle()
    duplicate = dict(document['tables']['identities'][0], alias_id='a2', inventor_id='p2')
    document['tables']['identities'].append(duplicate)
    save(tmp_path, document)
    with pytest.raises(DatasetInputError):
        read(tmp_path)


def evidence_bundle():
    document = bundle()
    document['tables']['personal_evidence'] = [
        {'evidence_id': 'pe1', 'inventor_id': 'p1', 'from_entity_id': 'e1',
         'to_entity_id': 'e2', 'valid_from': '2024', 'valid_to': None,
         'type': 'employment_move', 'claim_status': 'reported', 'source_ids': ['s1']}]
    document['tables']['reviews'] = [
        {'review_id': 'rv1', 'inventor_id': 'p1', 'claim': 'employment_move',
         'status': 'accepted', 'reason': 'Synthetic direct evidence', 'reviewed_date': '2024',
         'evidence_ids': ['pe1'], 'event_ids': ['ev1'], 'record_ids': ['r1'],
         'source_ids': ['s1'], 'supersedes_review_id': None}]
    document['tables']['citations'] = [
        {'citation_id': 'c1', 'record_id': 'r1', 'count': 0, 'snapshot_date': '2024-01',
         'citing_ids': [], 'source_ids': ['s1']},
        {'citation_id': 'c2', 'record_id': 'r1', 'count': None, 'snapshot_date': None,
         'citing_ids': None, 'source_ids': ['s1']}]
    return document


def test_evidence_review_citation_missing_and_zero_preserved(tmp_path):
    save(tmp_path, evidence_bundle())
    snapshot = read(tmp_path)
    assert snapshot.tables['citations'][0]['count'] == 0
    assert snapshot.tables['citations'][1]['count'] is None
    assert snapshot.tables['reviews'][0]['status'] == 'accepted'
    assert 'confirmed' not in snapshot.tables['personal_evidence'][0].values()


@pytest.mark.parametrize('change', [
    lambda t: t['personal_evidence'][0].update(inventor_id='missing'),
    lambda t: t['reviews'][0].update(evidence_ids=['missing']),
    lambda t: t['reviews'][0].update(event_ids=['missing']),
    lambda t: t['reviews'][0].update(supersedes_review_id='rv1'),
    lambda t: t['reviews'][0].update(inventor_id='p2'),
    lambda t: t['citations'][0].update(count=1),
    lambda t: t['citations'][0].update(count=-1),
    lambda t: t['personal_evidence'][0].update(from_entity_id=None, to_entity_id=None),
])
def test_evidence_review_citation_reference_contradictions(tmp_path, change):
    document = evidence_bundle()
    change(document['tables'])
    save(tmp_path, document)
    with pytest.raises(DatasetInputError):
        read(tmp_path)


def test_observation_references_are_checked_against_snapshot(tmp_path):
    from patent_analysis.inventor_identity import IdentityResolver
    from patent_analysis.inventor_models import PatentObservation, parse_observation_date
    from patent_analysis.inventor_sidecars import validate_observation_references

    save(tmp_path, bundle())
    snapshot = read(tmp_path)
    resolver = snapshot.identity_resolver()
    o = PatentObservation('r1', (resolver.resolve(inventor_id=' Ａ '),),
                          parse_observation_date('2024', kind='filing'),
                          applicant_ids=('e1',), source_ids=('s1',))
    validate_observation_references(snapshot, (o,), inventor_ids=('p1',))
    from dataclasses import replace

    for bad in (replace(o, source_ids=('unknown',)), replace(o, applicant_ids=('unknown',)),
                replace(o, inventors=(replace(o.inventors[0], source_ids=('unknown',)),)),
                replace(o, inventors=(IdentityResolver().resolve(inventor_id='unknown'),))):
        with pytest.raises(DatasetInputError):
            validate_observation_references(snapshot, (bad,), inventor_ids=('p1',))


def test_csv_reference_arrays_cannot_use_blank_or_delimiter_syntax():
    import patent_analysis.inventor_sidecars as module

    schema = module.sidecar_schema()
    fields = list(schema['$defs']['events']['items']['properties'])
    row = bundle()['tables']['events'][0]
    for bad in ('', 's1|s2', '["s1",null]'):
        stream = io.StringIO(newline='')
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        writer.writerow({k: bad if k == 'record_ids' else
                         json.dumps(v) if isinstance(v, list) else v for k, v in row.items()})
        with pytest.raises(DatasetInputError):
            module._csv_rows(stream.getvalue().encode('utf-8'), 'events', schema)


def test_integer_citations_do_not_accept_float_lexemes(tmp_path):
    document = evidence_bundle()
    document['tables']['citations'][0]['count'] = 0.0
    save(tmp_path, document)
    with pytest.raises(DatasetInputError):
        read(tmp_path)


def test_csv_duplicate_header_invalid_width_and_version(tmp_path):
    paths = {table: f'{table}.csv' for table in TABLES}
    for text in ('source_id,source_id\ns1,s1\n',
                 'source_id,kind,citation,checked_date,url\ns1,local_document\n',
                 'source_id,kind,citation,checked_date,url\ns1,local_document,"oops\n'):
        (tmp_path / 'sources.csv').write_text(text, encoding='utf-8')
        with pytest.raises(DatasetInputError):
            read_inventor_sidecar_csv(paths, version='1.0.0', allowed_root=tmp_path)
    with pytest.raises(DatasetInputError):
        read_inventor_sidecar_csv(paths, version='unknown', allowed_root=tmp_path)


def test_sidecar_semantics_stable_after_row_reference_reordering(tmp_path):
    document = evidence_bundle()
    raw1 = save(tmp_path, document)
    first = read(tmp_path)
    for rows in document['tables'].values():
        rows.reverse()
        for row in rows:
            for value in row.values():
                if isinstance(value, list):
                    value.reverse()
    raw2 = save(tmp_path, document)
    second = read(tmp_path)
    assert first.tables == second.tables
    assert raw1 != raw2
    assert first.receipts != second.receipts


def test_byte_row_and_depth_budgets(tmp_path, monkeypatch):
    import patent_analysis.inventor_sidecars as module

    raw = save(tmp_path, bundle())
    monkeypatch.setattr(module, 'MAX_SIDECAR_BYTES', len(raw))
    read(tmp_path)
    monkeypatch.setattr(module, 'MAX_SIDECAR_BYTES', len(raw) - 1)
    with pytest.raises(DatasetInputError):
        read(tmp_path)
    monkeypatch.setattr(module, 'MAX_SIDECAR_BYTES', len(raw))
    monkeypatch.setattr(module, 'MAX_SIDECAR_ROWS', 7)
    read(tmp_path)
    monkeypatch.setattr(module, 'MAX_SIDECAR_ROWS', 6)
    with pytest.raises(DatasetInputError):
        read(tmp_path)
    monkeypatch.setattr(module, 'MAX_SIDECAR_ROWS', 5000)
    monkeypatch.setattr(module, 'MAX_SIDECAR_DEPTH', 3)
    with pytest.raises(DatasetInputError):
        read(tmp_path)
