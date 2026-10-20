"""Deterministic count-only matrix analysis over canonical normalized records."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from patent_analysis.analyses._aggregation import unique_aggregate_label
from patent_analysis.analysis_inputs import _project_resolution_spec, records_population_spec
from patent_analysis.column_resolution import resolve_roles
from patent_analysis.dataset_v2 import read_dataset_v2
from patent_analysis.normalization import (
    CLASSIFICATION_LEVELS,
    NormalizationConfig,
    normalize_dataset,
)
from patent_analysis.population import apply_population, family_roles

AXIS_OTHER_LABEL = "その他（上位外）"
PIE_BLANK_LABEL = "(空白)"
DEFAULT_PIE_LIMIT = 5
MIN_PIE_LIMIT = 2
MAX_PIE_LIMIT = 8
MATRIX_ALGORITHM_VERSION = "1.0.0"
MAX_VISIBLE_CELLS = 400
MAX_EXPANDED_CONTRIBUTIONS = 2_000_000


class MatrixBudgetError(ValueError):
    """Raised when a closed matrix operation budget would be exceeded."""


def _stable_unique(values: Iterable[object]) -> tuple[str, ...]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        output.append(text)
    return tuple(output)


def _row_values(row: object, role: str) -> tuple[str, ...]:
    values_method = getattr(row, "values", None)
    if callable(values_method):
        return _stable_unique(values_method(role))

    candidates: list[object] = []
    if isinstance(row, Mapping):
        nested = row.get("values")
        if isinstance(nested, Mapping):
            candidates.append(nested.get(role))
        candidates.append(row.get(role))
    for attribute in ("values", "values_by_role", "derived_values", "roles"):
        value = getattr(row, attribute, None)
        if isinstance(value, Mapping):
            candidates.append(value.get(role))

    for candidate in candidates:
        if candidate is None:
            continue
        if isinstance(candidate, str):
            return _stable_unique((candidate,))
        if isinstance(candidate, Sequence):
            return _stable_unique(candidate)
        return _stable_unique((candidate,))
    return ()


def _validate_parameters(parameters: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(parameters, Mapping):
        raise ValueError("matrix parameters must be an object")
    allowed = {
        "x_role",
        "y_role",
        "x_classification_level",
        "y_classification_level",
        "x_limit",
        "y_limit",
        "include_axis_other",
        "measure",
        "pie_role",
        "pie_classification_level",
        "pie_limit",
    }
    unknown = sorted(set(parameters) - allowed)
    if unknown:
        raise ValueError(f"unsupported matrix parameters: {unknown}")

    x_role = parameters.get("x_role")
    y_role = parameters.get("y_role")
    if not isinstance(x_role, str) or not x_role.strip():
        raise ValueError("x_role must be a non-empty string")
    if not isinstance(y_role, str) or not y_role.strip():
        raise ValueError("y_role must be a non-empty string")

    x_limit = parameters.get("x_limit", 10)
    y_limit = parameters.get("y_limit", 10)
    for name, value in (("x_limit", x_limit), ("y_limit", y_limit)):
        if type(value) is not int or not 1 <= value <= 100:
            raise ValueError(f"{name} must be an integer from 1 through 100")

    include_axis_other = parameters.get("include_axis_other", True)
    if type(include_axis_other) is not bool:
        raise ValueError("include_axis_other must be boolean")
    if parameters.get("measure", "count") != "count":
        raise ValueError("matrix.v1 supports only measure=count")

    pie_role: str | None = None
    if "pie_role" in parameters:
        pie_role = parameters["pie_role"]
        if not isinstance(pie_role, str) or not pie_role.strip():
            raise ValueError("pie_role must be a non-empty string")
        pie_role = pie_role.strip()
    pie_limit = DEFAULT_PIE_LIMIT
    if "pie_limit" in parameters:
        pie_limit = parameters["pie_limit"]
        if type(pie_limit) is not int or not MIN_PIE_LIMIT <= pie_limit <= MAX_PIE_LIMIT:
            raise ValueError(
                f"pie_limit must be an integer from {MIN_PIE_LIMIT} through {MAX_PIE_LIMIT}"
            )
    if pie_role is None:
        for option in ("pie_limit", "pie_classification_level"):
            if option in parameters:
                raise ValueError(f"{option} requires pie_role")

    axis_roles = {"x": x_role, "y": y_role, **({"pie": pie_role} if pie_role else {})}
    classification_levels: dict[str, str] = {}
    for axis, role in axis_roles.items():
        value = parameters.get(f"{axis}_classification_level")
        if value is not None:
            if not isinstance(value, str) or value not in CLASSIFICATION_LEVELS:
                raise ValueError(f"unsupported {axis}_classification_level")
            existing = classification_levels.get(role)
            if existing is not None and existing != value:
                raise ValueError("one role cannot use two classification levels")
            classification_levels[role] = value

    validated: dict[str, object] = {
        "x_role": x_role.strip(),
        "y_role": y_role.strip(),
        "x_limit": x_limit,
        "y_limit": y_limit,
        "include_axis_other": include_axis_other,
        "measure": "count",
        "classification_levels": classification_levels,
    }
    if pie_role is not None:
        validated["pie_role"] = pie_role
        validated["pie_limit"] = pie_limit
    return validated


def _rank_axis(rows: Sequence[tuple[str, ...]], limit: int) -> tuple[str, ...]:
    counts: Counter[str] = Counter()
    for values in rows:
        counts.update(_stable_unique(values))
    return tuple(sorted(counts, key=lambda label: (-counts[label], label))[:limit])


def _project_axis(
    values: tuple[str, ...],
    top: frozenset[str],
    *,
    include_other: bool,
    other_label: str,
) -> tuple[str, ...]:
    projected = (
        value if value in top else other_label
        for value in values
        if value in top or include_other
    )
    return _stable_unique(projected)


def _axis_categories(
    labels: tuple[str, ...],
    rows: Sequence[tuple[str, ...]],
    top: frozenset[str],
    other_label: str,
) -> list[dict[str, object]]:
    categories: list[dict[str, object]] = []
    for label in labels:
        if label == other_label:
            count = sum(any(value not in top for value in values) for values in rows)
        else:
            count = sum(label in values for values in rows)
        categories.append(
            {
                "label": label,
                "count": count,
                "is_other": label == other_label,
            }
        )
    return categories


def _pie_composition(
    visible: Sequence[tuple[int, tuple[str, ...], tuple[str, ...]]],
    pie_values: Sequence[tuple[str, ...]],
    x_index: Mapping[str, int],
    y_index: Mapping[str, int],
    limit: int,
    role: str,
) -> tuple[dict[str, object], dict[tuple[int, int], list[dict[str, object]]]]:
    """Split every visible cell by the pie role's top values.

    Only rows that reach a cell take part. A row with several pie values counts once per
    value, so a cell's slices can add up to more than its row count. Values outside the top
    `limit` are folded into one aggregate slice that never reuses a source label.
    """

    source = [pie_values[position] for position, _, _ in visible]
    source_labels = {value for values in source for value in values}
    blank_label = unique_aggregate_label(PIE_BLANK_LABEL, source_labels)
    rows = [values or (blank_label,) for values in source]

    counts: Counter[str] = Counter()
    for values in rows:
        counts.update(values)
    ranked = tuple(sorted(counts, key=lambda label: (-counts[label], label)))
    top = frozenset(ranked[:limit])
    other_label = unique_aggregate_label(AXIS_OTHER_LABEL, counts)
    has_other = len(ranked) > limit
    legend = ranked[:limit] + ((other_label,) if has_other else ())

    categories: list[dict[str, object]] = [
        {"label": label, "count": counts[label], "is_other": False} for label in ranked[:limit]
    ]
    if has_other:
        categories.append(
            {
                "label": other_label,
                "count": sum(any(value not in top for value in values) for values in rows),
                "is_other": True,
            }
        )

    slice_counts: dict[tuple[int, int], Counter[str]] = {}
    expanded = 0
    for (_, projected_x, projected_y), values in zip(visible, rows, strict=True):
        projected = _stable_unique(value if value in top else other_label for value in values)
        for y_label in projected_y:
            for x_label in projected_x:
                bucket = slice_counts.setdefault((y_index[y_label], x_index[x_label]), Counter())
                for label in projected:
                    if expanded >= MAX_EXPANDED_CONTRIBUTIONS:
                        raise MatrixBudgetError(
                            f"expanded pie contributions exceed limit {MAX_EXPANDED_CONTRIBUTIONS}"
                        )
                    expanded += 1
                    bucket[label] += 1

    slices = {
        key: [{"label": label, "count": bucket[label]} for label in legend if bucket[label]]
        for key, bucket in slice_counts.items()
    }
    return {"role": role, "categories": categories}, slices


def analyze_matrix(
    population: object,
    parameters: Mapping[str, object],
) -> dict[str, object]:
    """Aggregate one records-only population into a deterministic sparse matrix."""

    validated = _validate_parameters(parameters)
    x_role = str(validated["x_role"])
    y_role = str(validated["y_role"])
    rows = tuple(getattr(population, "rows", ()))
    axis_rows = tuple((_row_values(row, x_role), _row_values(row, y_role)) for row in rows)
    eligible = tuple(
        (x_values, y_values) for x_values, y_values in axis_rows if x_values and y_values
    )

    x_ranked = _rank_axis([item[0] for item in eligible], int(validated["x_limit"]))
    y_ranked = _rank_axis([item[1] for item in eligible], int(validated["y_limit"]))
    x_top = frozenset(x_ranked)
    y_top = frozenset(y_ranked)
    include_other = bool(validated["include_axis_other"])

    x_has_other = include_other and any(
        any(value not in x_top for value in x_values) for x_values, _ in eligible
    )
    y_has_other = include_other and any(
        any(value not in y_top for value in y_values) for _, y_values in eligible
    )
    x_other_label = unique_aggregate_label(
        AXIS_OTHER_LABEL, (value for x_values, _ in eligible for value in x_values)
    )
    y_other_label = unique_aggregate_label(
        AXIS_OTHER_LABEL, (value for _, y_values in eligible for value in y_values)
    )
    x_labels = x_ranked + ((x_other_label,) if x_has_other else ())
    y_labels = y_ranked + ((y_other_label,) if y_has_other else ())
    if len(x_labels) * len(y_labels) > MAX_VISIBLE_CELLS:
        raise MatrixBudgetError(f"visible cells exceed limit {MAX_VISIBLE_CELLS}")

    x_index = {label: index for index, label in enumerate(x_labels)}
    y_index = {label: index for index, label in enumerate(y_labels)}
    cells: Counter[tuple[int, int]] = Counter()
    visible_rows = 0
    blank_axis_rows = 0
    axis_other_rows = 0
    contributions = 0
    pie_role = validated.get("pie_role")
    # (row position, projected x labels, projected y labels) for every row that reaches a cell.
    visible: list[tuple[int, tuple[str, ...], tuple[str, ...]]] = []

    for position, (x_values, y_values) in enumerate(axis_rows):
        if not x_values or not y_values:
            blank_axis_rows += 1
            continue
        has_other = any(value not in x_top for value in x_values) or any(
            value not in y_top for value in y_values
        )
        projected_x = _project_axis(
            x_values, x_top, include_other=include_other, other_label=x_other_label
        )
        projected_y = _project_axis(
            y_values, y_top, include_other=include_other, other_label=y_other_label
        )
        if not projected_x or not projected_y:
            continue
        visible_rows += 1
        if pie_role is not None:
            visible.append((position, projected_x, projected_y))
        if include_other and has_other:
            axis_other_rows += 1
        for y_label in projected_y:
            for x_label in projected_x:
                if contributions >= MAX_EXPANDED_CONTRIBUTIONS:
                    raise MatrixBudgetError(
                        f"expanded contributions exceed limit {MAX_EXPANDED_CONTRIBUTIONS}"
                    )
                contributions += 1
                cells[(y_index[y_label], x_index[x_label])] += 1

    pie_document: dict[str, object] | None = None
    slices_by_cell: dict[tuple[int, int], list[dict[str, object]]] = {}
    if pie_role is not None:
        pie_document, slices_by_cell = _pie_composition(
            visible,
            [_row_values(row, str(pie_role)) for row in rows],
            x_index,
            y_index,
            int(validated["pie_limit"]),
            str(pie_role),
        )
    cell_documents = [
        {
            "x_index": x_position,
            "y_index": y_position,
            "x_label": x_labels[x_position],
            "y_label": y_labels[y_position],
            "value": count,
            "row_count": count,
            **(
                {"slices": slices_by_cell[(y_position, x_position)]}
                if pie_document is not None
                else {}
            ),
        }
        for (y_position, x_position), count in sorted(cells.items())
    ]
    document: dict[str, object] = {
        "schema_version": "1.0.0",
        "analysis_id": "matrix.v1",
        "algorithm_version": MATRIX_ALGORITHM_VERSION,
        "measure": "count",
        "x_axis": {
            "role": x_role,
            "categories": _axis_categories(
                x_labels,
                [item[0] for item in eligible],
                x_top,
                x_other_label,
            ),
        },
        "y_axis": {
            "role": y_role,
            "categories": _axis_categories(
                y_labels,
                [item[1] for item in eligible],
                y_top,
                y_other_label,
            ),
        },
        "cells": cell_documents,
        "population": {
            "input_rows": len(rows),
            "visible_rows": visible_rows,
            "blank_axis_rows": blank_axis_rows,
            "axis_other_rows": axis_other_rows,
            "excluded_rows": len(rows) - visible_rows,
        },
        "contributions": contributions,
        "limits": {
            "max_visible_cells": MAX_VISIBLE_CELLS,
            "max_expanded_contributions": MAX_EXPANDED_CONTRIBUTIONS,
        },
    }
    if pie_document is not None:
        document["pie"] = pie_document
    return document


def _stable_roles(values: Iterable[str]) -> tuple[str, ...]:
    return _stable_unique(values)


def _population_core_spec(value: object) -> dict[str, object]:
    return records_population_spec(value)[0]


def analyze_matrix_csv(
    source: str | Path,
    spec: Mapping[str, object],
    *,
    allowed_root: str | Path,
) -> dict[str, object]:
    """Run the canonical v2 CSV pipeline and return the common result document."""

    if not isinstance(spec, Mapping):
        raise ValueError("matrix analysis spec must be an object")
    parameters_value = spec.get("parameters")
    if not isinstance(parameters_value, Mapping):
        raise ValueError("matrix parameters must be an object")
    parameters = _validate_parameters(parameters_value)

    normalization_value = spec.get("normalization")
    if not isinstance(normalization_value, Mapping) or normalization_value.get("profiles") != []:
        raise ValueError("matrix.v1 accepts no source-product normalization profile")
    population_value = spec.get("population")
    population_spec, filter_roles = records_population_spec(population_value)
    roles = _stable_roles(
        [
            str(parameters["x_role"]),
            str(parameters["y_role"]),
            *([str(parameters["pie_role"])] if "pie_role" in parameters else []),
            *filter_roles,
        ]
    )
    dataset = read_dataset_v2(source, allowed_root=allowed_root)
    resolution_value = spec.get("resolution")
    if not isinstance(resolution_value, Mapping):
        raise ValueError("matrix resolution must be an object")
    selection_roles = family_roles(population_spec)
    required = _stable_roles((*roles, *selection_roles))
    resolution = resolve_roles(
        dataset.manifest,
        _project_resolution_spec(resolution_value, required),
        required_roles=required,
    )
    normalized = normalize_dataset(
        dataset,
        resolution,
        NormalizationConfig(
            roles=roles,
            multi_value_policy="all",
            classification_levels=dict(parameters["classification_levels"]),
        ),
    )
    population = apply_population(
        normalized, population_spec,
        source_role_ordinals={
            role: resolution.mapping[role].source_header_ordinal for role in selection_roles
        },
    )
    aggregation_parameters = {
        key: value for key, value in parameters.items() if key != "classification_levels"
    }
    data = analyze_matrix(population, aggregation_parameters)
    analyzed_rows = int(data["population"]["visible_rows"])
    return {
        "analysis_id": "matrix.v1",
        "algorithm_version": MATRIX_ALGORITHM_VERSION,
        "result_variant": "matrix",
        "population": {
            "input_rows": dataset.manifest.input_rows,
            "analyzed_rows": analyzed_rows,
            "excluded_rows": dataset.manifest.input_rows - analyzed_rows,
        },
        "data": data,
        "warnings": [],
        **population.receipt.analysis_metadata(),
    }
