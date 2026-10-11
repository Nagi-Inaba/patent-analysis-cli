"""Real observation regressions for numerical kernel review findings."""

from fractions import Fraction

import pytest
from test_inventor_citations import citation
from test_inventor_graph import obs

from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_activity import annual_activity
from patent_analysis.inventor_citations import citation_metrics
from patent_analysis.inventor_identity import Alias, IdentityResolver
from patent_analysis.inventor_numeric import MAX_RESULT_BYTES, exact, json_size
from patent_analysis.inventor_profiles import technology_profiles, technology_similarity
from patent_analysis.inventor_units import form_units


@pytest.mark.parametrize("feature", ["composition", "count", "tfidf"])
def test_similarity_budget_applies_to_returned_result_not_discarded_profile_cells(feature):
    rows = tuple(
        obs(
            f"r{i}",
            tuple(str(p) for p in range(10)),
            codes=tuple(f"A01B{j + 1}/00" for j in range(i * 32, (i + 1) * 32)),
        )
        for i in range(4)
    )
    units = form_units(rows, unit="records")
    with pytest.raises(DatasetInputError):
        technology_profiles(units, rows)

    result = technology_similarity(units, rows, feature=feature)

    assert json_size(result) <= MAX_RESULT_BYTES
    assert len(result["features"]) == len(result["profiles"]) == 10
    assert len(result["classifications"]) == 128
    assert len(result["similarities"]) == 55
    assert all(p["classification_total"]["numerator"] == "128" for p in result["profiles"])
    assert all(p["activity"]["numerator"] == "4" for p in result["profiles"])
    assert all(pair["cosine"] == 1.0 for pair in result["similarities"])
    assert all(len(pair["shared_classifications"]) == 128 for pair in result["similarities"])


@pytest.mark.parametrize("feature", ["composition", "count", "tfidf"])
@pytest.mark.parametrize("person_weight", ["full", "fractional"])
@pytest.mark.parametrize("classification_weight", ["full", "fractional"])
def test_similarity_summaries_match_full_profiles_with_witnessed_reference(
    feature, person_weight, classification_weight
):
    ambiguous = IdentityResolver((Alias("id", "X", "x", "x", ("s",), "candidate"),)).resolve(
        inventor_id="X"
    )
    rows = (
        obs("1", ("A", "B", ambiguous), codes=("X", "Y"), family_id="f"),
        obs("2", ("B", "C"), codes=("Z",), family_id="f"),
        obs("3", ("D",), family_id="g"),
    )
    units = form_units(rows, unit="family")
    kwargs = {"person_weight": person_weight, "classification_weight": classification_weight}
    profiles = technology_profiles(units, rows, **kwargs)
    similarity = technology_similarity(units, rows, feature=feature, **kwargs)
    assert similarity["profiles"] == profiles["profiles"]
    assert similarity == technology_similarity(units[::-1], rows[::-1], feature=feature, **kwargs)
    cells = {(c["person_token"], c["classification"][1]): c for c in profiles["cells"]}
    assert ('["id","A"]', "Z") not in cells
    assert ('["id","C"]', "X") not in cells
    assert all(c["unit_count"] == 1 for c in cells.values())
    assert ('["ambiguous_id","X"]', "X") in cells
    if person_weight == classification_weight == "fractional":
        assert profiles["coverage"]["classification_mass"] == {
            "value": 1.0,
            "numerator": "1",
            "denominator": "1",
        }
        reference = {r["classification"][1]: r for r in profiles["classifications"]}
        assert reference["X"]["count"]["numerator"] == "1"
        assert reference["X"]["count"]["denominator"] == "3"
        assert reference["Z"]["count"]["numerator"] == "1"
        assert reference["Z"]["count"]["denominator"] == "3"
        assert cells['["id","A"]', "X"]["relative_specialization"] == 1.5


