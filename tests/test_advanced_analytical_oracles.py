"""Independent small-population arithmetic oracles for the ten native analyses.

These tests exercise normalized calculation inputs, not CSV ingestion or SVGs.
Expected values are obtained by direct membership queries rather than by copying
production accumulation helpers. Seeds and finite populations make failures
reproducible; selection must never change full-population denominators.
"""

from __future__ import annotations

import importlib
import itertools
import random
from copy import deepcopy

import pytest

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


def run(name, rows, parameters):
    return importlib.import_module(f"patent_analysis.analyses.{name}").compute(rows, parameters)


def values(row, role):
    return {v.strip() for v in row.get(role, ()) if v.strip()}


def make_rows(seed, count=24):
    rng = random.Random(seed)
    rows = []
    for _ in range(count):
        row = {"year": (str(rng.randrange(2018, 2026)),)}
        for key, alphabet in (("group", "ABCD"), ("item", "PQRS"), ("x", "XYZ"), ("y", "UV")):
            chosen = tuple(v for v in alphabet if rng.randrange(3) == 0)
            # The independent oracle uses sets: duplicate input tokens cannot
            # create extra memberships in any of the calculations.
            row[key] = chosen + chosen[:1]
        row["cites"] = (str(rng.randrange(8)),)
        rows.append(row)
    return rows


def category_order(rows, role, limit):
    labels = set().union(*(values(row, role) for row in rows))
    return sorted(
        labels, key=lambda label: (-sum(label in values(row, role) for row in rows), label)
    )[:limit]


@pytest.mark.parametrize("seed", [11, 47, 103, 809])
def test_growth_quadrant_against_direct_half_membership_counts(seed):
    rows = make_rows(seed)
    p = {
        "date_role": "year",
        "category_role": "group",
        "long_start_year": 2018,
        "long_end_year": 2024,
        "short_start_year": 2022,
        "short_end_year": 2025,
        "top_n": 3,
    }
    result = run("growth_quadrant", rows, p)
    eligible = [r for r in rows if values(r, "group")]
    selected = category_order(eligible, "group", 3)
    assert [point["label"] for point in result["points"]] == selected
    assert result["contributions"] == sum(len(values(r, "group")) for r in eligible)
    assert result["population"]["visible_rows"] == len(eligible)
    for point in result["points"]:
        label = point["label"]
        assert point["total_count"] == sum(label in values(r, "group") for r in eligible)
        for key, start, split, end in (("long", 2018, 2021, 2024), ("short", 2022, 2023, 2025)):
            before = sum(
                label in values(r, "group") and start <= int(r["year"][0]) <= split for r in rows
            )
            after = sum(
                label in values(r, "group") and split < int(r["year"][0]) <= end for r in rows
            )
            expected = (after - before) * 100 / before if before else None if after else 0.0
            assert point[key]["previous"] == before
            assert point[key]["recent"] == after
            if expected is None:
                assert point[key]["rate_percent"] is None
                assert point[key]["state"] == "new"
            else:
                assert point[key]["rate_percent"] == pytest.approx(expected)
    # Overlap is not counted twice in total_count or contribution counters.
    assert sum(point["total_count"] for point in result["points"]) <= result["contributions"]


@pytest.mark.parametrize("seed", [13, 61, 107, 811])
def test_entry_exit_matches_full_population_observation_ranges(seed):
    rows = make_rows(seed)
    result = run("entry_exit", rows, {"date_role": "year", "category_role": "group", "top_n": 2})
    eligible = [r for r in rows if values(r, "group")]
    maximum = max(int(r["year"][0]) for r in eligible)
    assert result["as_of_year"] == maximum
    assert result["active_since_year"] == maximum - 2
    assert [point["label"] for point in result["points"]] == category_order(eligible, "group", 2)
    for point in result["points"]:
        observations = [int(r["year"][0]) for r in eligible if point["label"] in values(r, "group")]
        assert (point["first_year"], point["last_year"], point["count"]) == (
            min(observations),
            max(observations),
            len(observations),
        )
        assert point["active_recent"] is (max(observations) >= maximum - 2)


@pytest.mark.parametrize("seed", [17, 67, 109, 821])
def test_citation_is_record_rank_not_label_aggregation(seed):
    rows = make_rows(seed)
    # Separate records with identical labels and year must remain distinct.
    rows += [{"year": ("2023",), "group": ("A",), "cites": ("12",)}] * 2
    result = run(
        "citation",
        rows,
        {"date_role": "year", "label_role": "group", "citation_role": "cites", "top_n": 7},
    )
    records = [
        (next(iter(values(r, "group"))), int(r["year"][0]), int(r["cites"][0]))
        for r in rows
        if len(values(r, "group")) == 1
    ]
    expected = sorted(records, key=lambda r: (-r[2], r[1], r[0]))[:7]
    assert [(p["label"], p["year"], p["citation_value"]) for p in result["points"]] == expected
    assert [p["point_id"] for p in result["points"]] == list(range(1, len(expected) + 1))
    assert result["population"]["visible_rows"] == len(records)
    assert result["contributions"] == len(records)
    assert expected[:2] == [("A", 2023, 12)] * 2


