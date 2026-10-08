from __future__ import annotations

from copy import deepcopy

import pytest

import patent_analysis
import patent_analysis.analysis_contracts as analysis_contracts
from patent_analysis.analysis_contracts import AnalysisContractError, validate_analysis_spec


def _valid_analysis_result() -> dict[str, object]:
    return {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "count", "column": None},
        "population": {"input_rows": 4, "analyzed_rows": 6},
        "rows": [
            {
                "row_kind": "dimension_value",
                "label": "その他",
                "value": 3,
                "count": 3,
                "share": 0.5,
            },
            {
                "row_kind": "remainder",
                "label": "その他",
                "value": 3,
                "count": 3,
                "share": 0.5,
            },
        ],
        "warnings": [],
    }


def test_count_ranking_spec_is_accepted():
    assert (
        validate_analysis_spec(
            {
                "analysis_type": "ranking",
                "dimension": "出願人",
                "measure": {"mode": "count", "column": None},
                "top_n": 10,
                "include_other": True,
                "multi_value_mode": "all",
            }
        )["dimension"]
        == "出願人"
    )


def test_non_count_ranking_spec_is_accepted():
    assert (
        validate_analysis_spec(
            {
                "analysis_type": "ranking",
                "dimension": "出願人",
                "measure": {"mode": "average", "column": "件数"},
                "top_n": 10,
                "include_other": False,
                "multi_value_mode": "all",
            }
        )["measure"]["column"]
        == "件数"
    )


def test_long_nonblank_dimension_and_measure_column_are_accepted():
    long_dimension = "x" * 301
    long_column = "y" * 301

    assert (
        validate_analysis_spec(
            {
                "analysis_type": "ranking",
                "dimension": long_dimension,
                "measure": {"mode": "count", "column": None},
                "top_n": 10,
                "include_other": True,
                "multi_value_mode": "all",
            }
        )["dimension"]
        == long_dimension
    )

    assert (
        validate_analysis_spec(
            {
                "analysis_type": "ranking",
                "dimension": "出願人",
                "measure": {"mode": "average", "column": long_column},
                "top_n": 10,
                "include_other": False,
                "multi_value_mode": "first",
            }
        )["measure"]["column"]
        == long_column
    )


@pytest.mark.parametrize(
    "spec",
    [
        {"analysis_type": "timeline"},
        {
            "analysis_type": "ranking",
            "dimension": "出願人",
            "measure": {"mode": "average", "column": None},
            "top_n": 10,
            "include_other": True,
            "multi_value_mode": "all",
        },
        {
            "analysis_type": "ranking",
            "dimension": "出願人",
            "measure": {"mode": "count", "column": None},
            "top_n": 0,
            "include_other": True,
            "multi_value_mode": "all",
        },
    ],
)
def test_invalid_analysis_specs_are_rejected(spec):
    with pytest.raises(AnalysisContractError) as caught:
        validate_analysis_spec(spec)
    assert caught.value.code == "analysis.invalid"
    assert caught.value.details == {}


def test_invalid_analysis_specs_reject_whitespace_fields():
    with pytest.raises(AnalysisContractError) as caught:
        validate_analysis_spec(
            {
                "analysis_type": "ranking",
                "dimension": "   ",
                "measure": {"mode": "count", "column": None},
                "top_n": 10,
                "include_other": True,
                "multi_value_mode": "all",
            }
        )
    assert caught.value.code == "analysis.invalid"
    assert caught.value.details == {}

    with pytest.raises(AnalysisContractError) as caught:
        validate_analysis_spec(
            {
                "analysis_type": "ranking",
                "dimension": "出願人",
                "measure": {"mode": "average", "column": "   "},
                "top_n": 10,
                "include_other": True,
                "multi_value_mode": "all",
            }
        )
    assert caught.value.code == "analysis.invalid"
    assert caught.value.details == {}


def test_invalid_analysis_specs_reject_unexpected_properties():
    with pytest.raises(AnalysisContractError) as caught:
        validate_analysis_spec(
            {
                "analysis_type": "ranking",
                "dimension": "出願人",
                "measure": {"mode": "count", "column": None},
                "top_n": 10,
                "include_other": True,
                "multi_value_mode": "all",
                "unexpected_property": "oops",
            }
        )
    assert caught.value.code == "analysis.invalid"
    assert caught.value.details == {}

    with pytest.raises(AnalysisContractError) as caught:
        validate_analysis_spec(
            {
                "analysis_type": "ranking",
                "dimension": "出願人",
                "measure": {
                    "mode": "count",
                    "column": None,
                    "unexpected_property": "oops",
                },
                "top_n": 10,
                "include_other": True,
                "multi_value_mode": "all",
            }
        )
    assert caught.value.code == "analysis.invalid"
    assert caught.value.details == {}


def test_validate_analysis_spec_returns_a_defensive_copy():
    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "count", "column": None},
        "top_n": 10,
        "include_other": True,
        "multi_value_mode": "all",
    }

    validated = validate_analysis_spec(spec)

    spec["top_n"] = 99
    assert validated["top_n"] == 10


def test_analysis_result_schema_and_validator_are_public_contract_apis() -> None:
    schema = analysis_contracts.get_analysis_result_schema()
    result = _valid_analysis_result()

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == "urn:patent-analysis:analysis-result:1.0.0"
    assert schema["additionalProperties"] is False
    assert set(schema["$defs"]["rankingRow"]["required"]) == {
        "row_kind",
        "label",
        "value",
        "count",
        "share",
    }
    assert schema["$defs"]["rankingRow"]["additionalProperties"] is False
    assert analysis_contracts.validate_analysis_result(result) == result
    assert patent_analysis.get_analysis_result_schema()["$id"] == schema["$id"]
    assert patent_analysis.validate_analysis_result(result) == result


