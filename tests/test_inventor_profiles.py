from dataclasses import replace

import pytest
from test_inventor_graph import obs

from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_profiles import technology_profiles, technology_similarity
from patent_analysis.inventor_units import form_units


def test_family_witnessed_incidence_fractional_reference_and_missing():
    rows = (
        obs("1", ("A", "B"), codes=("X", "Y"), family_id="f"),
        obs("2", ("B", "C"), codes=("Z",), family_id="f"),
        obs("3", ("D",), family_id="g"),
    )
    units = form_units(rows, unit="family")
    result = technology_profiles(
        units, rows, person_weight="fractional", classification_weight="fractional"
    )
    cells = {(c["person_token"], c["classification"][1]): c for c in result["cells"]}
    assert ('["id","A"]', "Z") not in cells
    assert ('["id","C"]', "X") not in cells
    assert cells['["id","A"]', "X"]["count"]["denominator"] == "6"
    assert cells['["id","B"]', "Z"]["count"]["denominator"] == "9"
    assert cells['["id","A"]', "X"]["share"] == 0.5
    assert cells['["id","A"]', "X"]["relative_specialization"] == pytest.approx(1.8)
    assert result["profiles"][0]["entropy"] == 1.0
    assert result["profiles"][0]["hhi"] == 0.5
    assert result["profiles"][0]["predominant_classification"] == ["IPC", "X"]
    assert result["profiles"][3]["entropy"] is None
    assert result["profiles"][3]["undefined_reason"] == "missing_classification"
    assert result["coverage"]["classification_mass"]["value"] == 1.0
    assert result == technology_profiles(
        units[::-1], rows[::-1], person_weight="fractional", classification_weight="fractional"
    )
    with pytest.raises(DatasetInputError):
        technology_profiles(units, rows, classification_weight="bad")


@pytest.mark.parametrize("feature", ["composition", "count", "tfidf"])
def test_cosine_finite_symmetric_shared_explanation_zero_not_origin(feature):
    rows = (
        obs("1", ("A",), codes=("X",)),
        obs("2", ("B",), codes=("Y",)),
        obs("3", ("C",), codes=("X",)),
        obs("4", ("D",)),
    )
    units = form_units(rows, unit="records")
    result = technology_similarity(units, rows, feature=feature, co_inventor_overlay=True)
    pairs = {(p["source"], p["target"]): p for p in result["similarities"]}
    assert pairs['["id","A"]', '["id","C"]']["cosine"] == 1.0
    assert pairs['["id","A"]', '["id","B"]']["cosine"] == 0.0
    assert pairs['["id","A"]', '["id","C"]']["shared_classifications"] == [["IPC", "X"]]
    assert pairs['["id","A"]', '["id","D"]']["cosine"] is None
    assert result["features"][3]["undefined_reason"] == "zero_vector"
    assert result["co_inventor_edges"] == []
    assert result["profiles"][0]["predominant_classification"] == ["IPC", "X"]
    assert result["profiles"][0]["entropy"] == 0.0
    assert all("coordinates" not in p for p in result["features"])
    assert result == technology_similarity(
        units[::-1], rows[::-1], feature=feature, co_inventor_overlay=True
    )


def test_classification_column_and_scheme_budgets_without_top_normalization():
    rows = tuple(
        obs(str(i), ("A",), codes=tuple(str(j) for j in range(i * 43, (i + 1) * 43)))
        for i in range(3)
    )
    with pytest.raises(DatasetInputError):
        technology_profiles(form_units(rows, unit="records"), rows)
    mixed = (
        obs("a", ("A",), codes=("X",)),
        replace(obs("b", ("B",)), classifications=(("CPC", "Y"),)),
    )
    with pytest.raises(DatasetInputError):
        technology_profiles(form_units(mixed, unit="records"), mixed)


def test_unresolved_mass_in_all_person_reference_never_known_only_renormalized():
    from patent_analysis.inventor_identity import Alias, IdentityResolver

    ambiguous = IdentityResolver((Alias("id", "X", "x", "x", ("s",), "candidate"),)).resolve(
        inventor_id="X"
    )
    rows = (obs("a", ("A", ambiguous), codes=("X",)), obs("b", ("B",), codes=("Y",)))
    result = technology_profiles(
        form_units(rows, unit="records"),
        rows,
        person_weight="fractional",
        classification_weight="fractional",
    )
    a = next(c for c in result["cells"] if c["person_token"] == '["id","A"]')
    assert a["count"]["denominator"] == "2"
    assert a["relative_specialization"] == 2.0
    assert result["coverage"]["classification_mass"]["value"] == 2.0
