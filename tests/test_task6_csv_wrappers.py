from __future__ import annotations

from pathlib import Path

import pytest

from patent_analysis._render_canonical import canonical_json_bytes
from patent_analysis.v2_contracts import validate_analysis_result_v2


def _base_spec(analysis_id: str, parameters: dict[str, object]) -> dict[str, object]:
    return {
        "analysis_contract_version": "2.0.0",
        "analysis_id": analysis_id,
        "resolution": {"bindings": {}},
        "normalization": {"profiles": []},
        "population": {
            "filters": [],
            "selection_sets": [],
            "family_mode": "records",
        },
        "parameters": parameters,
    }


def test_timeline_csv_uses_shared_records_pipeline_and_returns_v2_envelope(
    tmp_path: Path,
) -> None:
    from patent_analysis.analyses.timeline import analyze_timeline_csv

    source = tmp_path / "timeline.csv"
    source.write_text(
        "filing_date,applicant,score\n"
        "2021-03-04,A社,10\n"
        "2020,B社,20\n"
        "2021,A社|B社,30\n"
        "invalid,C社,40\n",
        encoding="utf-8",
    )
    spec = _base_spec(
        "timeline.v1",
        {
            "date_role": "filing_date",
            "series_role": "applicant",
            "top_n": 10,
            "include_other": True,
            "measure": "count",
        },
    )
    spec["resolution"] = {
        "bindings": {
            "filing_date": "filing_date",
            "applicant": "applicant",
        }
    }

    first = analyze_timeline_csv(source.name, spec, allowed_root=tmp_path)
    second = analyze_timeline_csv(source.name, spec, allowed_root=tmp_path)

    assert validate_analysis_result_v2(first) == first
    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    assert first["analysis_id"] == "timeline.v1"
    assert first["result_variant"] == "series"
    assert first["population"] == {
        "input_rows": 4,
        "analyzed_rows": 3,
        "excluded_rows": 1,
    }
    data = first["data"]
    assert data["x"] == ["2020", "2021"]
    assert [item["label"] for item in data["series"]] == ["A社", "B社"]
    assert [item["values"] for item in data["series"]] == [[0, 2], [1, 1]]
    assert data["population"]["invalid_year_rows"] == 1


def test_composition_csv_uses_shared_records_pipeline_and_preserves_share_semantics(
    tmp_path: Path,
) -> None:
    from patent_analysis.analyses.composition import analyze_composition_csv

    source = tmp_path / "composition.csv"
    source.write_text(
        "applicant,score\n"
        "A社,10\n"
        "B社,-2\n"
        "B社,-3\n"
        ",8\n",
        encoding="utf-8",
    )
    spec = _base_spec(
        "composition.v1",
        {
            "role": "applicant",
            "top_n": 10,
            "include_other": False,
            "measure": "sum",
            "measure_role": "score",
        },
    )
    spec["resolution"] = {
        "bindings": {
            "applicant": "applicant",
            "score": "score",
        }
    }

    first = analyze_composition_csv(source.name, spec, allowed_root=tmp_path)
    second = analyze_composition_csv(source.name, spec, allowed_root=tmp_path)

    assert validate_analysis_result_v2(first) == first
    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    assert first["analysis_id"] == "composition.v1"
    assert first["result_variant"] == "composition"
    assert first["population"] == {
        "input_rows": 4,
        "analyzed_rows": 3,
        "excluded_rows": 1,
    }
    items = first["data"]["items"]
    assert [item["label"] for item in items] == ["A社", "B社"]
    assert [item["value"] for item in items] == [10, -5]
    assert [item["row_count"] for item in items] == [1, 2]
    assert [item["share_basis"] for item in items] == [
        "row_count",
        "row_count",
    ]
    assert [item["share"] for item in items] == [1 / 3, 2 / 3]


@pytest.mark.parametrize("analysis_id", ["composition.v1", "timeline.v1", "matrix.v1"])
@pytest.mark.parametrize("include_other", [False, True])
def test_source_other_labels_remain_distinct_through_public_analysis_and_chart_model(
    tmp_path: Path, analysis_id: str, include_other: bool,
) -> None:
    from patent_analysis import run_analysis_csv
    from patent_analysis.chart_models.composition import build_composition_chart_model
    from patent_analysis.chart_models.matrix import build_matrix_chart_model
    from patent_analysis.chart_models.series import build_series_chart_model

    labels = ["その他（上位外）", "その他（上位外） [2]", "その他（上位外） [3]", "Z社"]
    counts = [5, 4, 3, 2]
    source = tmp_path / "labels.csv"
    raw = ("topic,filing_date,axis\n" + "".join(
        f"{label},2020,{label}\n" * count
        for label, count in zip(labels, counts, strict=True)
    )).encode("utf-8")
    source.write_bytes(raw)
    limit = 2 if include_other else 4
    parameters = {
        "composition.v1": {"role": "topic", "top_n": limit,
                           "include_other": include_other, "measure": "count"},
        "timeline.v1": {"date_role": "filing_date", "series_role": "topic",
                        "top_n": limit, "include_other": include_other, "measure": "count"},
        "matrix.v1": {"x_role": "topic", "y_role": "axis", "x_limit": limit,
                      "y_limit": limit, "include_axis_other": include_other,
                      "measure": "count"},
    }[analysis_id]
    spec = _base_spec(analysis_id, parameters)
    bindings = {"topic": "topic"}
    if analysis_id == "matrix.v1":
        bindings["axis"] = "axis"
    elif analysis_id == "timeline.v1":
        bindings["filing_date"] = "filing_date"
    spec["resolution"] = {"bindings": bindings}
    document = run_analysis_csv(source, canonical_json_bytes(spec), allowed_root=tmp_path)
    result = document
    data = result["data"]
    expected_labels = labels[:2] + ["その他（上位外） [4]"] if include_other else labels
    expected_counts = [5, 4, 5] if include_other else counts
    expected_flags = [False, False, True] if include_other else [False] * 4
    if analysis_id == "composition.v1":
        items = data["items"]
        assert [i["value"] for i in items] == expected_counts
        assert [i["share"] for i in items] == pytest.approx([n / 14 for n in expected_counts])
        model, _ = build_composition_chart_model(result, mark="composition-pie-svg.v1")
        assert model["items"] == items
    elif analysis_id == "timeline.v1":
        items = data["series"]
        assert [i["values"] for i in items] == [[n] for n in expected_counts]
        model, _ = build_series_chart_model(result, mark="series-line-svg.v1")
        assert model["series"] == items
    else:
        items = data["x_axis"]["categories"]
        assert data["y_axis"]["categories"] == items
        assert [i["count"] for i in items] == expected_counts
        assert [(c["x_index"], c["y_index"], c["value"]) for c in data["cells"]] == [
            (i, i, n) for i, n in enumerate(expected_counts)
        ]
        model, _ = build_matrix_chart_model(result, mark="matrix-heatmap-svg.v1")
        assert [i["label"] for i in model["x_axis"]["categories"]] == expected_labels
    assert [i["label"] for i in items] == expected_labels
    assert [i["is_other"] for i in items] == expected_flags
    repeated = run_analysis_csv(source, canonical_json_bytes(spec), allowed_root=tmp_path)
    assert canonical_json_bytes(repeated) == canonical_json_bytes(document)
    assert source.read_bytes() == raw
