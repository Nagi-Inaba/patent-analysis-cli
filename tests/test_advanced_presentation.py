"""Portable projection checks, distinct from native API/Windows rendering tests."""

from __future__ import annotations

import importlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

NAMES = (
    "growth_quadrant",
    "entry_exit",
    "citation",
    "matrix_composition",
    "new_entrants",
    "compara",
    "cooccurrence",
    "network",
    "uniqueness",
    "shared_involvement",
)
ROOT = Path(__file__).resolve().parents[1]
ROWS = [
    {
        "year": ("2020",),
        "group": ("A",),
        "item": ("P", "Q"),
        "x": ("X",),
        "y": ("Y",),
        "cites": ("12",),
    },
    {
        "year": ("2023",),
        "group": ("A", "B"),
        "item": ("Q",),
        "x": ("Z",),
        "y": ("Y",),
        "cites": ("0",),
    },
    {
        "year": ("2024",),
        "group": ("B",),
        "item": ("Q", "R"),
        "x": ("Z",),
        "y": ("W",),
        "cites": ("4",),
    },
]


def projection_module():
    assert importlib.util.find_spec("patent_analysis.advanced_projection") is not None, (
        "advanced presentation projection is not implemented"
    )
    return importlib.import_module("patent_analysis.advanced_projection")


def native(name, rows=None):
    module = importlib.import_module("patent_analysis.analyses." + name)
    spec = json.loads(
        (
            ROOT / "examples/advanced" / (module.ANALYSIS_ID.removesuffix(".v1") + ".json")
        ).read_text(encoding="utf-8")
    )
    return module.ANALYSIS_ID, module.compute(ROWS if rows is None else rows, spec["parameters"])


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("empty", [False, True])
def test_every_analysis_has_a_closed_nonmutating_projection(name, empty):
    projection = projection_module()
    analysis_id, data = native(name, [] if empty else ROWS)
    before = deepcopy(data)
    first = projection.project_advanced_data(analysis_id, data)
    assert first == projection.project_advanced_data(analysis_id, data)
    assert data == before
    assert first["kind"] in {"scatter", "quadrant", "heatmap", "bars", "network"}
    json.dumps(first, allow_nan=False)
    schema = json.loads(
        (ROOT / "src/patent_analysis/schemas/advanced-projection-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(first)
    assert list(Draft202012Validator(schema).iter_errors({**first, "arbitrary_options": {}}))


def test_quadrant_undefined_values_are_not_invented_plot_coordinates():
    projection = projection_module()
    analysis_id, data = native("growth_quadrant")
    model = projection.project_advanced_data(analysis_id, data)
    unmeasurable = {
        p["label"]
        for p in data["points"]
        if p["long"]["rate_percent"] is None or p["short"]["rate_percent"] is None
    }
    assert {p["label"] for p in model["unplottable"]} == unmeasurable
    assert not (unmeasurable & {p["label"] for p in model["points"]})
    for p in model["points"]:
        original = next(q for q in data["points"] if q["label"] == p["label"])
        assert (p["x"], p["y"], p["size"]) == (
            original["long"]["rate_percent"],
            original["short"]["rate_percent"],
            original["total_count"],
        )


def test_citation_uses_synthetic_point_ids_not_duplicated_labels_as_identity():
    projection = projection_module()
    row = {**ROWS[0], "cites": ("0",)}
    analysis_id, data = native("citation", [row, deepcopy(row)])
    model = projection.project_advanced_data(analysis_id, data)
    assert len(model["points"]) == 2
    assert len({p["id"] for p in model["points"]}) == 2
    assert [p["size"] for p in model["points"]] == [0, 0]
    assert [p["y"] for p in model["points"]] == [0, 0]


def test_compara_preserves_signed_values_and_explicit_groups():
    projection = projection_module()
    analysis_id, data = native("compara")
    model = projection.project_advanced_data(analysis_id, data)
    assert model["signed"] is True
    assert [c["value"] for c in model["cells"]] == [c["difference"] for c in data["cells"]]
    assert "A" in model["context"] and "B" in model["context"]


def test_cooccurrence_symmetry_and_zero_diagonal_survive_projection():
    projection = projection_module()
    analysis_id, data = native("cooccurrence")
    model = projection.project_advanced_data(analysis_id, data)
    cells = {(c["x"], c["y"]): c["value"] for c in model["cells"]}
    assert all(cells[x, y] == cells[y, x] for x, y in cells)
    assert all(cells[x, x] == 0 for x in range(len(model["x"])))


def test_grouped_bars_retain_full_population_denominator_and_record_involvement():
    projection = projection_module()
    for name, count, rate in (
        ("uniqueness", "unique_item_count", "uniqueness_rate"),
        ("shared_involvement", "shared_item_count", "shared_rate"),
    ):
        analysis_id, data = native(name)
        model = projection.project_advanced_data(analysis_id, data)
        for item, original in zip(model["items"], data["groups"], strict=True):
            assert item["value"] == original[count]
            assert item["denominator"] == original["total_item_count"]
            assert item["share"] == original[rate]
            assert item["record_count"] == original["record_count"]
            assert item["involvement_count"] == original.get("involvement_record_count")


def test_network_identity_is_deterministic_and_no_self_links_are_created():
    projection = projection_module()
    analysis_id, data = native("network")
    model = projection.project_advanced_data(analysis_id, data)
    labels = [node["label"] for node in model["nodes"]]
    assert len(set(labels)) == len(labels)
    for edge, original in zip(model["edges"], data["edges"], strict=True):
        assert edge["source"] != edge["target"]
        assert labels[edge["source"]] == original["source"]
        assert labels[edge["target"]] == original["target"]
        assert edge["value"] == original["count"]