@pytest.mark.parametrize(
    "invalid_case",
    [
        "missing_row_kind",
        "unknown_row_kind",
        "additional_row_field",
        "additional_result_field",
    ],
)
def test_analysis_result_schema_rejects_invalid_row_shapes(invalid_case: str) -> None:
    result = _valid_analysis_result()
    rows = result["rows"]
    assert isinstance(rows, list)

    if invalid_case == "missing_row_kind":
        rows[0].pop("row_kind")
    elif invalid_case == "unknown_row_kind":
        rows[0]["row_kind"] = "other"
    elif invalid_case == "additional_row_field":
        rows[0]["unexpected"] = True
    else:
        result["unexpected"] = True

    with pytest.raises(AnalysisContractError) as caught:
        analysis_contracts.validate_analysis_result(result)

    assert caught.value.code == "analysis.invalid"
    assert caught.value.retryable is False
    assert caught.value.details == {}


@pytest.mark.parametrize("field", ["value", "share"])
@pytest.mark.parametrize(
    "nonfinite_value",
    [float("nan"), float("inf"), float("-inf")],
    ids=["nan", "positive_infinity", "negative_infinity"],
)
def test_analysis_result_rejects_nonfinite_row_numbers(
    field: str,
    nonfinite_value: float,
) -> None:
    result = _valid_analysis_result()
    rows = result["rows"]
    assert isinstance(rows, list)
    rows[0][field] = nonfinite_value

    with pytest.raises(AnalysisContractError) as caught:
        analysis_contracts.validate_analysis_result(result)

    assert caught.value.code == "analysis.invalid"
    assert caught.value.retryable is False
    assert caught.value.details == {}


@pytest.mark.parametrize("field", ["value", "share"])
@pytest.mark.parametrize("boolean_value", [False, True])
def test_analysis_result_rejects_boolean_row_numbers(
    field: str,
    boolean_value: bool,
) -> None:
    result = _valid_analysis_result()
    rows = result["rows"]
    assert isinstance(rows, list)
    rows[0][field] = boolean_value

    with pytest.raises(AnalysisContractError):
        analysis_contracts.validate_analysis_result(result)


@pytest.mark.parametrize("blank_field", ["dimension", "dimension_label", "remainder_label"])
def test_analysis_result_rejects_whitespace_only_dimension_and_row_labels(
    blank_field: str,
) -> None:
    result = _valid_analysis_result()
    rows = result["rows"]
    assert isinstance(rows, list)

    if blank_field == "dimension":
        result["dimension"] = "   "
    elif blank_field == "dimension_label":
        rows[0]["label"] = "   "
    else:
        rows[-1]["label"] = "   "

    with pytest.raises(AnalysisContractError) as caught:
        analysis_contracts.validate_analysis_result(result)

    assert caught.value.code == "analysis.invalid"
    assert caught.value.details == {}


def test_analysis_result_schema_rejects_zero_row_count() -> None:
    result = _valid_analysis_result()
    rows = result["rows"]
    assert isinstance(rows, list)
    rows[0]["count"] = 0

    with pytest.raises(AnalysisContractError) as caught:
        analysis_contracts.validate_analysis_result(result)

    assert caught.value.code == "analysis.invalid"
    assert caught.value.details == {}


@pytest.mark.parametrize("remainder_position", ["sole", "first"])
def test_analysis_result_rejects_remainder_without_preceding_dimension_value(
    remainder_position: str,
) -> None:
    result = _valid_analysis_result()
    rows = result["rows"]
    assert isinstance(rows, list)
    remainder = deepcopy(rows[-1])

    if remainder_position == "sole":
        result["rows"] = [remainder]
    else:
        result["rows"] = [remainder, deepcopy(rows[0])]

    with pytest.raises(AnalysisContractError) as caught:
        analysis_contracts.validate_analysis_result(result)

    assert caught.value.code == "analysis.invalid"
    assert caught.value.details == {}


def test_validate_analysis_result_returns_a_deep_defensive_copy() -> None:
    result = _valid_analysis_result()

    validated = analysis_contracts.validate_analysis_result(result)

    result["measure"]["mode"] = "sum"
    result["population"]["input_rows"] = 999
    result["rows"][0]["label"] = "mutated"
    result["warnings"].append("mutated")

    assert validated["measure"] == {"mode": "count", "column": None}
    assert validated["population"] == {"input_rows": 4, "analyzed_rows": 6}
    assert validated["rows"][0]["label"] == "その他"
    assert validated["warnings"] == []


@pytest.mark.parametrize(
    "invalid_case",
    [
        "remainder_not_last",
        "more_than_one_remainder",
        "wrong_remainder_label",
        "duplicate_kind_and_label",
    ],
)
def test_analysis_result_semantic_rules_reject_ambiguous_rows(invalid_case: str) -> None:
    result = _valid_analysis_result()
    rows = result["rows"]
    assert isinstance(rows, list)

    if invalid_case == "remainder_not_last":
        rows.reverse()
    elif invalid_case == "more_than_one_remainder":
        rows.append(deepcopy(rows[-1]))
    elif invalid_case == "wrong_remainder_label":
        rows[-1]["label"] = "Other"
    else:
        duplicate = deepcopy(rows[0])
        duplicate["label"] = "その他"
        rows.insert(1, duplicate)

    with pytest.raises(AnalysisContractError) as caught:
        analysis_contracts.validate_analysis_result(result)

    assert caught.value.code == "analysis.invalid"
    assert caught.value.retryable is False
    assert caught.value.details == {}
