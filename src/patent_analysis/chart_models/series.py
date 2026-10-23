"""Closed neutral chart-model builders for timeline series results."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy

from patent_analysis._render_canonical import canonical_json_bytes, sha256_bytes
from patent_analysis.chart_models._common import (
    build_receipt,
    coerce_analysis_result,
    fixed_render_spec,
    validate_schema,
)

SERIES_LINE_MARK = "series-line-svg.v1"
SERIES_STACKED_BAR_MARK = "series-stacked-bar-svg.v1"
SERIES_RENDER_MARKS = (SERIES_LINE_MARK, SERIES_STACKED_BAR_MARK)
CATEGORICAL_RENDER_PROFILE_ID = "categorical-svg-ja-jp-node24-echarts6.v1"
SERIES_RENDER_PROFILE_ID = CATEGORICAL_RENDER_PROFILE_ID


def _chart_type(mark: str) -> str:
    if mark == SERIES_LINE_MARK:
        return "series.line"
    if mark == SERIES_STACKED_BAR_MARK:
        return "series.stacked-bar"
    raise ValueError("unknown series renderer mark")


def _validate_series_lengths(data: Mapping[str, object]) -> None:
    x = data.get("x")
    series = data.get("series")
    if not isinstance(x, Sequence) or isinstance(x, (str, bytes)) or not isinstance(series, list):
        raise ValueError("series result data is invalid")
    expected = len(x)
    for item in series:
        if not isinstance(item, Mapping):
            raise ValueError("series result data is invalid")
        values = item.get("values")
        row_counts = item.get("row_counts")
        if not isinstance(values, list) or not isinstance(row_counts, list):
            raise ValueError("series result data is invalid")
        if len(values) != expected or len(row_counts) != expected:
            raise ValueError("series result lengths are inconsistent")


def _validate_series_semantics(
    data: Mapping[str, object],
    population: object,
) -> None:
    x = data.get("x")
    items = data.get("series")
    if not isinstance(x, list) or not isinstance(items, list):
        raise ValueError("series result semantics are invalid")
    labels: set[str] = set()
    other_indexes: list[int] = []
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            raise ValueError("series result semantics are invalid")
        label = item.get("label")
        values = item.get("values")
        row_counts = item.get("row_counts")
        if (
            not isinstance(label, str)
            or not label
            or label in labels
            or not isinstance(values, list)
            or not isinstance(row_counts, list)
            or len(values) != len(x)
            or len(row_counts) != len(x)
        ):
            raise ValueError("series result semantics are invalid")
        labels.add(label)
        if item.get("is_other") is True:
            other_indexes.append(index)
    if len(other_indexes) > 1 or (other_indexes and other_indexes[0] != len(items) - 1):
        raise ValueError("series result semantics are invalid")
    if not isinstance(population, Mapping):
        raise ValueError("series population is invalid")
    input_rows = population.get("input_rows")
    analyzed_rows = population.get("analyzed_rows")
    excluded_rows = population.get("excluded_rows")
    if (
        type(input_rows) is not int
        or type(analyzed_rows) is not int
        or type(excluded_rows) is not int
        or input_rows != analyzed_rows + excluded_rows
    ):
        raise ValueError("series population is invalid")


def build_series_chart_model(
    analysis_result: object,
    *,
    mark: str,
) -> tuple[dict[str, object], dict[str, object]]:
    """Build a fixed chart model from a validated neutral series result."""

    chart_type = _chart_type(mark)
    if not isinstance(analysis_result, (Mapping, bytes)):
        raise ValueError("analysis document is invalid")
    if isinstance(analysis_result, Mapping):
        analysis_id = analysis_result.get("analysis_id")
    else:
        import json
        try:
            decoded = json.loads(analysis_result.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("analysis document is invalid") from None
        analysis_id = decoded.get("analysis_id") if isinstance(decoded, Mapping) else None
    definitions = {
        "timeline.v1": ("timeline-result-v1.schema.json", "年次推移", SERIES_RENDER_MARKS),
        "growth.v1": ("growth-result-v1.schema.json", "増減率", (SERIES_LINE_MARK,)),
        "concentration.v1": (
            "concentration-result-v1.schema.json",
            "HHI集中度推移",
            (SERIES_LINE_MARK,),
        ),
    }
    try:
        result_schema, title, allowed_marks = definitions[analysis_id]
    except (KeyError, TypeError):
        raise ValueError("analysis document is incompatible") from None
    if mark not in allowed_marks:
        raise ValueError("series renderer mark is incompatible")
    result = coerce_analysis_result(
        analysis_result,
        analysis_id=str(analysis_id),
        result_variant="series",
        result_schema=result_schema,
    )
    data = result["data"]
    assert isinstance(data, dict)
    _validate_series_lengths(data)
    population = result["population"]
    _validate_series_semantics(data, population)

    model: dict[str, object] = {
        "chart_model_contract_version": "1.0.0",
        "chart_type": chart_type,
        "mark": mark,
        "analysis_result_sha256": sha256_bytes(canonical_json_bytes(result)),
        "title": title,
        "measure": deepcopy(data["measure"]),
        "x": list(data["x"]),
        "series": [
            {
                "label": item["label"],
                "values": list(item["values"]),
                "row_counts": list(item["row_counts"]),
                "is_other": item["is_other"],
            }
            for item in data["series"]
        ],
        "population": deepcopy(population),
        "warnings": list(result["warnings"]),
    }
    validate_schema(model, "categorical-chart-model-v1.schema.json")
    receipt = build_receipt(result, data, model, mark=mark)
    return deepcopy(model), deepcopy(receipt)


def build_series_render_spec(
    *,
    mark: str,
    x_count: int,
    series_count: int,
    palette: str | None = None,
) -> dict[str, object]:
    """Build the fixed categorical render spec for a series mark."""

    chart_type = _chart_type(mark)
    if (
        type(x_count) is not int
        or type(series_count) is not int
        or not 0 <= x_count <= 400
        or not 0 <= series_count <= 101
    ):
        raise ValueError("series render dimensions are invalid")
    renderer_kind = (
        "series.line.svg" if chart_type == "series.line" else "series.stacked-bar.svg"
    )
    spec = fixed_render_spec(
        renderer_kind=renderer_kind,
        render_profile_id=CATEGORICAL_RENDER_PROFILE_ID,
        palette=palette,
    )
    validate_schema(spec, "categorical-render-spec-v1.schema.json")
    return deepcopy(spec)


__all__ = (
    "CATEGORICAL_RENDER_PROFILE_ID",
    "SERIES_LINE_MARK",
    "SERIES_RENDER_MARKS",
    "SERIES_RENDER_PROFILE_ID",
    "SERIES_STACKED_BAR_MARK",
    "build_series_chart_model",
    "build_series_render_spec",
)
