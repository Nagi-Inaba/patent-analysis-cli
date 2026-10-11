import pytest
from test_inventor_graph import obs

from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_activity import annual_activity, cluster_flow
from patent_analysis.inventor_units import form_units


def test_annual_calendar_gaps_missing_dates_and_distinct_cumulative_family_basis():
    rows = (
        obs("1", ("A", "B"), "2020", ("X",), family_id="f"),
        obs("2", ("A", "C"), "2022-03", ("Y",), family_id="f"),
        obs("3", ("D",), None, family_id="g"),
    )
    units = form_units(rows, unit="family")
    result = annual_activity(units, rows, person_weight="fractional")
    assert [y["year"] for y in result["calendar"]] == [2020, 2021, 2022]
    assert result["calendar"][1]["observed"] is False
    assert result["missing_date_record_ids"] == ["3"]
    a = result["people"][0]
    assert a["cumulative_unit_activity"]["denominator"] == "3"
    assert a["annual_unit_presences"] == 2
    annual = [r for r in result["observations"] if r["person_token"] == '["id","A"]']
    assert annual[0]["activity"]["denominator"] == "3"
    assert annual[1]["observed"] is False
    assert annual[1]["activity"] is None
    assert annual[1]["not_observed_partners"] == ['["id","B"]']
    assert annual[2]["added_partners"] == ['["id","C"]']
    assert annual[2]["continued_partners"] == []
    assert result == annual_activity(units[::-1], rows[::-1], person_weight="fractional")
    long = (obs("a", ("A",), "1990"), obs("b", ("A",), "2020"))
    with pytest.raises(DatasetInputError):
        annual_activity(form_units(long, unit="records"), long)


def test_cluster_split_merge_singletons_membership_conservation_no_gap_links():
    rows = (
        obs("1", ("A", "B", "C"), "2020"),
        obs("2", ("A", "B"), "2021"),
        obs("3", ("C",), "2021"),
        obs("4", ("A", "B", "C"), "2022"),
        obs("5", ("A", "B"), "2024"),
    )
    units = form_units(rows, unit="records")
    result = cluster_flow(units, rows)
    groups = [n for n in result["nodes"] if n["kind"] == "cluster"]
    assert len(groups) == 5
    assert groups[0]["split"] is True
    assert [g for g in groups if g["year"] == 2022][0]["merge"] is True
    assert groups[0]["node_id"] != groups[-1]["node_id"]
    for node in groups:
        assert (
            sum(link["width"] for link in result["links"] if link["source"] == node["node_id"])
            == node["size"]
        )
        assert (
            sum(link["width"] for link in result["links"] if link["target"] == node["node_id"])
            == node["size"]
        )
    assert not any(
        link["kind"] == "shared_members" and link["target_year"] == 2024 for link in result["links"]
    )
    assert result == cluster_flow(units[::-1], rows[::-1])


def test_cluster_flow_retains_unplottable_person_metadata():
    from patent_analysis.inventor_identity import Alias, IdentityResolver

    ambiguous = IdentityResolver((Alias("id", "X", "x", "x", ("s",), "candidate"),)).resolve(
        inventor_id="X"
    )
    rows = (obs("1", ("A", ambiguous), "2020"), obs("2", ("D",), None))
    result = cluster_flow(form_units(rows, unit="records"), rows)
    assert [p["person_key"] for p in result["unplottable"]] == [["ambiguous_id", "X"], ["id", "D"]]
    assert result["unplottable"][0]["reasons"] == ["ambiguous_identity"]
    assert result["unplottable"][1]["reasons"] == ["missing_date"]
    assert all('["ambiguous_id","X"]' not in n["members"] for n in result["nodes"])


def test_annual_fraction_bit_preflight_precedes_year_graphs(monkeypatch):
    import patent_analysis.inventor_activity as module

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

    def forbidden(*args, **kwargs):
        raise AssertionError("year graph reached before fraction budget")

    monkeypatch.setattr(module, "co_inventor_graph", forbidden)
    with pytest.raises(DatasetInputError):
        annual_activity(units, rows, person_weight="fractional")
