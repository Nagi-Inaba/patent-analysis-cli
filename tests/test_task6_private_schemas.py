from __future__ import annotations

import json
from importlib.resources import files

from patent_analysis.analysis_contracts import StrictDraft202012Validator


def _schema(name: str) -> dict[str, object]:
    raw = files("patent_analysis").joinpath("schemas", name).read_text(encoding="utf-8")
    value = json.loads(raw)
    assert isinstance(value, dict)
    StrictDraft202012Validator.check_schema(value)
    return value


def _valid(schema: dict[str, object], value: object) -> bool:
    return next(StrictDraft202012Validator(schema).iter_errors(value), None) is None


def test_timeline_result_schema_closes_canonical_year_and_series_shape() -> None:
    schema = _schema("timeline-result-v1.schema.json")
    value = {
        "schema_version": "1.0.0",
        "analysis_id": "timeline.v1",
        "algorithm_version": "1.0.0",
        "measure": {"mode": "count", "role": None},
        "x": ["2020", "2021"],
        "series": [
            {
                "label": "A社",
                "values": [1, 2],
                "row_counts": [1, 2],
                "is_other": False,
            }
        ],
        "population": {
            "input_rows": 3,
            "visible_rows": 3,
            "invalid_year_rows": 0,
            "outside_year_range_rows": 0,
            "blank_series_rows": 0,
            "excluded_rows": 0,
        },
        "contributions": 3,
        "limits": {"max_top_n": 100, "max_expanded_contributions": 1_000_000},
    }
    assert _valid(schema, value)
    value["x"] = ["Filed 2021"]
    assert not _valid(schema, value)


def test_composition_result_schema_requires_explicit_share_basis() -> None:
    schema = _schema("composition-result-v1.schema.json")
    value = {
        "schema_version": "1.0.0",
        "analysis_id": "composition.v1",
        "algorithm_version": "1.0.0",
        "measure": {"mode": "sum", "role": "score"},
        "items": [
            {
                "label": "A社",
                "value": 10,
                "row_count": 2,
                "share": 1.0,
                "share_basis": "value",
                "is_other": False,
            }
        ],
        "population": {
            "input_rows": 2,
            "visible_rows": 2,
            "blank_role_rows": 0,
            "excluded_rows": 0,
        },
        "contributions": 2,
        "limits": {"max_top_n": 100, "max_expanded_contributions": 500_000},
    }
    assert _valid(schema, value)
    del value["items"][0]["share_basis"]
    assert not _valid(schema, value)


def test_task6_parameter_schemas_require_measure_role_only_for_numeric_modes() -> None:
    timeline = _schema("timeline-parameters-v1.schema.json")
    composition = _schema("composition-parameters-v1.schema.json")

    base = {
        "analysis_contract_version": "2.0.0",
        "resolution": {},
        "normalization": {"profiles": []},
        "population": {"filters": [], "selection_sets": [], "family_mode": "records"},
    }
    timeline_count = {
        **base,
        "analysis_id": "timeline.v1",
        "parameters": {
            "date_role": "year",
            "series_role": "applicant",
            "measure": "count",
        },
    }
    assert _valid(timeline, timeline_count)

    timeline_sum = json.loads(json.dumps(timeline_count))
    timeline_sum["parameters"]["measure"] = "sum"
    assert not _valid(timeline, timeline_sum)
    timeline_sum["parameters"]["measure_role"] = "score"
    assert _valid(timeline, timeline_sum)

    composition_count = {
        **base,
        "analysis_id": "composition.v1",
        "parameters": {"role": "applicant", "measure": "count"},
    }
    assert _valid(composition, composition_count)

    composition_sum = json.loads(json.dumps(composition_count))
    composition_sum["parameters"]["measure"] = "sum"
    assert not _valid(composition, composition_sum)
    composition_sum["parameters"]["measure_role"] = "score"
    assert _valid(composition, composition_sum)
