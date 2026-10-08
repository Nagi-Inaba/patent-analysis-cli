from __future__ import annotations

from copy import deepcopy

import pytest

from patent_analysis.analysis_contracts import AnalysisContractError
from patent_analysis.v2_contracts import (
    V2_ANALYSIS_CONTRACT_VERSION,
    build_v2_success_envelope,
    get_analysis_error_v2_schema,
    get_analysis_result_v2_schema,
    get_analysis_spec_v2_schema,
    validate_analysis_error_v2,
    validate_analysis_result_v2,
    validate_analysis_spec_v2,
)

V2_SPEC = {
    "analysis_contract_version": "2.0.0",
    "analysis_id": "timeline.v1",
    "resolution": {"profile": "column-alias.v2", "bindings": {"year": "公開年"}},
    "normalization": {"profiles": ["year-workbench.v1"]},
    "population": {"filters": [], "selection_sets": [], "family_mode": "records"},
    "parameters": {},
}

V2_RESULT = {
    "analysis_id": "timeline.v1",
    "algorithm_version": "1.0.0",
    "result_variant": "series",
    "population": {"input_rows": 10, "analyzed_rows": 8, "excluded_rows": 2},
    "data": {},
    "warnings": [],
}


def test_v2_schemas_are_distinct_closed_contract_resources() -> None:
    spec_schema = get_analysis_spec_v2_schema()
    result_schema = get_analysis_result_v2_schema()
    error_schema = get_analysis_error_v2_schema()

    assert spec_schema["$id"] == "urn:patent-analysis:analysis-spec:2.0.0"
    assert result_schema["$id"] == "urn:patent-analysis:analysis-result:2.0.0"
    assert error_schema["$id"] == "urn:patent-analysis:analysis-error:2.0.0"
    assert spec_schema["additionalProperties"] is False
    assert result_schema["additionalProperties"] is False
    assert error_schema["additionalProperties"] is False


def test_v2_common_spec_is_closed_but_leaves_parameters_to_definition_schema() -> None:
    spec = deepcopy(V2_SPEC)
    spec["parameters"] = {"definition_specific": {"nested": True}}
    assert validate_analysis_spec_v2(spec) == spec

    spec["unexpected"] = True
    with pytest.raises(AnalysisContractError):
        validate_analysis_spec_v2(spec)


def test_v2_common_population_contract_rejects_arbitrary_predicates() -> None:
    spec = deepcopy(V2_SPEC)
    spec["population"]["filters"] = [
        {"role": "year", "effect": "include", "match": "regex", "value": ".*"}
    ]
    with pytest.raises(AnalysisContractError):
        validate_analysis_spec_v2(spec)


def test_v2_common_population_contract_rejects_reversed_ranges() -> None:
    spec = deepcopy(V2_SPEC)
    spec["population"]["filters"] = [
        {
            "role": "year",
            "effect": "include",
            "match": "year_range",
            "start_year": 2025,
            "end_year": 2020,
        }
    ]
    with pytest.raises(AnalysisContractError):
        validate_analysis_spec_v2(spec)


def test_v2_common_population_contract_rejects_duplicate_selection_dimensions() -> None:
    spec = deepcopy(V2_SPEC)
    selection = {"dimension_role": "applicant", "mode": "include", "values": ["A"]}
    spec["population"]["selection_sets"] = [selection, deepcopy(selection)]
    with pytest.raises(AnalysisContractError):
        validate_analysis_spec_v2(spec)


def test_v2_value_only_contract_helpers_still_require_jcs_representability() -> None:
    spec = deepcopy(V2_SPEC)
    spec["parameters"] = {"unsafe_integer": 2**53}
    with pytest.raises(AnalysisContractError):
        validate_analysis_spec_v2(spec)


def test_v2_result_and_error_contracts_are_closed() -> None:
    assert validate_analysis_result_v2(V2_RESULT) == V2_RESULT
    error = {
        "analysis_contract_version": "2.0.0",
        "ok": False,
        "error": {"code": "analysis.invalid", "message": "invalid", "details": {}},
    }
    assert validate_analysis_error_v2(error) == error

    invalid_result = {**V2_RESULT, "echarts_option": {}}
    with pytest.raises(AnalysisContractError):
        validate_analysis_result_v2(invalid_result)


def test_v2_result_population_is_closed_and_rejects_definition_specific_data() -> None:
    result = deepcopy(V2_RESULT)
    result["population"]["definition_specific"] = {"nested": True}
    with pytest.raises(AnalysisContractError):
        validate_analysis_result_v2(result)


@pytest.mark.parametrize("field", ["input_rows", "analyzed_rows", "excluded_rows"])
def test_v2_result_population_rejects_boolean_counts(field: str) -> None:
    result = deepcopy(V2_RESULT)
    result["population"][field] = True
    with pytest.raises(AnalysisContractError):
        validate_analysis_result_v2(result)


def test_v2_result_population_requires_count_conservation() -> None:
    result = deepcopy(V2_RESULT)
    result["population"]["excluded_rows"] = 1
    with pytest.raises(AnalysisContractError):
        validate_analysis_result_v2(result)


def test_v2_success_envelope_rejects_invalid_population() -> None:
    result = deepcopy(V2_RESULT)
    result["population"] = {"definition_specific": {"nested": True}}
    with pytest.raises(AnalysisContractError):
        build_v2_success_envelope(result, {"result_sha256": "0" * 64})


def test_v2_success_envelope_has_exact_outer_shape() -> None:
    envelope = build_v2_success_envelope(V2_RESULT, {"result_sha256": "0" * 64})
    assert V2_ANALYSIS_CONTRACT_VERSION == "2.0.0"
    assert tuple(envelope) == ("analysis_contract_version", "ok", "result", "receipt")
    assert envelope == {
        "analysis_contract_version": "2.0.0",
        "ok": True,
        "result": V2_RESULT,
        "receipt": {"result_sha256": "0" * 64},
    }
