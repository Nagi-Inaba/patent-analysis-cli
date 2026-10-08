"""Closed neutral chart-model builders for composition results."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from patent_analysis._render_canonical import canonical_json_bytes, sha256_bytes
from patent_analysis.chart_models._common import (
    build_receipt,
    coerce_analysis_result,
    fixed_render_spec,
    validate_schema,
)
from patent_analysis.chart_models.series import CATEGORICAL_RENDER_PROFILE_ID

COMPOSITION_BAR_MARK = "composition-bar-svg.v1"
COMPOSITION_PIE_MARK = "composition-pie-svg.v1"
COMPOSITION_RENDER_MARKS = (COMPOSITION_BAR_MARK, COMPOSITION_PIE_MARK)
COMPOSITION_RENDER_PROFILE_ID = CATEGORICAL_RENDER_PROFILE_ID


def _chart_type(mark: str) -> str:
    if mark == COMPOSITION_BAR_MARK:
        return "composition.bar"
    if mark == COMPOSITION_PIE_MARK:
        return "composition.pie"
    raise ValueError("unknown composition renderer mark")


def _validate_composition_semantics(
    data: Mapping[str, object],
    population: object,
) -> None:
    measure = data.get("measure")
    items = data.get("items")
    if not isinstance(measure, Mapping) or not isinstance(items, list):
        raise ValueError("composition result semantics are invalid")
    labels: set[str] = set()
    other_indexes: list[int] = []
    values: list[float] = []
    row_counts: list[int] = []
    shares: list[float] = []
    bases: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            raise ValueError("composition result semantics are invalid")
        label = item.get("label")
        value = item.get("value")
        row_count = item.get("row_count")
        share = item.get("share")
        basis = item.get("share_basis")
        if (
            not isinstance(label, str)
            or not label
            or label in labels
            or type(value) not in {int, float}
            or type(row_count) is not int
            or row_count <= 0
            or type(share) not in {int, float}
            or basis not in {"value", "row_count"}
        ):
            raise ValueError("composition result semantics are invalid")
        labels.add(label)
        values.append(float(value))
        row_counts.append(row_count)
        shares.append(float(share))
        bases.append(str(basis))
        if item.get("is_other") is True:
            other_indexes.append(index)
    if len(other_indexes) > 1 or (other_indexes and other_indexes[0] != len(items) - 1):
        raise ValueError("composition result semantics are invalid")

    mode = measure.get("mode")
    expected_basis = (
        "value"
        if mode in {"count", "sum"} and all(value >= 0 for value in values)
        else "row_count"
    )
    if any(basis != expected_basis for basis in bases):
        raise ValueError("composition share basis is invalid")
    weights = values if expected_basis == "value" else [float(value) for value in row_counts]
    total = sum(weights)
    expected = [weight / total for weight in weights] if total > 0 else [0.0] * len(weights)
    if any(
        abs(actual - wanted) > 1e-12
        for actual, wanted in zip(shares, expected, strict=True)
    ):
        raise ValueError("composition shares are invalid")

    if not isinstance(population, Mapping):
        raise ValueError("composition population is invalid")
    input_rows = population.get("input_rows")
    analyzed_rows = population.get("analyzed_rows")
    excluded_rows = population.get("excluded_rows")
    if (
        type(input_rows) is not int
        or type(analyzed_rows) is not int
        or type(excluded_rows) is not int
        or input_rows != analyzed_rows + excluded_rows
    ):
        raise ValueError("composition population is invalid")


def build_composition_chart_model(
    analysis_result: object,
    *,
    mark: str,
) -> tuple[dict[str, object], dict[str, object]]:
    """Build a fixed chart model without reinterpreting value/share semantics."""

    chart_type = _chart_type(mark)
    result = coerce_analysis_result(
        analysis_result,
        analysis_id="composition.v1",
        result_variant="composition",
        result_schema="composition-result-v1.schema.json",
    )
    data = result["data"]
    assert isinstance(data, dict)
    population = result["population"]
    _validate_composition_semantics(data, population)

    model: dict[str, object] = {
        "chart_model_contract_version": "1.0.0",
        "chart_type": chart_type,
        "mark": mark,
        "analysis_result_sha256": sha256_bytes(canonical_json_bytes(result)),
        "title": "構成比",
        "measure": deepcopy(data["measure"]),
        "items": deepcopy(data["items"]),
        "population": deepcopy(population),
        "warnings": list(result["warnings"]),
    }
    validate_schema(model, "categorical-chart-model-v1.schema.json")
    receipt = build_receipt(result, data, model, mark=mark)
    return deepcopy(model), deepcopy(receipt)


def build_composition_render_spec(
    *,
    mark: str,
    item_count: int,
) -> dict[str, object]:
    """Build the fixed categorical render spec for a composition mark."""

    chart_type = _chart_type(mark)
    if type(item_count) is not int or not 0 <= item_count <= 101:
        raise ValueError("composition render dimensions are invalid")
    renderer_kind = (
        "composition.bar.svg"
        if chart_type == "composition.bar"
        else "composition.pie.svg"
    )
    spec = fixed_render_spec(
        renderer_kind=renderer_kind,
        render_profile_id=CATEGORICAL_RENDER_PROFILE_ID,
    )
    validate_schema(spec, "categorical-render-spec-v1.schema.json")
    return deepcopy(spec)


__all__ = (
    "COMPOSITION_BAR_MARK",
    "COMPOSITION_PIE_MARK",
    "COMPOSITION_RENDER_MARKS",
    "COMPOSITION_RENDER_PROFILE_ID",
    "build_composition_chart_model",
    "build_composition_render_spec",
)
