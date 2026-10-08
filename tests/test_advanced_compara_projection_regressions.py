"""Reject structurally valid Compara results that contradict their operands."""

from __future__ import annotations

import json
from copy import deepcopy
from importlib.resources import files

import pytest
from jsonschema import Draft202012Validator

from patent_analysis.advanced_projection import project_advanced_data


def _result(a: int, b: int, difference: int) -> dict:
    result = {
        "schema_version": "1.0.0",
        "analysis_id": "compara.v1",
        "algorithm_version": "1.0.0",
        "population": {"input_rows": a + b, "visible_rows": a + b, "excluded_rows": 0},
        "contributions": a + b,
        "groups": {"a": "A", "b": "B"},
        "x": ["X"],
        "y": ["Y"],
        "cells": [{"x": "X", "y": "Y", "a_count": a, "b_count": b,
                   "difference": difference}],
    }
    schema = json.loads(
        files("patent_analysis").joinpath("schemas/compara-result-v1.schema.json")
        .read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(result)
    return result


@pytest.mark.parametrize(("a", "b", "difference"), [(5, 1, 0), (1, 5, 4), (0, 0, 1)])
def test_compara_rejects_schema_valid_inconsistent_difference(a, b, difference):
    data = _result(a, b, difference)
    original = deepcopy(data)
    with pytest.raises(ValueError, match="Compara difference"):
        project_advanced_data("compara.v1", data)
    assert data == original


@pytest.mark.parametrize(("a", "b", "difference"), [(5, 1, 4), (1, 5, -4), (2, 2, 0), (0, 0, 0)])
def test_compara_preserves_correct_signed_difference_without_mutation(a, b, difference):
    data = _result(a, b, difference)
    original = deepcopy(data)
    projection = project_advanced_data("compara.v1", data)
    assert projection["signed"] is True
    assert projection["cells"] == [{"x": 0, "y": 0, "value": difference, "share": None}]
    assert data == original


def test_compara_checks_every_cell_not_only_the_first():
    data = _result(5, 1, 4)
    data["x"].append("Z")
    data["cells"].append({"x": "Z", "y": "Y", "a_count": 5, "b_count": 1, "difference": 0})
    original = deepcopy(data)
    with pytest.raises(ValueError, match="Compara difference"):
        project_advanced_data("compara.v1", data)
    assert data == original


def test_compara_empty_result_remains_empty():
    data = _result(0, 0, 0)
    data.update(x=[], y=[], cells=[])
    projection = project_advanced_data("compara.v1", data)
    assert projection["cells"] == []
    assert projection["signed"] is True