@pytest.mark.parametrize("seed", [19, 71, 127, 823])
def test_selected_cell_composition_preserves_untruncated_membership_denominator(seed):
    rows = make_rows(seed)
    result = run(
        "matrix_composition",
        rows,
        {
            "x_role": "x",
            "y_role": "y",
            "category_role": "item",
            "x_value": "X",
            "y_value": "U",
            "top_n": 1,
        },
    )
    selected = [r for r in rows if "X" in values(r, "x") and "U" in values(r, "y")]
    counts = {item: sum(item in values(r, "item") for r in selected) for item in "PQRS"}
    total = sum(counts.values())
    assert result["contributions"] == total
    assert result["population"]["visible_rows"] == sum(bool(values(r, "item")) for r in selected)
    expected = sorted((i for i in counts if counts[i]), key=lambda i: (-counts[i], i))[:1]
    assert [item["label"] for item in result["items"]] == expected
    for item in result["items"]:
        assert item["count"] == counts[item["label"]]
        assert item["share"] == pytest.approx(item["count"] / total)


@pytest.mark.parametrize("seed", [23, 73, 131, 827])
def test_new_entrant_history_is_independent_of_classification_and_display_top_n(seed):
    rows = make_rows(seed)
    # Add a definitely new applicant in the recent period and one historical
    # appearance without classification. That history still excludes OLD.
    rows += [
        {"year": ("2024",), "group": ("NEW",), "item": ("P", "Q", "Q")},
        {"year": ("2018",), "group": ("OLD",), "item": ()},
        {"year": ("2025",), "group": ("OLD",), "item": ("P",)},
    ]
    p = {
        "date_role": "year",
        "applicant_role": "group",
        "classification_role": "item",
        "as_of_year": 2023,
        "top_n": 2,
        "top_classifications": 1,
    }
    result = run("new_entrants", rows, p)
    all_groups = set().union(*(values(r, "group") for r in rows))
    first = {a: min(int(r["year"][0]) for r in rows if a in values(r, "group")) for a in all_groups}
    frequencies = {a: sum(a in values(r, "group") for r in rows) for a in all_groups}
    applicants = sorted(
        (a for a in all_groups if first[a] >= 2023), key=lambda a: (-frequencies[a], a)
    )[:2]
    assert [a["label"] for a in result["applicants"]] == applicants
    assert "OLD" not in applicants
    all_items = set().union(*(values(r, "item") for r in rows))
    pairs = {
        (a, i): sum(a in values(r, "group") and i in values(r, "item") for r in rows)
        for a in applicants
        for i in all_items
    }
    totals = {a: sum(pairs[a, i] for i in all_items) for a in applicants}
    labels = sorted(
        (i for i in all_items if sum(pairs[a, i] for a in applicants)),
        key=lambda i: (-sum(pairs[a, i] for a in applicants), i),
    )[:1]
    assert result["classifications"] == labels
    for cell in result["cells"]:
        assert cell["count"] == pairs[cell["applicant"], cell["classification"]]
        assert cell["share"] == pytest.approx(cell["count"] / totals[cell["applicant"]])
    for a in result["applicants"]:
        assert a["first_year"] == first[a["label"]]
        assert a["classification_memberships"] == totals[a["label"]]
    assert result["contributions"] == sum(totals.values())


@pytest.mark.parametrize("seed", [29, 79, 137, 829])
def test_compara_signed_difference_against_membership_queries(seed):
    rows = make_rows(seed)
    p = {
        "x_role": "x",
        "y_role": "y",
        "group_role": "group",
        "group_a": "A",
        "group_b": "B",
        "top_n": 2,
    }
    result = run("compara", rows, p)
    eligible = [
        r for r in rows if values(r, "x") and values(r, "y") and values(r, "group") & {"A", "B"}
    ]
    assert result["x"] == category_order(eligible, "x", 2)
    assert result["y"] == category_order(eligible, "y", 2)
    assert len(result["cells"]) == len(result["x"]) * len(result["y"])
    for cell in result["cells"]:
        pair_rows = [r for r in rows if cell["x"] in values(r, "x") and cell["y"] in values(r, "y")]
        a = sum("A" in values(r, "group") for r in pair_rows)
        b = sum("B" in values(r, "group") for r in pair_rows)
        assert (cell["a_count"], cell["b_count"], cell["difference"]) == (a, b, a - b)
    reversed_result = run("compara", rows, {**p, "group_a": "B", "group_b": "A"})
    assert result["x"] == reversed_result["x"] and result["y"] == reversed_result["y"]
    assert [c["difference"] for c in result["cells"]] == [
        -c["difference"] for c in reversed_result["cells"]
    ]
    expected_memberships = sum(
        len(values(r, "x")) * len(values(r, "y")) * len(values(r, "group") & {"A", "B"})
        for r in eligible
    )
    assert result["contributions"] == expected_memberships


