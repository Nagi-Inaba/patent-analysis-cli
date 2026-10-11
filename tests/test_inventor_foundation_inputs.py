from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_inputs import prepare_inventor_inputs
from patent_analysis.inventor_models import ObservationDate, parse_observation_date


@pytest.mark.parametrize(('raw', 'precision', 'start', 'end'), [
    ('2024-02-29', 'day', date(2024, 2, 29), date(2024, 2, 29)),
    ('2024-02', 'month', date(2024, 2, 1), date(2024, 2, 29)),
    ('2024', 'year', date(2024, 1, 1), date(2024, 12, 31)),
    ('', 'missing', None, None),
    (None, 'missing', None, None),
])
def test_date_precision_and_missing(raw, precision, start, end):
    value = parse_observation_date(raw, kind='filing')
    assert (value.raw, value.kind, value.precision, value.start, value.end) == (
        raw, 'filing', precision, start, end)
    with pytest.raises(FrozenInstanceError):
        value.kind = 'employment'


@pytest.mark.parametrize('raw', ['2023-02-29', '2024-13', '2024-00-01', ' 2024 ',
                                 '２０２４', '2024/01/01', '2024-1', '0000', 'n/a', 2024])
def test_invalid_dates_are_not_missing(raw):
    with pytest.raises(DatasetInputError):
        parse_observation_date(raw, kind='filing')


def test_prepare_preserves_raw_ids_missing_coverage_and_filters(tmp_path):
    import json

    rows = [
        {'record': 'r1', 'people': '[" Ａ ","B","B"]', 'day': '2024-02',
         'ipc': 'a01b 1/00|A01B 1/00', 'org': '["e1","e2"]'},
        {'record': 'r2', 'people': '[]', 'day': '', 'ipc': '', 'org': '[]'},
    ]
    (tmp_path / 'patents.json').write_text(json.dumps(rows), encoding='utf-8')
    bindings = {'record_id': 'record', 'inventor_ids': 'people', 'date': 'day',
                'classification': 'ipc', 'applicant_ids': 'org'}
    prepared = prepare_inventor_inputs('patents.json', allowed_root=tmp_path,
                                       bindings=bindings, date_kind='filing')
    obs = prepared.observations[0]
    assert obs.inventor_keys == (('id', ' Ａ '), ('id', 'B'))
    assert tuple(p.raw_id for p in obs.inventors) == (' Ａ ', 'B', 'B')
    assert obs.classifications == (('IPC', 'A01B 1/00'),)
    assert obs.applicant_ids == ('e1', 'e2')
    assert obs.source_ordinal == 1
    assert dict(prepared.coverage) == {'input_rows': 2, 'included_rows': 2, 'filtered_rows': 0,
                                     'missing_inventors': 1, 'missing_date': 1,
                                     'missing_applicants': 1, 'missing_classification': 1}
    with pytest.raises(FrozenInstanceError):
        obs.record_id = 'new'
    filtered = prepare_inventor_inputs(
        'patents.json', allowed_root=tmp_path, bindings=bindings, date_kind='filing',
        population={'family_mode': 'records', 'filters': [
            {'role': 'inventor_id', 'match': 'exact', 'value': ' Ａ '}]})
    assert tuple(o.record_id for o in filtered.observations) == ('r1',)
    with pytest.raises(DatasetInputError):
        prepare_inventor_inputs('patents.json', allowed_root=tmp_path, bindings=bindings,
                               date_kind='filing', population={'family_mode': 'earliest',
                                                              'filters': []})


@pytest.mark.parametrize('people', ['A|B', '["A",null]', '["A",1]', '{"A":1}'])
def test_id_multivalues_require_explicit_json_string_array(tmp_path, people):
    import json

    (tmp_path / 'p.json').write_text(json.dumps([{'r': 'r', 'i': people}]), encoding='utf-8')
    with pytest.raises(DatasetInputError):
        prepare_inventor_inputs('p.json', allowed_root=tmp_path,
                               bindings={'record_id': 'r', 'inventor_ids': 'i'})


def test_date_constructor_cannot_forge_precision():
    with pytest.raises(DatasetInputError):
        ObservationDate('2024', 'filing', 'day', date(2024, 1, 1), date(2024, 1, 1))