@pytest.mark.parametrize("feature", ["composition", "count", "tfidf"])
def test_similarity_complete_result_budget_still_rejects_when_profiles_fit(feature, monkeypatch):
    import patent_analysis.inventor_profiles as module

    rows = (obs("r", tuple(str(p) for p in range(30)), codes=tuple(f"C{c}" for c in range(32))),)
    units = form_units(rows, unit="records")
    assert json_size(technology_profiles(units, rows)) <= MAX_RESULT_BYTES
    actual_finish = module.finish
    complete_sizes = []

    def measured_finish(result):
        complete_sizes.append(json_size(result))
        assert "similarities" in result
        return actual_finish(result)

    monkeypatch.setattr(module, "finish", measured_finish)
    with pytest.raises(DatasetInputError):
        technology_similarity(units, rows, feature=feature)
    assert len(complete_sizes) == 1
    assert complete_sizes[0] > MAX_RESULT_BYTES


def test_annual_missing_date_membership_work_is_linear_in_people_times_records(monkeypatch):
    import patent_analysis.inventor_activity as module

    rows = tuple(obs(f"r{i:03}", (str(i % 12),), None) for i in range(80))
    units = form_units(rows, unit="records")
    actual_inputs = module._annual_inputs
    probes = 0

    class CountedMissing(list):
        def __contains__(self, rid):
            nonlocal probes
            for candidate in self:
                probes += 1
                if candidate == rid:
                    return True
            return False

    def measured_inputs(received_units, received_rows):
        assert received_units is units
        assert received_rows is rows
        records, identities, dated, missing, years, views = actual_inputs(
            received_units, received_rows
        )
        return records, identities, dated, CountedMissing(missing), years, views

    monkeypatch.setattr(module, "_annual_inputs", measured_inputs)
    result = annual_activity(units, rows)

    assert probes <= len(result["people"]) * len(rows)
    assert result["missing_date_record_ids"] == sorted(r.record_id for r in rows)
    assert isinstance(result["missing_date_record_ids"], list)
    assert result["calendar"] == result["observations"] == []
    for person in result["people"]:
        expected_ids = sorted(
            r.record_id for r in rows if r.inventor_keys[0] == tuple(person["person_key"])
        )
        assert person["missing_date_unit_ids"] == expected_ids
        assert person["cumulative_unique_units"] == len(expected_ids)


@pytest.mark.parametrize("missing_date", [None, ""])
def test_annual_missing_date_ids_preserve_own_family_witnesses_and_permutations(missing_date):
    rows = (
        obs("dated", ("A",), "2020", family_id="f"),
        obs("missing-b", ("B",), missing_date, family_id="f"),
        obs("missing-a", ("A",), missing_date, family_id="g"),
    )
    units = form_units(rows, unit="family")
    result = annual_activity(units, rows, person_weight="fractional")
    assert result["missing_date_record_ids"] == ["missing-a", "missing-b"]
    assert type(result["missing_date_record_ids"]) is list
    people = {p["inventor_id"]: p for p in result["people"]}
    assert people["A"]["missing_date_unit_ids"] == ["g"]
    assert people["B"]["missing_date_unit_ids"] == ["f"]
    assert people["A"]["cumulative_unit_activity"]["value"] == 1.5
    assert people["B"]["cumulative_unit_activity"]["value"] == 0.5
    assert people["A"]["annual_unit_presences"] == 1
    assert people["B"]["annual_unit_presences"] == 0
    assert result == annual_activity(units[::-1], rows[::-1], person_weight="fractional")


@pytest.mark.parametrize("recent_start_year", [None, 2023])
def test_citation_all_missing_dates_have_unknown_recent_activity(recent_start_year):
    rows = (obs("r", ("A", "B"), None, ("X",)),)
    units = form_units(rows, unit="records")
    evidence = (citation("r", 10),)
    result = citation_metrics(
        units,
        rows,
        evidence,
        snapshot_date="2025-01-01",
        person_weight="fractional",
        recent_start_year=recent_start_year,
    )
    assert all(p["recent_activity"] is None for p in result["people"])
    assert all("missing_activity_date" in p["unplottable_reasons"] for p in result["people"])
    assert all(p["activity"]["value"] == 0.5 for p in result["people"])
    assert all(p["raw_sum"]["value"] == 5 for p in result["people"])
    assert result["coverage"]["allocated_citation_sum"]["value"] == 10
    assert result["coverage"]["unit_citation_sum"]["value"] == 10
    assert result["basis"]["recent_start_year"] == recent_start_year


