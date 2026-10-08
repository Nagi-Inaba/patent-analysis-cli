"""Real API/CLI contracts for the new JSON slices; requires a full checkout.

No analysis, CSV reader, or CLI execution is mocked. These tests are separate
from the portable arithmetic tests so a partial checkout cannot masquerade as
end-to-end verification.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from patent_analysis import api, cli
from patent_analysis.analyses._advanced_registration import MODULES
from patent_analysis.analysis_contracts import AnalysisContractError
from patent_analysis.analysis_registry import get_analysis_definition
from patent_analysis.canonical_v2 import canonical_json_bytes

EXAMPLES = Path(__file__).resolve().parents[1] / 'examples' / 'advanced'
IDS = tuple(module.ANALYSIS_ID for module in MODULES)


@pytest.mark.parametrize('analysis_id', IDS)
def test_advanced_csv_api_cli_and_public_schemas(
    analysis_id: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / 'patents.csv'
    before = (EXAMPLES / 'patents.csv').read_bytes()
    source.write_bytes(before)
    slug = analysis_id.removesuffix('.v1')
    spec_file = tmp_path / 'spec.json'
    spec_bytes = (EXAMPLES / (slug + '.json')).read_bytes()
    spec_file.write_bytes(spec_bytes)
    monkeypatch.setenv('PATENT_ANALYSIS_ALLOWED_ROOT', str(tmp_path))

    result = api.run_analysis_csv(source.name, spec_bytes, allowed_root=tmp_path)
    again = api.run_analysis_csv(source.name, spec_bytes, allowed_root=tmp_path)
    assert canonical_json_bytes(result) == canonical_json_bytes(again)
    assert result['analysis_id'] == analysis_id
    assert result['population']['input_rows'] == 10
    assert result['population']['analyzed_rows'] > 0
    assert cli.main(['analyze', source.name, '--spec', spec_file.name, '--json']) == 0
    output = capsys.readouterr()
    assert not output.err
    assert json.loads(output.out) == result
    assert source.read_bytes() == before
    assert api.validate_analysis_spec_bytes(spec_bytes)['analysis_id'] == analysis_id
    for kind in ('parameters', 'result'):
        schema = api.get_public_schema(f'{slug}-{kind}-v1.schema.json')
        assert schema['additionalProperties'] is False
    definition = get_analysis_definition(analysis_id)
    assert definition.compatible_render_marks == (definition.analysis_id[:-3] + "-svg.v1",)
    assert definition.mcp_public is True


def test_semantic_preflight_rejects_reversed_span_without_input_file() -> None:
    spec = json.loads((EXAMPLES / 'growth-quadrant.json').read_text(encoding='utf-8'))
    spec['parameters']['long_end_year'] = spec['parameters']['long_start_year']
    with pytest.raises(AnalysisContractError):
        api.validate_analysis_spec_bytes(canonical_json_bytes(spec))


def test_semantic_preflight_rejects_same_comparison_group() -> None:
    spec = json.loads((EXAMPLES / 'compara.json').read_text(encoding='utf-8'))
    spec['parameters']['group_b'] = spec['parameters']['group_a']
    with pytest.raises(AnalysisContractError):
        api.validate_analysis_spec_bytes(canonical_json_bytes(spec))
