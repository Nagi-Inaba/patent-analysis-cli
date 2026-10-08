"""Regression tests for PR33's independent presentation-contract review."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def _fixture(analysis_id):
    fixture = json.loads(
        (ROOT / "renderer/test/fixtures/advanced-models.json").read_text(encoding="utf-8")
    )
    return deepcopy(next(m for m in fixture["models"] if m["analysis_id"] == analysis_id))


@pytest.mark.parametrize(
    "analysis_id,field,value",
    [
        ("citation.v1", "x_year", False),
        ("citation.v1", "y_year", True),
        ("citation.v1", "x_label", "CAGR"),
        ("citation.v1", "y_label", "件数の合計"),
        ("entry-exit.v1", "x_year", False),
        ("entry-exit.v1", "y_year", False),
        ("entry-exit.v1", "size_label", "被引用件数"),
    ],
)
def test_public_model_schema_rejects_changed_analysis_axis_contract(analysis_id, field, value):
    schema = json.loads(
        (ROOT / "src/patent_analysis/schemas/advanced-chart-model-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validator = Draft202012Validator(schema)
    model = _fixture(analysis_id)
    validator.validate(model)
    model["projection"][field] = value
    assert list(validator.iter_errors(model)), "analysis-specific axes must be fixed"


@pytest.mark.parametrize(
    "analysis_id,category",
    [
        ("citation.v1", "active"),
        ("citation.v1", "inactive"),
        ("entry-exit.v1", "citation"),
        ("entry-exit.v1", "sustained_growth"),
    ],
)
def test_public_model_schema_rejects_cross_analysis_category(analysis_id, category):
    schema = json.loads(
        (ROOT / "src/patent_analysis/schemas/advanced-chart-model-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    model = _fixture(analysis_id)
    model["projection"]["points"][0]["category"] = category
    assert list(Draft202012Validator(schema).iter_errors(model))
