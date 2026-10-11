import json

from test_inventor_foundation_sidecars import bundle, save
from test_inventor_public import spec, write_patents

from patent_analysis.analysis_runner import run_analysis


def citation_bundle():
    d = bundle()
    d["tables"]["citations"] = [
        dict(
            citation_id="c1",
            record_id="r1",
            count=0,
            snapshot_date="2025-01-01",
            citing_ids=[],
            source_ids=["s1"],
        ),
        dict(
            citation_id="c2",
            record_id="r2",
            count=None,
            snapshot_date="2025-01-01",
            citing_ids=None,
            source_ids=["s1"],
        ),
    ]
    return d


def test_impact_zero_unknown_and_minimum_filing_cohort(tmp_path):
    write_patents(tmp_path)
    save(tmp_path, citation_bundle())
    result = run_analysis(
        "patents.json",
        json.dumps(
            spec(
                "inventor-impact.v1",
                {
                    "snapshot_date": "2025-01-01",
                    "auxiliary": {"format": "json", "path": "sidecar.json"},
                },
            )
        ).encode(),
        allowed_root=tmp_path,
    )
    stats = result["data"]["statistics"]
    assert stats["coverage"]["known_zero_units"] == 1
    assert stats["coverage"]["missing_citation_units"] == 2
    assert stats["cohorts"][0]["undefined_reason"] == "insufficient_cohort_units"
    assert stats["people"][0]["raw_sum"]["value"] == 0
    assert stats["people"][-1]["raw_sum"] is None
    assert stats["basis"]["snapshot_date"] == "2025-01-01"
    evidence = result["data"]["citation_evidence"]
    assert [(row["record_id"], row["entry_state"], row["citation_count"]) for row in evidence] == [
        ("r1", "known", 0),
        ("r2", "unknown", None),
        ("r3", "entry_not_provided", None),
    ]
    assert evidence[1]["citation_ids"] == ["c2"] and evidence[1]["source_ids"] == ["s1"]


def test_impact_excluded_conflicting_citation_rows_still_rejected(tmp_path):
    import pytest

    from patent_analysis.errors import DatasetInputError

    write_patents(tmp_path)
    d = citation_bundle()
    d["tables"]["citations"].append(
        dict(d["tables"]["citations"][1], citation_id="conflict", count=2)
    )
    save(tmp_path, d)
    request = spec(
        "inventor-impact.v1",
        {"snapshot_date": "2025-01-01", "auxiliary": {"format": "json", "path": "sidecar.json"}},
    )
    request["population"]["filters"] = [
        dict(role="record_id", effect="include", match="exact", value="r1")
    ]
    with pytest.raises(DatasetInputError):
        run_analysis("patents.json", json.dumps(request).encode(), allowed_root=tmp_path)


def test_impact_five_distinct_units_adjustment_and_unknown_not_zero(tmp_path):
    rows = [
        dict(record=f"r{i}", people='["A","B"]', day="2022-01-01", ipc="A01B 1/00", org='["e1"]')
        for i in range(1, 7)
    ]
    (tmp_path / "patents.json").write_text(json.dumps(rows), encoding="utf-8")
    d = bundle()
    d["tables"]["citations"] = [
        dict(
            citation_id=f"c{i}",
            record_id=f"r{i}",
            count=i - 1 if i <= 5 else None,
            snapshot_date="2025-01-01",
            citing_ids=None,
            source_ids=["s1"],
        )
        for i in range(1, 7)
    ]
    save(tmp_path, d)
    request = spec(
        "inventor-impact.v1",
        {
            "snapshot_date": "2025-01-01",
            "person_weight": "fractional",
            "auxiliary": {"format": "json", "path": "sidecar.json"},
        },
    )
    result = run_analysis("patents.json", json.dumps(request).encode(), allowed_root=tmp_path)
    s = result["data"]["statistics"]
    assert s["coverage"]["known_zero_units"] == 1 and s["coverage"]["missing_citation_units"] == 1
    assert s["cohorts"][0]["distinct_units"] == 5 and s["cohorts"][0]["raw_mean"]["value"] == 2
    assert s["cohorts"][0]["undefined_reason"] is None
    assert s["people"][0]["raw_mean"]["value"] == 2 and s["people"][0]["partial_citation_coverage"]
    assert s["people"][0]["adjusted_mean"] is None
    request["population"]["filters"] = [
        dict(role="record_id", effect="exclude", match="exact", value="r6")
    ]
    complete = run_analysis("patents.json", json.dumps(request).encode(), allowed_root=tmp_path)
    assert complete["data"]["statistics"]["people"][0]["adjusted_mean"]["value"] == 1
    assert complete["data"]["statistics"]["people"][0]["raw_sum"]["numerator"] == "5"


def test_impact_sidecar_refs_are_full_input_before_filter(tmp_path):
    write_patents(tmp_path)
    save(tmp_path, citation_bundle())
    request = spec(
        "inventor-impact.v1",
        {"snapshot_date": "2025-01-01", "auxiliary": {"format": "json", "path": "sidecar.json"}},
    )
    request["population"]["filters"] = [
        dict(role="record_id", effect="include", match="exact", value="r1")
    ]
    result = run_analysis("patents.json", json.dumps(request).encode(), allowed_root=tmp_path)
    assert result["data"]["statistics"]["coverage"]["units"] == 1
