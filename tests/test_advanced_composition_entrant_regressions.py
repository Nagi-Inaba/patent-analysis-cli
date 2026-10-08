"""Schema-valid composition and entrant results must preserve declared semantics."""
from __future__ import annotations

import json
from copy import deepcopy
from importlib.resources import files

import pytest
from jsonschema import Draft202012Validator

from patent_analysis.advanced_projection import project_advanced_data


def _validate(data):
    schema_name = data["analysis_id"].removesuffix(".v1") + "-result-v1.schema.json"
    schema = json.loads(
        files("patent_analysis").joinpath("schemas", schema_name).read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(data)
    return data


def _composition(counts, denominator, shares=None):
    if shares is None:
        shares = [count / denominator if denominator else 0 for count in counts]
    return _validate({
        "schema_version": "1.0.0", "algorithm_version": "1.0.0",
        "analysis_id": "matrix-composition.v1",
        "population": {"input_rows": denominator, "visible_rows": denominator, "excluded_rows": 0},
        "contributions": denominator, "cell": {"x": "X", "y": "Y"},
        "cell_rows": denominator, "category_memberships": denominator,
        "share_basis": "category_memberships",
        "items": [
            {"label": f"C{index}", "count": count, "share": share}
            for index, (count, share) in enumerate(zip(counts, shares, strict=True))
        ],
    })


@pytest.mark.parametrize(("counts", "denominator", "shares"), [
    ([8, 8], 10, [0.8, 0.8]),
    ([6, 5], 10, [0.4, 0.4]),
    ([4, 4], 10, [0.8, 0.8]),
    ([0, 0], 0, [0.8, 0.8]),
])
def test_composition_rejects_aggregate_excess(counts, denominator, shares):
    data = _composition(counts, denominator, shares)
    before = deepcopy(data)
    with pytest.raises(ValueError, match="Composition"):
        project_advanced_data(data["analysis_id"], data)
    assert data == before


@pytest.mark.parametrize(("counts", "denominator"), [
    ([2, 3], 10), ([3, 7], 10), ([1] * 10, 10), ([0, 0], 0), ([], 0),
])
def test_composition_preserves_subset_full_zero_and_empty(counts, denominator):
    data = _composition(counts, denominator)
    before = deepcopy(data)
    projection = project_advanced_data(data["analysis_id"], data)
    assert [item["value"] for item in projection["items"]] == counts
    assert [item["denominator"] for item in projection["items"]] == [denominator] * len(counts)
    assert [item["share"] for item in projection["items"]] == [
        item["share"] for item in data["items"]
    ]
    assert data == before


def _entrants(years):
    size = len(years)
    return _validate({
        "schema_version": "1.0.0", "algorithm_version": "1.0.0",
        "analysis_id": "new-entrants.v1", "as_of_year": 2023,
        "population": {"input_rows": size, "visible_rows": size, "excluded_rows": 0},
        "contributions": size,
        "applicants": [
            {"label": f"A{i}", "first_year": year, "row_count": 1,
             "classification_memberships": 1}
            for i, year in enumerate(years)
        ],
        "classifications": ["X"] if years else [],
        "cells": [
            {"applicant": f"A{i}", "classification": "X", "count": 1, "share": 1.0}
            for i in range(size)
        ],
        "share_basis": "all_classification_memberships_per_applicant",
    })


@pytest.mark.parametrize("years", [[2022], [2023, 2022], [2022, 2024]])
def test_entrants_reject_first_observation_before_cutoff(years):
    data = _entrants(years)
    before = deepcopy(data)
    with pytest.raises(ValueError, match="entrant"):
        project_advanced_data(data["analysis_id"], data)
    assert data == before


@pytest.mark.parametrize("years", [[2023], [2023, 2024], []])
def test_entrants_accept_inclusive_cutoff_later_years_and_empty(years):
    data = _entrants(years)
    before = deepcopy(data)
    projection = project_advanced_data(data["analysis_id"], data)
    assert projection["y"] == [f"A{i}" for i in range(len(years))]
    assert len(projection["cells"]) == len(years)
    assert data == before
