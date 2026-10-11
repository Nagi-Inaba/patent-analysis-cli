import json
from dataclasses import replace
from fractions import Fraction
from itertools import permutations

import pytest

from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_graph import co_inventor_graph, ego_network
from patent_analysis.inventor_identity import Alias, IdentityResolver
from patent_analysis.inventor_models import PatentObservation, parse_observation_date
from patent_analysis.inventor_units import form_units


def obs(record, people, year="2024", codes=(), **kwargs):
    resolver = IdentityResolver()
    identities = tuple(
        p if not isinstance(p, str) else resolver.resolve(inventor_id=p) for p in people
    )
    return PatentObservation(
        record,
        identities,
        parse_observation_date(year, kind="filing"),
        classifications=tuple(("IPC", c) for c in codes),
        **kwargs,
    )


def test_full_graph_chain_isolate_and_fractional_ambiguous_reservation():
    ambiguous = IdentityResolver((Alias("id", "X", "x", "x", ("s",), "candidate"),)).resolve(
        inventor_id="X"
    )
    rows = (obs("1", ("A", "B", ambiguous)), obs("2", ("B", "C")), obs("3", ("D",)))
    units = form_units(rows, unit="records")
    result = co_inventor_graph(
        units, rows, person_weight="fractional", pair_weight="unit_pair_fractional"
    )
    nodes = {n["inventor_id"]: n for n in result["nodes"]}
    assert list(nodes) == list("ABCD")
    assert [nodes[p]["degree"] for p in "ABCD"] == [1, 2, 1, 0]
    assert nodes["A"]["activity"]["denominator"] == "3"
    assert nodes["B"]["betweenness_unweighted"] == pytest.approx(1 / 3)
    assert nodes["B"]["betweenness_weighted"] == pytest.approx(1 / 3)
    assert result["edges"][0]["weight"]["denominator"] == "3"
    assert result["edges"][0]["record_ids"] == ["1"]
    assert len(result["communities"]) == 2
    assert result["coverage"]["ambiguous_people"] == 1
    assert result["unplottable"][0]["person_key"] == ["ambiguous_id", "X"]
    assert result["unplottable"][0]["activity"]["denominator"] == "3"
    assert result["unplottable"][0]["reason"] == "ambiguous_identity"
    assert result["unplottable"][0]["candidate_ids"] == ["x"]
    assert result["unplottable"][0]["source_ids"] == ["s"]
    assert sum(n["pagerank"] for n in result["nodes"]) == pytest.approx(1)
    assert result["basis"]["pagerank_l1_tolerance"] == 1e-12
    assert result["basis"]["pagerank_max_iterations"] == 1000
    assert result["basis"]["algorithm_version"] == "inventor_graph.v1"
    json.dumps(result, allow_nan=False)
    assert result == co_inventor_graph(
        units[::-1], rows[::-1], person_weight="fractional", pair_weight="unit_pair_fractional"
    )
    with pytest.raises(DatasetInputError):
        co_inventor_graph(units, rows[:-1])


def test_ego_global_metrics_hops_dates_and_isolated_focus():
    rows = (obs("1", ("A", "B"), "2020-02", ("X",)), obs("2", ("B", "C"), "2022"), obs("3", ("D",)))
    units = form_units(rows, unit="records")
    graph = co_inventor_graph(units, rows)
    ego = ego_network(graph, focus=("id", "A"), hops=1)
    assert ego["nodes"] == graph["nodes"][:2]
    assert ego["hop_membership"] == [
        {"person_token": '["id","A"]', "hop": 0},
        {"person_token": '["id","B"]', "hop": 1},
    ]
    assert ego["partners"][0]["first_observation"]["precision"] == "month"
    assert ego["partners"][0]["classifications"] == [["IPC", "X"]]
    assert len(ego_network(graph, focus=("id", "A"), hops=2)["nodes"]) == 3
    assert len(ego_network(graph, focus=("id", "D"))["nodes"]) == 1
    for focus in (("id", "missing"), ("ambiguous_id", "X")):
        with pytest.raises(DatasetInputError):
            ego_network(graph, focus=focus)
    with pytest.raises(DatasetInputError):
        ego_network(graph, focus=("id", "A"), hops=4)


def test_weighted_betweenness_reciprocal_and_pagerank_stationary_oracle():
    rows = (
        tuple(obs(f"ab{i}", ("A", "B")) for i in range(10))
        + tuple(obs(f"bc{i}", ("B", "C")) for i in range(10))
        + (obs("ac", ("A", "C")),)
    )
    graph = co_inventor_graph(form_units(rows, unit="records"), rows)
    b = graph["nodes"][1]
    assert b["betweenness_unweighted"] == 0
    assert b["betweenness_weighted"] == 1
    # Independent stationary equations of A-B-C + isolated D.
    chain = (obs("ab", ("A", "B")), obs("bc", ("B", "C")), obs("d", ("D",)))
    result = co_inventor_graph(form_units(chain, unit="records"), chain)
    assert [n["pagerank"] for n in result["nodes"]] == pytest.approx(
        [
            float(Fraction(190, 777)),
            float(Fraction(360, 777)),
            float(Fraction(190, 777)),
            float(Fraction(1, 21)),
        ],
        abs=2e-12,
    )
    from patent_analysis.inventor_graph import _pagerank

    with pytest.raises(DatasetInputError):
        _pagerank(
            {
                ("id", "A"): {("id", "B"): Fraction(1)},
                ("id", "B"): {("id", "A"): Fraction(1), ("id", "C"): Fraction(1)},
                ("id", "C"): {("id", "B"): Fraction(1)},
            },
            max_iterations=1,
        )


