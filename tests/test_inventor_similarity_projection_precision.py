"""Cosine consistency must allow the declared exported-feature quantization."""

from copy import deepcopy

import pytest
from test_inventor_graph import obs

from patent_analysis.advanced_projection import project_advanced_data
from patent_analysis.inventor_profiles import technology_similarity
from patent_analysis.inventor_units import form_units


def similarity_data(feature="composition", person_weight="full", classification_weight="full"):
    rows = (
        obs("1", ("A", "B"), "2023", ("X",)),
        obs("2", ("B", "C"), "2024", ("Y",)),
        obs("3", ("A", "B"), "2024", ("X",)),
        obs("4", ("D",), None),
    )
    stats = technology_similarity(
        form_units(rows, unit="records"),
        rows,
        feature=feature,
        person_weight=person_weight,
        classification_weight=classification_weight,
    )
    return {"analysis_id": "inventor-similarity.v1", "statistics": stats}


def test_similarity_projection_accepts_real_rounded_composition_without_mutating_statistics():
    data = similarity_data()
    before = deepcopy(data)
    projection = project_advanced_data(data["analysis_id"], data)
    assert projection["kind"] == "inventor-scatter"
    assert {p["label"] for p in projection["points"]} == {"A", "B", "C"}
    assert [p["label"] for p in projection["unplottable"]] == ["D"]
    assert data == before


@pytest.mark.parametrize("feature", ["composition", "count", "tfidf"])
@pytest.mark.parametrize("person_weight", ["full", "fractional"])
@pytest.mark.parametrize("classification_weight", ["full", "fractional"])
def test_similarity_quantization_guard_accepts_real_feature_weight_combinations(
    feature,
    person_weight,
    classification_weight,
):
    data = similarity_data(feature, person_weight, classification_weight)
    before = deepcopy(data)
    result = project_advanced_data(data["analysis_id"], data)
    assert len(result["points"]) == 3 and len(result["unplottable"]) == 1
    assert data == before


@pytest.mark.parametrize("mutation", ["off_diagonal", "diagonal", "undefined", "boolean"])
def test_similarity_quantization_guard_still_rejects_inconsistent_cosine(mutation):
    data = similarity_data()
    pairs = data["statistics"]["similarities"]
    if mutation == "off_diagonal":
        edge = next(e for e in pairs if e["source"] != e["target"] and e["cosine"] is not None)
        edge["cosine"] -= 0.0001
    elif mutation == "diagonal":
        edge = next(e for e in pairs if e["source"] == e["target"] and e["cosine"] == 1)
        edge["cosine"] = 0.999999999999
    elif mutation == "undefined":
        next(e for e in pairs if e["cosine"] is None)["cosine"] = 0
    else:
        next(e for e in pairs if e["cosine"] is not None)["cosine"] = True
    with pytest.raises(ValueError, match="operands are inconsistent"):
        project_advanced_data(data["analysis_id"], data)
