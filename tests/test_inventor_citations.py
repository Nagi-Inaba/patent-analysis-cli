import pytest
from test_inventor_graph import obs

from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_citations import citation_metrics
from patent_analysis.inventor_units import form_units


def citation(record, count, snapshot="2025-01-01", citing_ids=None, suffix=""):
    return {
        "citation_id": record + suffix,
        "record_id": record,
        "count": count,
        "snapshot_date": snapshot,
        "citing_ids": citing_ids,
        "source_ids": ("s",),
    }


def test_snapshot_zero_missing_fractional_conservation_and_same_filing_cohort():
    rows = tuple(obs(str(i), ("A", "B"), "2022", ("X",)) for i in range(5)) + (
        obs("missing", ("C",), "2024", ("X",)),
    )
    units = form_units(rows, unit="records")
    evidence = tuple(citation(str(i), i) for i in range(5)) + (
        citation("0", 99, snapshot="2024-01-01", suffix="old"),
    )
    result = citation_metrics(
        units, rows, evidence, snapshot_date="2025-01-01", person_weight="fractional"
    )
    a, b, c = result["people"]
    assert a["activity"]["value"] == 2.5
    assert a["raw_sum"]["value"] == 5.0
    assert a["raw_mean"]["value"] == 2.0
    assert a["adjusted_mean"]["value"] == 1.0
    assert a["recent_activity"]["value"] == 2.5
    assert b["raw_sum"] == a["raw_sum"]
    assert c["raw_sum"] is None
    assert "missing_citations" in c["unplottable_reasons"]
    assert result["cohorts"][0]["distinct_units"] == 5
    assert result["coverage"]["unit_citation_sum"]["value"] == 10
    assert result["coverage"]["allocated_citation_sum"]["value"] == 10
    assert result["coverage"]["known_zero_units"] == 1
    assert result["coverage"]["selected_source_ids"] == ["s"]
    assert result["basis"]["recent_start_year"] == 2022
    assert result == citation_metrics(
        units[::-1],
        rows[::-1],
        evidence[::-1],
        snapshot_date="2025-01-01",
        person_weight="fractional",
    )
    with pytest.raises(DatasetInputError):
        citation_metrics(
            units,
            rows,
            evidence + (citation("0", 8, suffix="conflict"),),
            snapshot_date="2025-01-01",
        )


def test_family_union_requires_ids_or_explicit_representative_not_count_sum():
    rows = (
        obs("1", ("A", "B"), "2022", ("X",), family_id="f"),
        obs("2", ("B", "C"), "2022", ("Y",), family_id="f"),
    )
    units = form_units(rows, unit="family")
    counts = (citation("1", 2), citation("2", 2))
    with pytest.raises(DatasetInputError):
        citation_metrics(units, rows, counts, snapshot_date="2025-01-01")
    with pytest.raises(DatasetInputError):
        citation_metrics(
            units, rows, counts, snapshot_date="2025-01-01", citation_basis="representative_record"
        )
    representative = citation_metrics(
        units,
        rows,
        counts,
        snapshot_date="2025-01-01",
        citation_basis="representative_record",
        representative_records={"f": "2"},
        person_weight="fractional",
    )
    assert representative["coverage"]["allocated_citation_sum"]["value"] == 2
    ids = (citation("1", 2, citing_ids=("u", "v")), citation("2", 2, citing_ids=("v", "w")))
    result = citation_metrics(
        units,
        rows,
        ids,
        snapshot_date="2025-01-01",
        citation_basis="unique_citing_ids",
        person_weight="fractional",
    )
    assert result["units"][0]["citation_count"] == 3
    assert result["coverage"]["allocated_citation_sum"]["value"] == 3
    assert all(p["raw_sum"]["value"] == 1 for p in result["people"])
    assert result["cohorts"][0]["reference_weight"]["denominator"] == "2"
    missing = citation_metrics(
        units, rows, counts, snapshot_date="2025-01-01", citation_basis="unique_citing_ids"
    )
    assert missing["units"][0]["citation_count"] is None


