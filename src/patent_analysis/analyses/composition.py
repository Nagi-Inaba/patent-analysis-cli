"""Deterministic categorical composition analysis with explicit share semantics."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path

from patent_analysis.analyses._aggregation import (
    dedupe_rows,
    measure_rows,
    row_values,
    unique_aggregate_label,
    validate_measure,
)
from patent_analysis.analysis_inputs import prepare_records_population
from patent_analysis.normalization import NormalizedRow
from patent_analysis.population import PopulationResult

COMPOSITION_ALGORITHM_VERSION = "1.0.0"
OTHER_LABEL = "その他（上位外）"
MAX_TOP_N = 100
MAX_EXPANDED_CONTRIBUTIONS = 500_000


class CompositionBudgetError(ValueError):
    """Raised before a composition contribution would exceed the fixed budget."""


def _validate_parameters(parameters: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(parameters, Mapping):
        raise ValueError("composition parameters must be an object")
    allowed = {"role", "top_n", "include_other", "measure", "measure_role"}
    unknown = sorted(set(parameters) - allowed)
    if unknown:
        raise ValueError(f"unsupported composition parameters: {unknown}")

    role = parameters.get("role")
    if not isinstance(role, str) or not role.strip():
        raise ValueError("role must be a non-empty string")
    top_n = parameters.get("top_n", 10)
    if type(top_n) is not int or not 1 <= top_n <= MAX_TOP_N:
        raise ValueError("top_n must be an integer from 1 through 100")
    include_other = parameters.get("include_other", True)
    if type(include_other) is not bool:
        raise ValueError("include_other must be boolean")
    measure, measure_role = validate_measure(parameters)
    return {
        "role": role.strip(),
        "top_n": top_n,
        "include_other": include_other,
        "measure": measure,
        "measure_role": measure_role,
    }


def required_roles(parameters: Mapping[str, object]) -> tuple[str, ...]:
    validated = _validate_parameters(parameters)
    output = [str(validated["role"])]
    measure_role = validated["measure_role"]
    if isinstance(measure_role, str) and measure_role not in output:
        output.append(measure_role)
    return tuple(output)


def _shares(
    visible: list[tuple[str, tuple[NormalizedRow, ...], float | int]],
    *,
    mode: str,
) -> tuple[str, list[float]]:
    values = [float(value) for _, _, value in visible]
    if mode in {"count", "sum"} and all(value >= 0 for value in values):
        basis = "value"
        weights = values
    else:
        basis = "row_count"
        weights = [float(len(rows)) for _, rows, _ in visible]
    denominator = sum(weights)
    if denominator <= 0:
        return basis, [0.0 for _ in weights]
    return basis, [weight / denominator for weight in weights]


def analyze_composition(
    population: PopulationResult,
    parameters: Mapping[str, object],
) -> dict[str, object]:
    if not isinstance(population, PopulationResult):
        raise TypeError("population must be a PopulationResult")
    validated = _validate_parameters(parameters)
    role = str(validated["role"])
    mode = str(validated["measure"])
    measure_role = validated["measure_role"]
    assert measure_role is None or isinstance(measure_role, str)

    buckets: dict[str, list[NormalizedRow]] = defaultdict(list)
    blank_rows = 0
    contributions = 0
    for row in population.rows:
        labels = row_values(row, role)
        if not labels:
            blank_rows += 1
            continue
        if contributions + len(labels) > MAX_EXPANDED_CONTRIBUTIONS:
            raise CompositionBudgetError(
                f"expanded contributions exceed limit {MAX_EXPANDED_CONTRIBUTIONS}"
            )
        contributions += len(labels)
        for label in labels:
            buckets[label].append(row)

    ranked = sorted(
        (
            (
                label,
                tuple(bucket_rows),
                measure_rows(bucket_rows, mode=mode, measure_role=measure_role),
            )
            for label, bucket_rows in buckets.items()
        ),
        key=lambda item: (-float(item[2]), -len(item[1]), item[0]),
    )

    top_n = int(validated["top_n"])
    visible = list(ranked[:top_n])
    other_label = None
    if bool(validated["include_other"]) and len(ranked) > len(visible):
        other_label = unique_aggregate_label(OTHER_LABEL, buckets)
        other_rows = dedupe_rows(
            row
            for _, bucket_rows, _ in ranked[len(visible) :]
            for row in bucket_rows
        )
        visible.append(
            (
                other_label,
                other_rows,
                measure_rows(other_rows, mode=mode, measure_role=measure_role),
            )
        )

    share_basis, shares = _shares(visible, mode=mode)
    items = [
        {
            "label": label,
            "value": value,
            "row_count": len(bucket_rows),
            "share": share,
            "share_basis": share_basis,
            "is_other": label == other_label,
        }
        for (label, bucket_rows, value), share in zip(visible, shares, strict=True)
    ]

    input_rows = population.receipt.included_rows
    visible_rows = input_rows - blank_rows
    return {
        "schema_version": "1.0.0",
        "analysis_id": "composition.v1",
        "algorithm_version": COMPOSITION_ALGORITHM_VERSION,
        "measure": {"mode": mode, "role": measure_role},
        "items": items,
        "population": {
            "input_rows": input_rows,
            "visible_rows": visible_rows,
            "blank_role_rows": blank_rows,
            "excluded_rows": blank_rows,
        },
        "contributions": contributions,
        "limits": {
            "max_top_n": MAX_TOP_N,
            "max_expanded_contributions": MAX_EXPANDED_CONTRIBUTIONS,
        },
    }


def analyze_composition_csv(
    source: str | Path,
    spec: Mapping[str, object],
    *,
    allowed_root: str | Path,
) -> dict[str, object]:
    """Run the shared records pipeline and return the common v2 result envelope."""

    if not isinstance(spec, Mapping) or spec.get("analysis_id") != "composition.v1":
        raise ValueError("composition analysis spec is invalid")
    parameters = spec.get("parameters")
    if not isinstance(parameters, Mapping):
        raise ValueError("composition parameters must be an object")
    roles = required_roles(parameters)
    dataset, population = prepare_records_population(
        source,
        spec,
        allowed_root=allowed_root,
        analysis_roles=roles,
    )
    data = analyze_composition(population, parameters)
    analyzed_rows = int(data["population"]["visible_rows"])
    return {
        "analysis_id": "composition.v1",
        "algorithm_version": COMPOSITION_ALGORITHM_VERSION,
        "result_variant": "composition",
        "population": {
            "input_rows": dataset.manifest.input_rows,
            "analyzed_rows": analyzed_rows,
            "excluded_rows": dataset.manifest.input_rows - analyzed_rows,
        },
        "data": data,
        "warnings": [],
        **population.receipt.analysis_metadata(),
    }