@pytest.mark.parametrize("seed", [31, 83, 139, 839])
def test_cooccurrence_matches_direct_boolean_incidence_product(seed):
    rows = make_rows(seed)
    result = run("cooccurrence", rows, {"category_role": "item", "top_n": 3})
    assert result["labels"] == category_order(rows, "item", 3)
    for cell in result["cells"]:
        expected = (
            0
            if cell["x"] == cell["y"]
            else sum({cell["x"], cell["y"]} <= values(r, "item") for r in rows)
        )
        assert cell["count"] == expected
    visible_pairs = {(p["source"], p["target"]): p["count"] for p in result["pairs"]}
    assert sum(c["count"] for c in result["cells"]) == 2 * sum(visible_pairs.values())
    assert all(a < b for a, b in visible_pairs)
    assert result["contributions"] == sum(
        len(values(r, "item")) * (len(values(r, "item")) - 1) // 2 for r in rows
    )


@pytest.mark.parametrize("seed", [37, 89, 149, 853])
def test_network_weights_and_global_pair_cutoff_match_independent_incidence(seed):
    rows = make_rows(seed)
    result = run("network", rows, {"category_role": "group", "top_n": 3, "top_nodes": 3})
    joint = [r for r in rows if len(values(r, "group")) >= 2]
    weights = {g: sum(g in values(r, "group") for r in joint) for g in "ABCD"}
    nodes = sorted((g for g in weights if weights[g]), key=lambda g: (-weights[g], g))[:3]
    pair_counts = {
        (a, b): sum({a, b} <= values(r, "group") for r in joint)
        for a, b in itertools.combinations("ABCD", 2)
    }
    top = sorted(
        (pair for pair, n in pair_counts.items() if n), key=lambda pair: (-pair_counts[pair], pair)
    )[:3]
    edges = [
        {"source": a, "target": b, "count": pair_counts[a, b]}
        for a, b in top
        if a in nodes and b in nodes
    ]
    assert result["edges"] == edges
    linked = {edge[key] for edge in edges for key in ("source", "target")}
    assert result["nodes"] == [{"label": g, "count": weights[g]} for g in nodes if g in linked]
    assert result["population"]["visible_rows"] == len(joint)


@pytest.mark.parametrize("seed", [41, 97, 151, 857])
@pytest.mark.parametrize("minimum", [2, 3, 4])
def test_grouped_metrics_match_global_set_queries_and_single_record_involvement(seed, minimum):
    rows = make_rows(seed)
    rows += [deepcopy(rows[0])]  # Repeated records change row counts, not distinct ownership.
    p = {"group_role": "group", "item_role": "item", "top_n": 2}
    unique = run("uniqueness", rows, p)
    shared = run("shared_involvement", rows, {**p, "min_groups": minimum})
    eligible = [r for r in rows if values(r, "group") and values(r, "item")]
    owned = {
        g: set().union(*(values(r, "item") for r in eligible if g in values(r, "group")))
        for g in "ABCD"
    }
    owners = {item: {g for g in owned if item in owned[g]} for item in "PQRS"}
    for record in unique["groups"]:
        g = record["group"]
        exclusive = {item for item in owned[g] if owners[item] == {g}}
        assert record["unique_items"] == sorted(exclusive)
        assert record["unique_item_count"] == len(exclusive)
        assert record["uniqueness_rate"] == pytest.approx(len(exclusive) / len(owned[g]))
        assert record["record_count"] == sum(g in values(r, "group") for r in eligible)
    global_shared = {item for item in owners if len(owners[item]) >= minimum}
    for record in shared["groups"]:
        g = record["group"]
        shared_items = owned[g] & global_shared
        assert record["shared_items"] == sorted(shared_items)
        assert record["shared_item_count"] == len(shared_items)
        assert record["shared_rate"] == pytest.approx(len(shared_items) / len(owned[g]))
        assert record["involvement_record_count"] == sum(
            g in values(r, "group") and bool(values(r, "item") & global_shared) for r in eligible
        )
    expected_memberships = sum(len(values(r, "group")) * len(values(r, "item")) for r in eligible)
    assert unique["contributions"] == shared["contributions"] == expected_memberships