@pytest.mark.parametrize(
    "minimum,counts,reason",
    [(5, [2, 4], "insufficient_cohort_units"), (2, [0, 0], "zero_cohort_mean")],
)
def test_zero_or_insufficient_baselines_null_never_silently_zero(minimum, counts, reason):
    rows = tuple(obs(str(i), ("A",), "2020", ("X",)) for i in range(2))
    evidence = tuple(citation(str(i), value) for i, value in enumerate(counts))
    result = citation_metrics(
        form_units(rows, unit="records"),
        rows,
        evidence,
        snapshot_date="2025-01-01",
        min_cohort_units=minimum,
    )
    assert result["people"][0]["adjusted_mean"] is None
    assert reason in result["people"][0]["unplottable_reasons"]
    assert result["people"][0]["raw_mean"]["value"] == sum(counts) / 2
    assert result == citation_metrics(
        form_units(rows, unit="records"),
        rows,
        evidence + (evidence[0],),
        snapshot_date="2025-01-01",
        min_cohort_units=minimum,
    )


def test_citation_date_issues_ambiguous_reserved_and_no_system_clock():
    from patent_analysis.inventor_identity import Alias, IdentityResolver

    ambiguous = IdentityResolver((Alias("id", "X", "x", "x", ("s",), "candidate"),)).resolve(
        inventor_id="X"
    )
    rows = (obs("1", ("A", ambiguous), None, ("X",)),)
    result = citation_metrics(
        form_units(rows, unit="records"),
        rows,
        (citation("1", 10),),
        snapshot_date="2025-01-01",
        person_weight="fractional",
    )
    assert result["basis"]["recent_start_year"] is None
    assert result["coverage"]["reserved_ambiguous_citations"]["value"] == 5
    assert result["coverage"]["allocated_citation_sum"]["value"] == 10
    assert "ambiguous_identity" in result["people"][0]["unplottable_reasons"]
    assert all(
        p["recent_activity"] is None and p["adjusted_mean"] is None for p in result["people"]
    )
    assert all("missing_filing_date" in p["unplottable_reasons"] for p in result["people"])


@pytest.mark.parametrize(
    "field,value",
    [
        ("record_id", []),
        ("count", True),
        ("source_ids", ("s", "s")),
        ("citing_ids", ("u", "u")),
        ("snapshot_date", None),
    ],
)
def test_invalid_citation_evidence_shape_has_safe_input_error(field, value):
    rows = (obs("1", ("A",), "2022", ("X",)),)
    evidence = citation("1", 2)
    evidence[field] = value
    with pytest.raises(DatasetInputError):
        citation_metrics(
            form_units(rows, unit="records"), rows, (evidence,), snapshot_date="2025-01-01"
        )


def test_publication_consensus_deduplicates_counts_and_rejects_conflicts():
    rows = (
        obs("a", ("A",), "2020", ("X",), publication_id="p"),
        obs("b", ("A",), "2020", ("X",), publication_id="p"),
    )
    units = form_units(rows, unit="publication")
    result = citation_metrics(
        units, rows, (citation("a", 3), citation("b", 3)), snapshot_date="2025-01-01"
    )
    assert result["people"][0]["raw_sum"]["value"] == 3
    with pytest.raises(DatasetInputError):
        citation_metrics(
            units, rows, (citation("a", 3), citation("b", 4)), snapshot_date="2025-01-01"
        )
    old = citation_metrics(
        units, rows, (citation("a", 3, snapshot="2024-01-01"),), snapshot_date="2025-01-01"
    )
    assert old["people"][0]["raw_sum"] is None
    assert old["coverage"]["other_snapshot_record_entries"] == 1


def test_family_mixed_filing_cohorts_not_implicitly_earliest():
    rows = (
        obs("a", ("A",), "2020", ("X",), family_id="f"),
        obs("b", ("A",), "2021", ("X",), family_id="f"),
    )
    result = citation_metrics(
        form_units(rows, unit="family"),
        rows,
        (citation("a", 3),),
        snapshot_date="2025-01-01",
        citation_basis="representative_record",
        representative_records={"f": "a"},
        min_cohort_units=1,
    )
    assert result["people"][0]["raw_sum"]["value"] == 3
    assert result["people"][0]["adjusted_mean"] is None
    assert "multiple_filing_years" in result["people"][0]["unplottable_reasons"]
    assert result["units"][0]["filing_year"] is None
