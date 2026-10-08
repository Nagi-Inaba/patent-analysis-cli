"""Check supplied membership operands before projection discards them."""
from __future__ import annotations

import json
from copy import deepcopy
from importlib.resources import files

import pytest
from jsonschema import Draft202012Validator

from patent_analysis.advanced_projection import project_advanced_data


def _base(analysis_id):
    return {
        "schema_version": "1.0.0", "algorithm_version": "1.0.0", "analysis_id": analysis_id,
        "population": {"input_rows": 100, "visible_rows": 100, "excluded_rows": 0},
        "contributions": 100,
    }


def _project(data, *, reject=False):
    name = data["analysis_id"].removesuffix(".v1") + "-result-v1.schema.json"
    schema = json.loads(files("patent_analysis").joinpath("schemas", name).read_text("utf-8"))
    Draft202012Validator(schema).validate(data)
    before = deepcopy(data)
    if reject:
        with pytest.raises(ValueError):
            project_advanced_data(data["analysis_id"], data)
        result = None
    else:
        result = project_advanced_data(data["analysis_id"], data)
    assert data == before
    return result


def _entrants(counts=(2, 3), memberships=10, shares=None):
    if shares is None:
        shares = [n / memberships if memberships else 0 for n in counts]
    data = _base("new-entrants.v1")
    data.update(
        as_of_year=2023,
        applicants=[{"label": "A", "first_year": 2023, "row_count": 10,
                     "classification_memberships": memberships}],
        classifications=[f"C{i}" for i in range(len(counts))],
        cells=[{"applicant": "A", "classification": f"C{i}", "count": n, "share": s}
               for i, (n, s) in enumerate(zip(counts, shares, strict=True))],
        share_basis="all_classification_memberships_per_applicant",
    )
    return data


@pytest.mark.parametrize(("counts", "memberships", "shares"), [
    ((100,), 1, (1.0,)), ((1,), 10, (0.9,)), ((6, 6), 10, (0.6, 0.6)),
    ((1,), 0, (0.0,)), ((0,), 0, (0.5,)),
])
def test_entrant_cells_reject_impossible_counts_shares_or_subtotals(counts, memberships, shares):
    _project(_entrants(counts, memberships, shares), reject=True)


@pytest.mark.parametrize(("counts", "memberships"), [
    ((2, 3), 10), ((3, 7), 10), ((0,), 0), ((), 0),
])
def test_entrant_valid_subsets_keep_full_denominator_shares(counts, memberships):
    data = _entrants(counts, memberships)
    result = _project(data)
    assert [c["value"] for c in result["cells"]] == list(counts)
    assert [c["share"] for c in result["cells"]] == [c["share"] for c in data["cells"]]


def test_entrant_totals_are_per_applicant_not_global():
    data = _entrants((1,), 1)
    data["applicants"].append({"label": "B", "first_year": 2024, "row_count": 10,
                               "classification_memberships": 10})
    data["cells"].append({"applicant": "B", "classification": "C0", "count": 5, "share": 0.5})
    assert [c["share"] for c in _project(data)["cells"]] == [1.0, 0.5]


def _cooccurrence(count=2, marginal=3):
    data = _base("cooccurrence.v1")
    data.update(
        labels=["A", "B"], label_counts=[{"label": x, "count": marginal} for x in ("A", "B")],
        cells=[{"x": x, "y": y, "count": 0 if x == y else count}
               for y in ("A", "B") for x in ("A", "B")],
        pairs=[{"source": "A", "target": "B", "count": count}] if count else [],
    )
    return data


@pytest.mark.parametrize("mutation", [
    "joint-exceeds-marginals", "cell-disagrees", "missing-pair", "duplicate-pair",
    "reversed-duplicate", "missing-label-count", "extra-label-count", "duplicate-label-count",
    "unknown-pair", "self-pair", "missing-cell", "nonzero-diagonal",
])
def test_cooccurrence_checks_counts_pairs_and_complete_cells(mutation):
    data = _cooccurrence()
    if mutation == "joint-exceeds-marginals":
        data = _cooccurrence(count=50, marginal=1)
    elif mutation == "cell-disagrees":
        data["cells"][1]["count"] = 1
    elif mutation == "missing-pair":
        data["pairs"] = []
    elif mutation == "duplicate-pair":
        data["pairs"].append(dict(data["pairs"][0]))
    elif mutation == "reversed-duplicate":
        data["pairs"].append({"source": "B", "target": "A", "count": 2})
    elif mutation == "missing-label-count":
        data["label_counts"].pop()
    elif mutation == "extra-label-count":
        data["label_counts"].append({"label": "C", "count": 3})
    elif mutation == "duplicate-label-count":
        data["label_counts"].append(dict(data["label_counts"][0]))
    elif mutation == "unknown-pair":
        data["pairs"][0]["source"] = "C"
    elif mutation == "self-pair":
        data["pairs"][0]["source"] = "B"
    elif mutation == "missing-cell":
        data["cells"].pop()
    else:
        data["cells"][0]["count"] = 1
    _project(data, reject=True)


@pytest.mark.parametrize(("count", "marginal"), [(2, 3), (3, 3), (0, 3), (0, 0)])
def test_cooccurrence_preserves_valid_pairs_and_absent_zero_pairs(count, marginal):
    data = _cooccurrence(count, marginal)
    assert [c["value"] for c in _project(data)["cells"]] == [0, count, count, 0]


def test_cooccurrence_empty_result_remains_valid():
    data = _cooccurrence()
    data.update(labels=[], label_counts=[], cells=[], pairs=[])
    assert _project(data)["cells"] == []


def _network(left, right, joint):
    data = _base("collaboration-network.v1")
    data.update(nodes=[{"label": "A", "count": left}, {"label": "B", "count": right}],
                edges=[{"source": "A", "target": "B", "count": joint}])
    return data


@pytest.mark.parametrize(("left", "right", "joint"), [(1, 1, 100), (2, 5, 3), (5, 2, 3)])
def test_network_joint_count_cannot_exceed_either_endpoint(left, right, joint):
    _project(_network(left, right, joint), reject=True)


@pytest.mark.parametrize(("left", "right", "joint"), [(2, 5, 2), (5, 2, 2), (0, 0, 0)])
def test_network_accepts_joint_count_at_boundary(left, right, joint):
    assert _project(_network(left, right, joint))["edges"][0]["value"] == joint


def test_network_multi_owner_row_does_not_use_incident_sum_as_bound():
    data = _base("collaboration-network.v1")
    data.update(nodes=[{"label": x, "count": 1} for x in ("A", "B", "C")],
                edges=[{"source": a, "target": b, "count": 1}
                       for a, b in (("A", "B"), ("A", "C"), ("B", "C"))])
    assert len(_project(data)["edges"]) == 3