def test_greedy_modularity_explicit_tie_and_family_no_fabrication():
    rows = (
        obs("1", ("A", "B"), family_id="f"),
        obs("2", ("B", "C"), family_id="f"),
        obs("3", ("D",), family_id="g"),
    )
    units = form_units(rows, unit="family")
    result = co_inventor_graph(units, rows, community_method="greedy_modularity")
    assert [(e["source"], e["target"]) for e in result["edges"]] == [
        ('["id","A"]', '["id","B"]'),
        ('["id","B"]', '["id","C"]'),
    ]
    for reordered in permutations(rows):
        assert co_inventor_graph(units, reordered, community_method="greedy_modularity") == result
    assert [c["members"] for c in result["communities"]] == [
        ['["id","A"]', '["id","B"]', '["id","C"]'],
        ['["id","D"]'],
    ]


def test_full_population_budgets_and_name_id_collision():
    resolver = IdentityResolver()
    rows = (obs("1", ("A", resolver.resolve(name="A"))),)
    graph = co_inventor_graph(form_units(rows, unit="records"), rows)
    assert {n["person_token"] for n in graph["nodes"]} == {'["id","A"]', '["name","A"]'}
    assert graph["nodes"][1]["caveats"] == ["name_match_is_not_person_confirmation"]
    many = tuple(obs(str(i), (str(i),)) for i in range(201))
    with pytest.raises(DatasetInputError):
        co_inventor_graph(form_units(many, unit="records"), many)
    assert (
        len(co_inventor_graph(form_units(many[:200], unit="records"), many[:200])["nodes"]) == 200
    )
    assert co_inventor_graph((), ())["nodes"] == []


def test_fraction_bit_budget_checked_before_centrality(monkeypatch):
    import patent_analysis.inventor_graph as module

    primes = [
        101,
        103,
        107,
        109,
        113,
        127,
        131,
        137,
        139,
        149,
        151,
        157,
        163,
        167,
        173,
        179,
        181,
        191,
        193,
        197,
        199,
    ]
    rows = tuple(obs(f"{n}:{i}", (str(i),), family_id=str(n)) for n in primes for i in range(n))
    units = form_units(rows, unit="family")

    def forbidden(*args):
        raise AssertionError("centrality reached before fraction preflight")

    monkeypatch.setattr(module, "_betweenness", forbidden)
    with pytest.raises(DatasetInputError):
        co_inventor_graph(units, rows, person_weight="fractional")


def test_first_last_observation_do_not_compare_mixed_date_kinds():
    rows = (
        obs("a", ("A", "B"), "2020"),
        replace(
            obs("b", ("A", "B"), "2021"),
            observed_date=parse_observation_date("2021", kind="publication"),
        ),
    )
    with pytest.raises(DatasetInputError):
        co_inventor_graph(form_units(rows, unit="records"), rows)


def test_edge_budget_before_superlinear_metric_work(monkeypatch):
    from itertools import combinations

    import patent_analysis.inventor_graph as module

    blocks = [tuple(str(i) for i in range(j, j + 25)) for j in range(0, 100, 25)] + [("100",)]
    rows = tuple(obs(str(i), a + b) for i, (a, b) in enumerate(combinations(blocks, 2)))
    units = form_units(rows, unit="records")

    def forbidden(*args):
        raise AssertionError("centrality reached before edge budget")

    monkeypatch.setattr(module, "_betweenness", forbidden)
    with pytest.raises(DatasetInputError):
        co_inventor_graph(units, rows)


def test_result_byte_budget_precedes_centrality_for_long_identifiers(monkeypatch):
    import patent_analysis.inventor_graph as module

    rows = (obs("r", tuple(str(i) + "x" * 500 for i in range(30))),)
    units = form_units(rows, unit="records")

    def forbidden(*args):
        raise AssertionError("centrality reached before output budget")

    monkeypatch.setattr(module, "_betweenness", forbidden)
    with pytest.raises(DatasetInputError):
        co_inventor_graph(units, rows)


def test_ego_and_flow_members_sort_person_keys_not_escaped_token_text():
    from patent_analysis.inventor_activity import cluster_flow
    from patent_analysis.inventor_numeric import person_token

    partners = ('"', "A", "\\")
    rows = (obs("a", ("F", *partners), "2020"), obs("b", ("F", *partners), "2021"))
    units = form_units(rows, unit="records")
    graph = co_inventor_graph(units, rows)
    ego = ego_network(graph, focus=("id", "F"))
    assert [p["person_token"] for p in ego["partners"]] == [
        person_token(("id", p)) for p in partners
    ]
    flow = cluster_flow(units, rows)
    shared = next(link for link in flow["links"] if link["kind"] == "shared_members")
    assert shared["members"] == [person_token(("id", p)) for p in sorted(("F", *partners))]