@pytest.mark.parametrize("recent_start_year", [None, 2023])
@pytest.mark.parametrize("person_weight", ["full", "fractional"])
@pytest.mark.parametrize(
    "witnesses,expected_memberships,missing_people",
    [
        ((("A", "2020", "f"),), {"A": 0}, set()),
        ((("A", "2020", "f"), ("A", None, "f")), {"A": None}, {"A"}),
        ((("AB", "2024", "f"), ("A", None, "f")), {"A": 1, "B": 1}, {"A"}),
        ((("AB", "2024", "f"), ("A", None, "g")), {"A": None, "B": 1}, {"A"}),
        ((("A", None, "f"), ("B", "2024", "f")), {"A": None, "B": 1}, {"A"}),
        ((("A", "2020", "f"), ("B", None, "f")), {"A": 0, "B": None}, {"B"}),
        ((("A", "2023", "f"),), {"A": 1}, set()),
    ],
    ids=[
        "old",
        "old-unknown",
        "same-unit-proof",
        "separate-unknown-unit",
        "other-person-proof-invalid",
        "other-person-missing",
        "threshold-inclusive",
    ],
)
def test_citation_recent_membership_uses_each_person_witnessed_original_unit(
    witnesses, expected_memberships, missing_people, person_weight, recent_start_year
):
    rows = tuple(
        obs(str(i), tuple(people), date, ("X",), family_id=family)
        for i, (people, date, family) in enumerate(witnesses)
    ) + (obs("anchor", ("Z",), "2025", ("X",), family_id="anchor"),)
    units = form_units(rows, unit="family")
    evidence = tuple(citation(row.record_id, 1, citing_ids=("c",)) for row in rows)
    kwargs = {
        "snapshot_date": "2025-01-01",
        "citation_basis": "unique_citing_ids",
        "person_weight": person_weight,
        "recent_start_year": recent_start_year,
    }
    result = citation_metrics(units, rows, evidence, **kwargs)
    assert result["basis"]["recent_start_year"] == 2023
    people = {p["inventor_id"]: p for p in result["people"]}
    for person, memberships in expected_memberships.items():
        row = people[person]
        if memberships is None:
            assert row["recent_activity"] is None
        else:
            unit = next(u for u in units if u.unit_id == "f")
            denominator = len(unit.inventor_keys) if person_weight == "fractional" else 1
            assert row["recent_activity"] == exact(Fraction(memberships, denominator))
        assert ("missing_activity_date" in row["unplottable_reasons"]) == (person in missing_people)
        assert row["raw_sum"] == row["activity"] == row["known_citation_activity"]
        assert row["partial_citation_coverage"] is False
    assert all(unit["citation_count"] == 1 for unit in result["units"])
    assert result["coverage"]["unit_citation_sum"] == exact(len(units))
    if person_weight == "fractional":
        assert result["coverage"]["allocated_citation_sum"] == exact(len(units))
    assert result == citation_metrics(units[::-1], rows[::-1], evidence[::-1], **kwargs)


@pytest.mark.parametrize("recent_start_year", [None, 2023])
def test_citation_recent_unknown_membership_does_not_read_system_clock(
    monkeypatch, recent_start_year
):
    import datetime
    import time

    import patent_analysis.inventor_models as models

    rows = (obs("r", ("A",), None), obs("anchor", ("Z",), "2025"))
    units = form_units(rows, unit="records")
    evidence = (citation("r", 0), citation("anchor", 0))
    kwargs = {"snapshot_date": "2025-01-01", "recent_start_year": recent_start_year}
    expected = citation_metrics(units, rows, evidence, **kwargs)

    def forbidden_clock(*args, **kwargs):
        raise AssertionError("recent activity must not read the system clock")

    class NoClockDate(datetime.date):
        today = classmethod(forbidden_clock)

    class NoClockDatetime(datetime.datetime):
        now = classmethod(forbidden_clock)
        utcnow = classmethod(forbidden_clock)

    with monkeypatch.context() as context:
        context.setattr(datetime, "date", NoClockDate)
        context.setattr(datetime, "datetime", NoClockDatetime)
        context.setattr(models, "date", NoClockDate)
        context.setattr(time, "time", forbidden_clock)
        result = citation_metrics(units, rows, evidence, **kwargs)
    assert result == expected
    assert result["people"][0]["recent_activity"] is None
