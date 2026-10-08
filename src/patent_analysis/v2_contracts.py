"""Common closed schemas and value-only validators for analysis contract v2."""

from __future__ import annotations

import json
from copy import deepcopy
from importlib.resources import files
from typing import Any

from patent_analysis.analysis_contracts import (
    AnalysisContractError,
    StrictDraft202012Validator,
)
from patent_analysis.canonical_v2 import CanonicalizationError, canonical_json_bytes

V2_ANALYSIS_CONTRACT_VERSION = "2.0.0"


def _load_schema(name: str) -> dict[str, Any]:
    text = files("patent_analysis").joinpath("schemas", name).read_text(encoding="utf-8")
    return json.loads(text)


def get_analysis_spec_v2_schema() -> dict[str, Any]:
    return _load_schema("analysis-spec-v2.schema.json")


def get_analysis_result_v2_schema() -> dict[str, Any]:
    return _load_schema("analysis-result-v2.schema.json")


def get_analysis_error_v2_schema() -> dict[str, Any]:
    return _load_schema("analysis-error-v2.schema.json")


def _validate(value: Any, schema: dict[str, Any], noun: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AnalysisContractError(f"{noun} must be an object", details={})
    try:
        canonical_json_bytes(value)
    except CanonicalizationError:
        raise AnalysisContractError(f"{noun} is not JCS representable", details={}) from None
    errors = sorted(
        StrictDraft202012Validator(schema).iter_errors(value),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        raise AnalysisContractError(f"{noun} violates the schema", details={})
    return deepcopy(value)


def _validate_population_semantics(spec: dict[str, Any]) -> None:
    population = spec["population"]
    for filter_spec in population["filters"]:
        if (
            filter_spec["match"] in {"year_range", "outside_year_range"}
            and filter_spec["start_year"] > filter_spec["end_year"]
        ):
            raise AnalysisContractError("analysis v2 spec has a reversed year range", details={})

    seen_dimensions: set[str] = set()
    for selection_set in population["selection_sets"]:
        dimension = selection_set["dimension_role"]
        if dimension in seen_dimensions:
            raise AnalysisContractError(
                "analysis v2 spec repeats a selection dimension", details={}
            )
        seen_dimensions.add(dimension)
        if (
            "start_year" in selection_set
            and selection_set["start_year"] > selection_set["end_year"]
        ):
            raise AnalysisContractError("analysis v2 spec has a reversed year range", details={})


def validate_analysis_spec_v2(spec: Any) -> dict[str, Any]:
    """Validate an already-decoded value; duplicate detection requires the byte dispatcher."""

    validated = _validate(spec, get_analysis_spec_v2_schema(), "analysis v2 spec")
    _validate_population_semantics(validated)
    return validated


def validate_analysis_result_v2(result: Any) -> dict[str, Any]:
    validated = _validate(result, get_analysis_result_v2_schema(), "analysis v2 result")
    population = validated["population"]
    if population["input_rows"] != population["analyzed_rows"] + population["excluded_rows"]:
        raise AnalysisContractError(
            "analysis v2 result population counts do not balance", details={}
        )
    selection = validated.get("family_selection")
    inner_population = validated["data"].get("population")
    if selection is not None and not (
        isinstance(inner_population, dict)
        and selection["representative_rows"] == inner_population.get("input_rows")
        and selection["matched_rows"] <= population["input_rows"]
        and selection["matched_rows"]
        == selection["representative_rows"] + selection["collapsed_rows"]
        and population["analyzed_rows"] <= selection["representative_rows"]
        and selection["unidentified_rows"] <= selection["representative_rows"]
        and (
            selection["collapsed_rows"] == 0
            or selection["unidentified_rows"] < selection["representative_rows"]
        )
    ):
        raise AnalysisContractError(
            "analysis v2 family selection counts do not balance", details={}
        )
    return validated


def validate_analysis_error_v2(error: Any) -> dict[str, Any]:
    return _validate(error, get_analysis_error_v2_schema(), "analysis v2 error")


def build_v2_success_envelope(result: Any, receipt: Any) -> dict[str, Any]:
    validated_result = validate_analysis_result_v2(result)
    receipt_value = receipt.to_dict() if hasattr(receipt, "to_dict") else deepcopy(receipt)
    if not isinstance(receipt_value, dict):
        raise AnalysisContractError("analysis v2 receipt must be an object", details={})
    return {
        "analysis_contract_version": V2_ANALYSIS_CONTRACT_VERSION,
        "ok": True,
        "result": validated_result,
        "receipt": receipt_value,
    }
