from __future__ import annotations

import json

import pytest

import patent_analysis.analysis_dispatch as analysis_dispatch
from patent_analysis.analysis_budgets import MAX_ANALYSIS_SPEC_BYTES
from patent_analysis.analysis_contracts import AnalysisContractError, validate_analysis_spec
from patent_analysis.analysis_dispatch import (
    ValidatedV1Spec,
    dispatch_and_validate_spec_bytes,
)

RANKING_SPEC = {
    "analysis_type": "ranking",
    "dimension": "出願人",
    "measure": {"mode": "count", "column": None},
    "top_n": 10,
    "include_other": True,
    "multi_value_mode": "all",
}
RANKING_SPEC_BYTES = json.dumps(RANKING_SPEC, ensure_ascii=False).encode()


def test_missing_contract_version_dispatches_only_to_v1() -> None:
    validated = dispatch_and_validate_spec_bytes(RANKING_SPEC_BYTES)
    assert isinstance(validated, ValidatedV1Spec)
    assert validated.contract_version == "1.0.0"
    assert validated.spec == RANKING_SPEC


def test_explicit_v1_version_is_not_rewritten_to_legacy_v1() -> None:
    explicit = {**RANKING_SPEC, "analysis_contract_version": "1.0.0"}
    with pytest.raises(AnalysisContractError):
        dispatch_and_validate_spec_bytes(json.dumps(explicit).encode())


def test_explicit_v2_requires_common_schema_and_registered_v2_definition() -> None:
    spec = {
        "analysis_contract_version": "2.0.0",
        "analysis_id": "future-analysis.v1",
        "resolution": {},
        "normalization": {"profiles": []},
        "population": {"filters": [], "selection_sets": [], "family_mode": "records"},
        "parameters": {},
    }
    with pytest.raises(AnalysisContractError, match="unknown analysis_id"):
        dispatch_and_validate_spec_bytes(json.dumps(spec).encode())


def test_explicit_v2_cannot_reuse_the_registered_v1_ranking_definition() -> None:
    spec = {
        "analysis_contract_version": "2.0.0",
        "analysis_id": "ranking.v1",
        "resolution": {},
        "normalization": {"profiles": []},
        "population": {"filters": [], "selection_sets": [], "family_mode": "records"},
        "parameters": {},
    }
    with pytest.raises(AnalysisContractError):
        dispatch_and_validate_spec_bytes(json.dumps(spec).encode())


def test_versionless_v1_dispatch_preserves_legacy_duplicate_last_wins() -> None:
    raw = (
        b'{"analysis_type":"timeline","analysis_type":"ranking",'
        b'"dimension":"applicant","measure":{"mode":"count","column":null},'
        b'"top_n":10,"include_other":true,"multi_value_mode":"all"}'
    )
    validated = dispatch_and_validate_spec_bytes(raw)
    assert isinstance(validated, ValidatedV1Spec)
    assert validated.spec["analysis_type"] == "ranking"


def test_versionless_v1_dispatch_preserves_legacy_escaped_lone_surrogate() -> None:
    raw = (
        b'{"analysis_type":"ranking","dimension":"\\ud800",'
        b'"measure":{"mode":"count","column":null},"top_n":10,'
        b'"include_other":true,"multi_value_mode":"all"}'
    )
    validated = dispatch_and_validate_spec_bytes(raw)
    assert isinstance(validated, ValidatedV1Spec)
    assert validated.spec["dimension"] == "\ud800"


def test_versionless_v1_dispatch_preserves_legacy_validation_error() -> None:
    raw = (
        b'{"analysis_type":"ranking","dimension":"\\ud800",'
        b'"measure":{"mode":"count","column":null},"top_n":10,"top_n":0,'
        b'"include_other":true,"multi_value_mode":"all"}'
    )
    legacy_value = json.loads(raw.decode("utf-8"))
    with pytest.raises(AnalysisContractError) as legacy_error:
        validate_analysis_spec(legacy_value)
    with pytest.raises(AnalysisContractError) as dispatch_error:
        dispatch_and_validate_spec_bytes(raw)

    assert str(dispatch_error.value) == str(legacy_error.value)
    assert dispatch_error.value.as_dict() == legacy_error.value.as_dict()


@pytest.mark.parametrize(
    "raw",
    [
        RANKING_SPEC_BYTES,
        b'{"analysis_contract_version":"2.0.0","analysis_id":"timeline.v1"}',
    ],
    ids=["versionless-v1", "explicit-v2"],
)
def test_dispatch_rejects_oversized_bytes_before_legacy_parse(
    raw: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_if_called(_raw: bytes) -> object:
        pytest.fail("legacy parser must not be called for oversized bytes")

    monkeypatch.setattr(analysis_dispatch, "_parse_legacy_json_bytes", fail_if_called)
    oversized = raw + (b" " * (MAX_ANALYSIS_SPEC_BYTES - len(raw) + 1))
    with pytest.raises(AnalysisContractError, match="byte limit"):
        dispatch_and_validate_spec_bytes(oversized)


def test_explicit_v2_dispatch_remains_strict_for_duplicate_keys_and_surrogates() -> None:
    duplicate = (
        b'{"analysis_contract_version":"2.0.0","analysis_id":"timeline.v1",'
        b'"analysis_id":"timeline.v1","resolution":{},'
        b'"normalization":{"profiles":[]},'
        b'"population":{"filters":[],"selection_sets":[],"family_mode":"records"},'
        b'"parameters":{}}'
    )
    surrogate = duplicate.replace(
        b'"analysis_id":"timeline.v1","analysis_id":"timeline.v1"',
        b'"analysis_id":"\\ud800"',
    )
    with pytest.raises(AnalysisContractError):
        dispatch_and_validate_spec_bytes(duplicate)
    with pytest.raises(AnalysisContractError):
        dispatch_and_validate_spec_bytes(surrogate)


@pytest.mark.parametrize(
    "number",
    [
        b"1e999999999999999999999999999999999999",
        b"-1e999999999999999999999999999999999999",
        b"-1e-999999999999999999999999999999999999",
    ],
)
def test_explicit_v2_dispatch_converts_extreme_numeric_errors(number: bytes) -> None:
    raw = (
        b'{"analysis_contract_version":"2.0.0","analysis_id":"timeline.v1",'
        b'"resolution":{},"normalization":{"profiles":[]},'
        b'"population":{"filters":[],"selection_sets":[],"family_mode":"records"},'
        b'"parameters":{"value":' + number + b"}}"
    )
    with pytest.raises(AnalysisContractError, match="strict JSON"):
        dispatch_and_validate_spec_bytes(raw)


def test_explicit_v2_dispatch_handles_supported_positive_extreme_underflow() -> None:
    raw = (
        b'{"analysis_contract_version":"2.0.0","analysis_id":"future-analysis.v1",'
        b'"resolution":{},"normalization":{"profiles":[]},'
        b'"population":{"filters":[],"selection_sets":[],"family_mode":"records"},'
        b'"parameters":{"value":1e-999999999999999999999999999999999999}}'
    )
    with pytest.raises(AnalysisContractError, match="unknown analysis_id"):
        dispatch_and_validate_spec_bytes(raw)


def test_dispatch_rejects_unknown_versions() -> None:
    with pytest.raises(AnalysisContractError):
        dispatch_and_validate_spec_bytes(b'{"analysis_contract_version":"3.0.0"}')
