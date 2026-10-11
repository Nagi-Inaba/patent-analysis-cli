from fractions import Fraction

import pytest

from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_numeric import exact, finish, person_token, project_features


def test_explicit_exact_rounding_and_safe_json_boundary():
    assert exact(Fraction(1, 3)) == {"value": 0.333333333333, "numerator": "1", "denominator": "3"}
    assert person_token(("id", "A")) == '["id","A"]'
    assert person_token(("name", "A")) != person_token(("id", "A"))
    assert finish({"a": exact(Fraction(1, 3))})["a"]["denominator"] == "3"
    for value in (float("nan"), float("inf"), Fraction(1, 3), 2**54):
        with pytest.raises(DatasetInputError):
            finish({"a": value})
    with pytest.raises(DatasetInputError):
        exact(Fraction(1, 2**129))
    with pytest.raises(DatasetInputError):
        finish({"a": "a" * 204801})


def feature(key, values, reason=None):
    return {
        "person_key": ["id", key],
        "person_token": person_token(("id", key)),
        "values": values,
        "undefined_reason": reason,
    }


def test_mds_orthogonal_three_projector_canonical_oracle_and_order():
    rows = [feature("A", [1, 0, 0]), feature("B", [0, 1, 0]), feature("C", [0, 0, 1])]
    result = project_features(rows)
    xy = [p["raw_coordinates"] for p in result["points"]]
    assert xy[0] == pytest.approx([2 / (6**0.5), 0], abs=1e-11)
    assert xy[1] == pytest.approx([-1 / (6**0.5), 1 / (2**0.5)], abs=1e-11)
    assert xy[2] == pytest.approx([-1 / (6**0.5), -1 / (2**0.5)], abs=1e-11)
    assert result["distortion"]["stress"] == pytest.approx(0, abs=1e-11)
    assert result["distortion"]["retained_energy"] == pytest.approx(1)
    assert 0 < float(result["basis"]["eigenvalue_tolerance"]) < 1e-12
    assert result["basis"]["numpy_version"] == "2.4.3"
    assert result == project_features(rows[::-1])


def test_mds_rank_zero_one_duplicates_and_zero_vector_separate_offsets():
    rows = [feature("A", [1, 0]), feature("B", [1, 0]), feature("Z", [0, 0], "zero_vector")]
    result = project_features(rows)
    assert result["basis"]["rank"] == 0
    assert result["distortion"]["stress"] is None
    assert result["distortion"]["retained_energy"] is None
    assert result["distortion"]["undefined_reason"] == "zero_distance_and_energy"
    assert (
        result["points"][0]["raw_coordinates"] == result["points"][1]["raw_coordinates"] == [0, 0]
    )
    assert result["points"][0]["display_offset"] != result["points"][1]["display_offset"]
    assert result["points"][2]["raw_coordinates"] is None
    one = project_features([feature("A", [1, 0]), feature("B", [0, 1])])
    assert one["basis"]["rank"] == 1
    assert one["points"][0]["raw_coordinates"] == pytest.approx([2**-0.5, 0], abs=1e-11)
    assert project_features([])["points"] == []


def test_projector_rotated_repeated_and_near_eigenspace_preserves_gram():
    import numpy as np

    from patent_analysis.inventor_numeric import _canonical_block

    q = np.array([[2 / 6**0.5, 0], [-1 / 6**0.5, 1 / 2**0.5], [-1 / 6**0.5, -1 / 2**0.5]])
    angle = 0.735
    rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    gram = q @ q.T
    expected = _canonical_block(gram, q, 1e-12)
    rotated = _canonical_block(gram, q @ rotation, 1e-12)
    assert np.allclose(expected, rotated, atol=1e-13, rtol=0)
    near_gram = (q @ rotation) @ np.diag([1, 1 + 1e-13]) @ (q @ rotation).T
    near = _canonical_block(near_gram, q @ rotation, 1e-12)
    assert np.allclose(near @ near.T, near_gram, atol=2e-15, rtol=0)


def test_optional_numerics_absent_only_projection_rejects(monkeypatch):
    import builtins

    from patent_analysis.inventor_graph import co_inventor_graph
    from patent_analysis.inventor_profiles import technology_profiles

    original = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name in {"numpy", "networkx", "scipy"}:
            raise ImportError("synthetic missing extra")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    assert co_inventor_graph((), ())["nodes"] == []
    assert technology_profiles((), ())["profiles"] == []
    with pytest.raises(DatasetInputError):
        project_features([feature("A", [1])])
