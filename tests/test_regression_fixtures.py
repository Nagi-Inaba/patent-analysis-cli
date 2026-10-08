"""Frozen numerical and normalization regressions, independent of Git history."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from pathlib import Path

import pytest

from patent_analysis.analysis import analyze_csv
from patent_analysis.canonical_v2 import canonical_json_bytes
from patent_analysis.normalization import NormalizedRow
from patent_analysis.population import PopulationReceipt, PopulationResult

FIXTURES = Path(__file__).parent / "fixtures" / "regression"


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _native_population_projection(
    case_input: Mapping[str, object],
) -> list[int]:
    from patent_analysis.normalization import (
        NormalizationReceipt,
        NormalizedDataset,
        NormalizedRow,
    )
    from patent_analysis.population import apply_population

    raw_rows = case_input["rows"]
    assert isinstance(raw_rows, list)
    rows: list[NormalizedRow] = []
    requested_roles: list[str] = []
    contributions = 0
    for raw_row in raw_rows:
        assert isinstance(raw_row, Mapping)
        raw_values = raw_row["values_by_role"]
        assert isinstance(raw_values, Mapping)
        values_by_role: dict[str, tuple[str, ...]] = {}
        for role, values in raw_values.items():
            assert isinstance(role, str)
            assert isinstance(values, list)
            converted = tuple(str(value) for value in values)
            values_by_role[role] = converted
            contributions += len(converted)
            if role not in requested_roles:
                requested_roles.append(role)
        source_fields = raw_row["source_fields"]
        assert isinstance(source_fields, list)
        rows.append(
            NormalizedRow(
                source_ordinal=int(raw_row["source_ordinal"]),
                source_fields=tuple(str(value) for value in source_fields),
                values_by_role=values_by_role,
            )
        )
    row_documents = [row.to_dict() for row in rows]
    receipt = NormalizationReceipt(
        normalization_contract_version="1.0.0",
        source_input_sha256="1" * 64,
        resolved_role_mapping_sha256="2" * 64,
        requested_roles=tuple(requested_roles),
        multi_value_policy="all",
        classification_levels={},
        input_rows=len(rows),
        output_rows=len(rows),
        normalized_contributions=contributions,
        normalized_row_stream_sha256=_canonical_sha256(row_documents),
    )
    spec = case_input["spec"]
    assert isinstance(spec, Mapping)
    result = apply_population(
        NormalizedDataset(rows=tuple(rows), receipt=receipt),
        spec,
    )
    return [row.source_ordinal for row in result.rows]


def _native_case_projection(
    case: Mapping[str, object],
) -> object:
    from patent_analysis.normalization import (
        derive_classification_values,
        extract_year,
        normalize_applicant,
        split_patent_values,
    )

    operation = case["operation"]
    case_input = case["input"]
    assert isinstance(case_input, Mapping)
    if operation == "split_patent_values":
        return list(
            split_patent_values(
                str(case_input["raw"]),
                role=str(case_input["role"]),
            )
        )
    if operation == "derive_classification_values":
        values = case_input["values"]
        assert isinstance(values, list)
        return list(
            derive_classification_values(
                tuple(str(value) for value in values),
                level=str(case_input["level"]),
            )
        )
    if operation == "normalize_applicant":
        return normalize_applicant(str(case_input["value"]))
    if operation == "extract_year":
        return extract_year(str(case_input["value"]))
    return _native_population_projection(case_input)


def _same(left: object, right: object) -> bool:
    if type(left) in (int, float) and type(right) in (int, float):
        return math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _same(a, b) for a, b in zip(left, right, strict=True)
        )
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(_same(left[k], right[k]) for k in left)
    return type(left) is type(right) and left == right


def _native(analysis_id: str, cases: list[dict[str, object]]) -> list[object]:
    from patent_analysis.analyses.concentration import analyze_concentration
    from patent_analysis.analyses.growth import analyze_growth
    from patent_analysis.analyses.lifecycle import analyze_lifecycle

    functions = {
        "growth": analyze_growth,
        "concentration": analyze_concentration,
        "lifecycle": analyze_lifecycle,
    }
    output: list[object] = []
    for case in cases:
        rows = tuple(
            NormalizedRow(
                source_ordinal=index + 1,
                source_fields=(),
                values_by_role={"year": (year,), "category": tuple(labels)},
            )
            for index, (year, labels) in enumerate(case["rows"])
        )
        receipt = PopulationReceipt(
            "1.0.0", "a" * 64, "b" * 64, "records", 0, len(rows), len(rows), 0
        )
        result = functions[analysis_id](PopulationResult(rows, receipt), case["parameters"])
        if analysis_id == "growth":
            output.append(
                [
                    {
                        key: item[key]
                        for key in (
                            "label",
                            "values",
                            "growth_rate",
                            "growth_state",
                        )
                    }
                    for item in result["series"]
                ]
            )
        elif analysis_id == "concentration":
            values = result["series"][0]["values"] if result["series"] else []
            output.append(
                [
                    {"year": year, "hhi": value}
                    for year, value in zip(result["x"], values, strict=True)
                ]
            )
        else:
            output.append(result["points"])
    return output


@pytest.mark.parametrize(
    "case",
    json.loads((FIXTURES / "normalization.json").read_text(encoding="utf-8")),
    ids=lambda case: case["id"],
)
def test_normalization_regression_fixture(case: dict) -> None:
    assert _native_case_projection(case) == case["expected"]


@pytest.mark.parametrize("analysis_id", ["growth", "concentration", "lifecycle"])
def test_series_points_regression_fixture(analysis_id: str) -> None:
    fixture = FIXTURES / analysis_id
    cases = json.loads((fixture / "cases.json").read_text(encoding="utf-8"))
    expected = json.loads((fixture / "expected.json").read_text(encoding="utf-8"))
    assert cases and len(cases) == len(expected)
    assert _same(_native(analysis_id, cases), expected)


def test_ranking_regression_fixture() -> None:
    fixture = FIXTURES / "ranking"
    spec = json.loads((fixture / "spec.json").read_text(encoding="utf-8"))
    expected = json.loads((fixture / "expected.json").read_text(encoding="utf-8"))
    actual = analyze_csv("input.csv", spec, allowed_root=fixture)["result"]
    assert canonical_json_bytes(actual) == canonical_json_bytes(expected)
