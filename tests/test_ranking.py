from __future__ import annotations

import csv
import hashlib
import json
import traceback
from pathlib import Path

import pytest

import patent_analysis.analysis as analysis_module
from patent_analysis import DatasetInputError, inspect_csv
from patent_analysis.analysis import AnalysisContractError
from patent_analysis.analysis import analyze_csv as _analyze_csv

RANKING_CASES_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "patent_analysis"
    / "schemas"
    / "ranking-cases.json"
)


def analyze_csv(source: Path, spec: dict) -> dict:
    return _analyze_csv(source, spec, allowed_root=source.parent)


def _write_csv(
    source: Path,
    header: str,
    rows: list[dict[str, str]],
    *,
    encoding: str = "utf-8",
) -> None:
    with source.open("w", encoding=encoding, newline="") as handle:
        writer = csv.writer(handle)
        columns = header.split(",")
        writer.writerow(columns)
        writer.writerows([row.get(column, "") for column in columns] for row in rows)


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_ranking_cases() -> dict:
    return json.loads(RANKING_CASES_PATH.read_text(encoding="utf-8"))


def _run_case(tmp_path: Path, case: dict) -> dict:
    source = tmp_path / "case.csv"
    _write_csv(source, case["header"], case["rows"])
    result = analyze_csv(source, case["spec"])
    return result["result"]


def _assert_row(
    result_rows: list[dict[str, object]],
    position: int,
    *,
    row_kind: str,
    label: str,
    value: float | int,
    count: int,
    share: float,
) -> None:
    assert result_rows[position]["row_kind"] == row_kind
    assert result_rows[position]["label"] == label
    assert result_rows[position]["value"] == value
    assert result_rows[position]["count"] == count
    assert result_rows[position]["share"] == share


def test_average_fixture_with_other_bucket_reconstructs_workbench_example(tmp_path: Path) -> None:
    source = tmp_path / "average.csv"
    _write_csv(
        source,
        "出願人,被引用件数",
        [
            {"出願人": "A社", "被引用件数": "10"},
            {"出願人": "A社", "被引用件数": "20"},
            {"出願人": "B社", "被引用件数": "100"},
            {"出願人": "C社", "被引用件数": "200"},
        ],
    )

    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "average", "column": "被引用件数"},
        "top_n": 1,
        "include_other": True,
        "multi_value_mode": "all",
    }

    result = analyze_csv(source, spec)
    rows = result["result"]["rows"]

    assert result["result"]["population"] == {"input_rows": 4, "analyzed_rows": 4}
    assert result["result"]["analysis_type"] == "ranking"
    assert result["result"]["dimension"] == "出願人"
    assert result["result"]["measure"] == {"mode": "average", "column": "被引用件数"}
    assert result["result"]["warnings"] == []
    assert len(rows) == 2
    _assert_row(
        rows,
        0,
        row_kind="dimension_value",
        label="C社",
        value=200.0,
        count=1,
        share=0.25,
    )
    _assert_row(
        rows,
        1,
        row_kind="remainder",
        label="その他",
        value=43.333333333333336,
        count=3,
        share=0.75,
    )


def test_ranking_cases_json_covers_every_measure_mode() -> None:
    valid_cases = _load_ranking_cases()["valid"]
    assert {case["spec"]["measure"]["mode"] for case in valid_cases} == {
        "count",
        "sum",
        "average",
        "max",
        "min",
    }


@pytest.mark.parametrize(
    "case",
    _load_ranking_cases()["valid"],
    ids=lambda case: case["name"],
)
def test_ranking_cases_json_drives_required_aggregation_fixture(
    tmp_path: Path,
    case: dict,
) -> None:
    result = _run_case(tmp_path, case)
    expected = case["expected"]

    assert result["analysis_type"] == "ranking"
    assert result["dimension"] == case["spec"]["dimension"]
    assert result["measure"] == case["spec"]["measure"]
    assert result["population"] == expected["population"]
    assert result["warnings"] == []
    assert result["rows"] == expected["rows"]


def test_ranking_cases_json_drives_every_invalid_fixture(tmp_path: Path) -> None:
    cases = _load_ranking_cases()
    for case in cases["invalid"]:
        source = tmp_path / f"{case['name']}.csv"
        _write_csv(source, case["header"], case["rows"])

        with pytest.raises(AnalysisContractError) as caught:
            analyze_csv(source, case["spec"])

        assert caught.value.code == case["expected_error"]["code"]
        assert caught.value.retryable is case["expected_error"]["retryable"]
        assert caught.value.details == case["expected_error"]["details"]


def test_sum_nonpositive_total_other_uses_count_share_and_is_deterministic(
    tmp_path: Path,
) -> None:
    source = tmp_path / "sum-negative-total-other.csv"
    _write_csv(
        source,
        "出願人,値",
        [
            {"出願人": "A社", "値": "4"},
            {"出願人": "A社", "値": "6"},
            {"出願人": "B社", "値": "-20"},
        ],
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "sum", "column": "値"},
        "top_n": 1,
        "include_other": True,
        "multi_value_mode": "all",
    }

    first = analyze_csv(source, spec)
    second = analyze_csv(source, spec)

    assert first == second
    assert first["receipt"] == second["receipt"]
    assert first["result"]["rows"] == [
        {
            "row_kind": "dimension_value",
            "label": "A社",
            "value": 10.0,
            "count": 2,
            "share": 2 / 3,
        },
        {
            "row_kind": "remainder",
            "label": "その他",
            "value": -20.0,
            "count": 1,
            "share": 1 / 3,
        },
    ]


def test_count_with_multivalue_all_and_deduplicated_buckets(tmp_path: Path) -> None:
    source = tmp_path / "count-all.csv"
    _write_csv(
        source,
        "出願人,被引用件数",
        [
            {"出願人": "A社|B社", "被引用件数": "10"},
            {"出願人": "A社", "被引用件数": "20"},
            {"出願人": "   ", "被引用件数": "30"},
            {"出願人": "C社", "被引用件数": "40"},
        ],
    )

    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "count", "column": None},
        "top_n": 2,
        "include_other": True,
        "multi_value_mode": "all",
    }

    result = analyze_csv(source, spec)
    rows = result["result"]["rows"]

    assert result["result"]["population"] == {"input_rows": 4, "analyzed_rows": 5}
    assert len(rows) == 3
    _assert_row(
        rows, 0, row_kind="dimension_value", label="A社", value=2, count=2, share=0.4
    )
    _assert_row(
        rows,
        1,
        row_kind="dimension_value",
        label="(空白)",
        value=1,
        count=1,
        share=0.2,
    )
    _assert_row(
        rows, 2, row_kind="remainder", label="その他", value=2, count=2, share=0.4
    )
    assert rows[2]["label"] == "その他"


def test_multi_value_first_mode_uses_only_first_label_and_preserves_first_blank_bucket(
    tmp_path: Path,
) -> None:
    source = tmp_path / "first-mode.csv"
    _write_csv(
        source,
        "出願人,件数",
        [
            {"出願人": "A社|A社|B社", "件数": "1"},
            {"出願人": "", "件数": "2"},
        ],
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "count", "column": None},
        "top_n": 10,
        "include_other": False,
        "multi_value_mode": "first",
    }

    result = analyze_csv(source, spec)
    rows = result["result"]["rows"]

    assert len(rows) == 2
    _assert_row(
        rows,
        0,
        row_kind="dimension_value",
        label="(空白)",
        value=1,
        count=1,
        share=0.5,
    )
    _assert_row(
        rows, 1, row_kind="dimension_value", label="A社", value=1, count=1, share=0.5
    )


def test_ties_use_python_unicode_code_point_label_order(tmp_path: Path) -> None:
    source = tmp_path / "code-point-ties.csv"
    _write_csv(
        source,
        "出願人,件数",
        [
            {"出願人": "あ", "件数": "1"},
            {"出願人": "a", "件数": "1"},
            {"出願人": "Z", "件数": "1"},
            {"出願人": "", "件数": "1"},
        ],
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "count", "column": None},
        "top_n": 10,
        "include_other": False,
        "multi_value_mode": "all",
    }

    result = analyze_csv(source, spec)

    assert [row["label"] for row in result["result"]["rows"]] == ["(空白)", "Z", "a", "あ"]


@pytest.mark.parametrize(
    "mode,expected_labels,analyzed_rows,shares",
    [
        (
            "all",
            {"A社": 3, "(空白)": 1, "B社": 1},
            5,
            {"A社": 0.6, "(空白)": 0.2, "B社": 0.2},
        ),
        (
            "first",
            {"A社": 3, "(空白)": 1},
            4,
            {"A社": 0.75, "(空白)": 0.25},
        ),
    ],
)
def test_split_multi_value_discards_empty_tokens_for_trailing_and_consecutive_delimiters(
    tmp_path: Path,
    mode: str,
    expected_labels: dict[str, int],
    analyzed_rows: int,
    shares: dict[str, float],
) -> None:
    source = tmp_path / "empty-tokens.csv"
    _write_csv(
        source,
        "出願人,件数",
        [
            {"出願人": "A社|", "件数": "1"},
            {"出願人": "|A社", "件数": "1"},
            {"出願人": "A社||B社", "件数": "1"},
            {"出願人": "|||", "件数": "1"},
        ],
    )

    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "count", "column": None},
        "top_n": 10,
        "include_other": False,
        "multi_value_mode": mode,
    }

    result = analyze_csv(source, spec)
    rows = result["result"]["rows"]
    assert result["result"]["population"] == {"input_rows": 4, "analyzed_rows": analyzed_rows}
    if mode == "all":
        assert len(rows) == 3
    else:
        assert len(rows) == 2

    for row in rows:
        assert row["row_kind"] == "dimension_value"
        assert row["value"] == expected_labels[row["label"]]
        assert row["count"] == expected_labels[row["label"]]
        assert row["share"] == shares[row["label"]]


@pytest.mark.parametrize(
    "mode,expected_rows,spec_measure_column",
    [
        (
            "count",
            [
                {
                    "row_kind": "dimension_value",
                    "label": "A社",
                    "value": 2,
                    "count": 2,
                    "share": 2 / 3,
                },
                {
                    "row_kind": "dimension_value",
                    "label": "B社",
                    "value": 1,
                    "count": 1,
                    "share": 1 / 3,
                },
            ],
            None,
        ),
        (
            "sum",
            [
                {
                    "row_kind": "dimension_value",
                    "label": "A社",
                    "value": 30.0,
                    "count": 2,
                    "share": 0.5,
                },
                {
                    "row_kind": "dimension_value",
                    "label": "B社",
                    "value": 30.0,
                    "count": 1,
                    "share": 0.5,
                },
            ],
            "値",
        ),
        (
            "average",
            [
                {
                    "row_kind": "dimension_value",
                    "label": "B社",
                    "value": 30.0,
                    "count": 1,
                    "share": 1 / 3,
                },
                {
                    "row_kind": "dimension_value",
                    "label": "A社",
                    "value": 15.0,
                    "count": 2,
                    "share": 2 / 3,
                },
            ],
            "値",
        ),
        (
            "max",
            [
                {
                    "row_kind": "dimension_value",
                    "label": "B社",
                    "value": 30.0,
                    "count": 1,
                    "share": 1 / 3,
                },
                {
                    "row_kind": "dimension_value",
                    "label": "A社",
                    "value": 20.0,
                    "count": 2,
                    "share": 2 / 3,
                },
            ],
            "値",
        ),
        (
            "min",
            [
                {
                    "row_kind": "dimension_value",
                    "label": "B社",
                    "value": 30.0,
                    "count": 1,
                    "share": 1 / 3,
                },
                {
                    "row_kind": "dimension_value",
                    "label": "A社",
                    "value": 10.0,
                    "count": 2,
                    "share": 2 / 3,
                },
            ],
            "値",
        ),
    ],
)
def test_supported_measure_modes_are_aggregated(
    tmp_path: Path,
    mode: str,
    expected_rows: list[dict[str, object]],
    spec_measure_column: str | None,
) -> None:
    source = tmp_path / "measures.csv"
    _write_csv(
        source,
        "出願人,値",
        [
            {"出願人": "A社", "値": "10"},
            {"出願人": "A社", "値": "20"},
            {"出願人": "B社", "値": "30"},
        ],
    )

    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": mode, "column": spec_measure_column},
        "top_n": 10,
        "include_other": False,
        "multi_value_mode": "all",
    }

    result = analyze_csv(source, spec)
    rows = result["result"]["rows"]

    assert rows == expected_rows


@pytest.mark.parametrize(
    "dimension,rows,expected_rows",
    [
        (
            "IPCサブクラス",
            [{"IPCサブクラス": "A61K, A61Q", "値": "10"}],
            [
                {
                    "row_kind": "dimension_value",
                    "label": "A61K",
                    "value": 1,
                    "count": 1,
                    "share": 0.5,
                },
                {
                    "row_kind": "dimension_value",
                    "label": "A61Q",
                    "value": 1,
                    "count": 1,
                    "share": 0.5,
                },
            ],
        ),
        (
            "IPCメイングループ",
            [{"IPCメイングループ": "A22,B99", "値": "10"}],
            [
                {
                    "row_kind": "dimension_value",
                    "label": "A22",
                    "value": 1,
                    "count": 1,
                    "share": 0.5,
                },
                {
                    "row_kind": "dimension_value",
                    "label": "B99",
                    "value": 1,
                    "count": 1,
                    "share": 0.5,
                },
            ],
        ),
        (
            "ipc",
            [{"ipc": "A1, A2, A3", "値": "10"}],
            [
                {
                    "row_kind": "dimension_value",
                    "label": "A1",
                    "value": 1,
                    "count": 1,
                    "share": 1 / 3,
                },
                {
                    "row_kind": "dimension_value",
                    "label": "A2",
                    "value": 1,
                    "count": 1,
                    "share": 1 / 3,
                },
                {
                    "row_kind": "dimension_value",
                    "label": "A3",
                    "value": 1,
                    "count": 1,
                    "share": 1 / 3,
                },
            ],
        ),
        (
            "F term",
            [{"F term": "F1, F2", "値": "10"}],
            [
                {
                    "row_kind": "dimension_value",
                    "label": "F1",
                    "value": 1,
                    "count": 1,
                    "share": 0.5,
                },
                {
                    "row_kind": "dimension_value",
                    "label": "F2",
                    "value": 1,
                    "count": 1,
                    "share": 0.5,
                },
            ],
        ),
        (
            "摘要",
            [{"摘要": "A61K, A61Q", "値": "10"}],
            [
                {
                    "row_kind": "dimension_value",
                    "label": "A61K, A61Q",
                    "value": 1,
                    "count": 1,
                    "share": 1,
                },
            ],
        ),
        (
            "fターム",
            [{"fターム": "F1, F2", "値": "10"}],
            [
                {
                    "row_kind": "dimension_value",
                    "label": "F1, F2",
                    "value": 1,
                    "count": 1,
                    "share": 1,
                }
            ],
        ),
    ],
)
def test_classification_detection_controls_comma_splitting(
    tmp_path: Path,
    dimension: str,
    rows: list[dict[str, str]],
    expected_rows: list[dict[str, object]],
) -> None:
    source = tmp_path / "classification.csv"
    _write_csv(
        source,
        f"{dimension},値",
        rows,
    )

    spec = {
        "analysis_type": "ranking",
        "dimension": dimension,
        "measure": {"mode": "count", "column": None},
        "top_n": 10,
        "include_other": False,
        "multi_value_mode": "all",
    }
    result = analyze_csv(source, spec)
    rows = result["result"]["rows"]
    assert rows == expected_rows


def test_numeric_parsing_supports_thousands_and_citation_prefixes(tmp_path: Path) -> None:
    source = tmp_path / "numeric.csv"
    _write_csv(
        source,
        "出願人,被引用件数",
        [
            {"出願人": "A社", "被引用件数": "1,000"},
            {"出願人": "B社", "被引用件数": "被引用件数:2,000"},
            {"出願人": "C社", "被引用件数": " citation: 3,000"},
        ],
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "sum", "column": "被引用件数"},
        "top_n": 10,
        "include_other": False,
        "multi_value_mode": "all",
    }

    result = analyze_csv(source, spec)
    rows = result["result"]["rows"]

    assert rows[0] == {
        "row_kind": "dimension_value",
        "label": "C社",
        "value": 3000.0,
        "count": 1,
        "share": 0.5,
    }
    assert rows[1] == {
        "row_kind": "dimension_value",
        "label": "B社",
        "value": 2000.0,
        "count": 1,
        "share": 0.3333333333333333,
    }
    assert rows[2] == {
        "row_kind": "dimension_value",
        "label": "A社",
        "value": 1000.0,
        "count": 1,
        "share": 0.16666666666666666,
    }


@pytest.mark.parametrize(
    ("unicode_value", "ascii_value"),
    [
        ("１２", "12"),
        ("١٢", "12"),
        ("引用:１２", "引用:12"),
        ("citation:١٢", "citation:12"),
    ],
)
def test_numeric_grammar_rejects_unicode_digits_but_accepts_ascii_equivalent(
    tmp_path: Path,
    unicode_value: str,
    ascii_value: str,
) -> None:
    source = tmp_path / "unicode-digits.csv"
    _write_csv(
        source,
        "出願人,件数",
        [
            {"出願人": "Unicode社", "件数": unicode_value},
            {"出願人": "ASCII社", "件数": ascii_value},
        ],
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "sum", "column": "件数"},
        "top_n": 10,
        "include_other": False,
        "multi_value_mode": "all",
    }

    result = analyze_csv(source, spec)

    assert result["result"]["rows"] == [
        {
            "row_kind": "dimension_value",
            "label": "ASCII社",
            "value": 12.0,
            "count": 1,
            "share": 1.0,
        },
        {
            "row_kind": "dimension_value",
            "label": "Unicode社",
            "value": 0.0,
            "count": 1,
            "share": 0.0,
        },
    ]


@pytest.mark.parametrize(
    "value",
    [
        "1e308",
        "+10",
        "被引用件数 20",
        "被引用件数-20",
        "被引用件数:abc",
        "被引用件数: 3,000abc",
        "citation 20",
        "citation: 20 trailing",
        "9" * 309,
    ],
)
def test_numeric_grammar_rejects_invalid_formats(tmp_path: Path, value: str) -> None:
    source = tmp_path / "bad-numeric.csv"
    _write_csv(
        source,
        "出願人,件数",
        [
            {"出願人": "A社", "件数": value},
            {"出願人": "B社", "件数": "10"},
        ],
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "sum", "column": "件数"},
        "top_n": 10,
        "include_other": False,
        "multi_value_mode": "all",
    }
    result = analyze_csv(source, spec)
    rows = result["result"]["rows"]
    assert rows == [
        {
            "row_kind": "dimension_value",
            "label": "B社",
            "value": 10.0,
            "count": 1,
            "share": 1.0,
        },
        {
            "row_kind": "dimension_value",
            "label": "A社",
            "value": 0.0,
            "count": 1,
            "share": 0.0,
        },
    ]


def test_measurement_aggregate_overflow_raises_analysis_error_in_sum_mode(tmp_path: Path) -> None:
    finite_huge = "1" + ("0" * 308)
    source = tmp_path / "overflow.csv"
    _write_csv(
        source,
        "出願人,値",
        [
            {"出願人": "A社", "値": finite_huge},
            {"出願人": "A社", "値": finite_huge},
        ],
    )

    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "sum", "column": "値"},
        "top_n": 10,
        "include_other": False,
        "multi_value_mode": "all",
    }

    with pytest.raises(AnalysisContractError) as caught:
        analyze_csv(source, spec)
    assert caught.value.code == "analysis.invalid"
    assert caught.value.retryable is False
    assert caught.value.details == {}
    assert set(caught.value.as_dict()) == {"code", "message", "retryable", "details"}


def test_measurement_aggregate_overflow_raises_analysis_error_in_average_mode(
    tmp_path: Path,
) -> None:
    finite_huge = "1" + ("0" * 308)
    source = tmp_path / "overflow-average.csv"
    _write_csv(
        source,
        "出願人,値",
        [
            {"出願人": "A社", "値": finite_huge},
            {"出願人": "A社", "値": finite_huge},
        ],
    )

    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "average", "column": "値"},
        "top_n": 10,
        "include_other": False,
        "multi_value_mode": "all",
    }

    with pytest.raises(AnalysisContractError) as caught:
        analyze_csv(source, spec)
    assert caught.value.code == "analysis.invalid"
    assert caught.value.retryable is False
    assert caught.value.details == {}
    assert set(caught.value.as_dict()) == {"code", "message", "retryable", "details"}


def test_nonnumeric_cells_are_excluded_and_empty_numeric_bucket_is_zero(tmp_path: Path) -> None:
    source = tmp_path / "nonnumeric.csv"
    _write_csv(
        source,
        "出願人,値",
        [
            {"出願人": "A社", "値": "foo"},
            {"出願人": "B社", "値": "bar"},
            {"出願人": "C社", "値": "30"},
        ],
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "average", "column": "値"},
        "top_n": 10,
        "include_other": False,
        "multi_value_mode": "all",
    }

    result = analyze_csv(source, spec)
    rows = result["result"]["rows"]

    assert rows[0] == {
        "row_kind": "dimension_value",
        "label": "C社",
        "value": 30.0,
        "count": 1,
        "share": 1 / 3,
    }
    assert rows[1] == {
        "row_kind": "dimension_value",
        "label": "A社",
        "value": 0.0,
        "count": 1,
        "share": 1 / 3,
    }
    assert rows[2] == {
        "row_kind": "dimension_value",
        "label": "B社",
        "value": 0.0,
        "count": 1,
        "share": 1 / 3,
    }


def test_real_other_label_in_top_n_is_distinguishable_from_synthetic_remainder(
    tmp_path: Path,
) -> None:
    source = tmp_path / "real-and-synthetic-other.csv"
    _write_csv(
        source,
        "出願人,件数",
        [
            {"出願人": "その他", "件数": "1"},
            {"出願人": "その他", "件数": "2"},
            {"出願人": "その他", "件数": "3"},
            {"出願人": "A社", "件数": "4"},
            {"出願人": "A社", "件数": "5"},
            {"出願人": "B社", "件数": "6"},
        ],
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "count", "column": None},
        "top_n": 1,
        "include_other": True,
        "multi_value_mode": "all",
    }

    output = analyze_csv(source, spec)

    assert output["result"]["rows"] == [
        {
            "row_kind": "dimension_value",
            "label": "その他",
            "value": 3,
            "count": 3,
            "share": 0.5,
        },
        {
            "row_kind": "remainder",
            "label": "その他",
            "value": 3,
            "count": 3,
            "share": 0.5,
        },
    ]


def test_real_other_label_outside_top_n_is_absorbed_into_single_remainder(
    tmp_path: Path,
) -> None:
    source = tmp_path / "real-other-absorbed.csv"
    _write_csv(
        source,
        "出願人,件数",
        [
            {"出願人": "A社", "件数": "1"},
            {"出願人": "A社", "件数": "2"},
            {"出願人": "A社", "件数": "3"},
            {"出願人": "B社", "件数": "4"},
            {"出願人": "B社", "件数": "5"},
            {"出願人": "その他", "件数": "6"},
        ],
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "count", "column": None},
        "top_n": 2,
        "include_other": True,
        "multi_value_mode": "all",
    }

    output = analyze_csv(source, spec)

    assert output["result"]["rows"] == [
        {
            "row_kind": "dimension_value",
            "label": "A社",
            "value": 3,
            "count": 3,
            "share": 0.5,
        },
        {
            "row_kind": "dimension_value",
            "label": "B社",
            "value": 2,
            "count": 2,
            "share": 1 / 3,
        },
        {
            "row_kind": "remainder",
            "label": "その他",
            "value": 1,
            "count": 1,
            "share": 1 / 6,
        },
    ]


def test_include_other_true_emits_no_remainder_when_all_buckets_fit_top_n(
    tmp_path: Path,
) -> None:
    source = tmp_path / "no-remainder-needed.csv"
    _write_csv(
        source,
        "出願人,件数",
        [
            {"出願人": "A社", "件数": "1"},
            {"出願人": "B社", "件数": "2"},
        ],
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "count", "column": None},
        "top_n": 10,
        "include_other": True,
        "multi_value_mode": "all",
    }

    output = analyze_csv(source, spec)

    assert output["result"]["rows"] == [
        {
            "row_kind": "dimension_value",
            "label": "A社",
            "value": 1,
            "count": 1,
            "share": 0.5,
        },
        {
            "row_kind": "dimension_value",
            "label": "B社",
            "value": 1,
            "count": 1,
            "share": 0.5,
        },
    ]


def test_include_other_false_excludes_others_bucket(tmp_path: Path) -> None:
    source = tmp_path / "no-other.csv"
    _write_csv(
        source,
        "出願人,件数",
        [
            {"出願人": "A社", "件数": "1"},
            {"出願人": "A社", "件数": "2"},
            {"出願人": "B社", "件数": "3"},
            {"出願人": "C社", "件数": "4"},
        ],
    )

    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "count", "column": None},
        "top_n": 2,
        "include_other": False,
        "multi_value_mode": "all",
    }

    result = analyze_csv(source, spec)
    rows = result["result"]["rows"]

    assert len(rows) == 2
    _assert_row(
        rows, 0, row_kind="dimension_value", label="A社", value=2, count=2, share=0.5
    )
    _assert_row(
        rows, 1, row_kind="dimension_value", label="B社", value=1, count=1, share=0.25
    )
    assert all(row["row_kind"] != "remainder" for row in rows)


def test_invalid_specs_missing_dimension_or_measure_column_rejects_with_analysis_error(
    tmp_path: Path,
) -> None:
    source = tmp_path / "columns.csv"
    _write_csv(source, "出願人,値", [{"出願人": "A社", "値": "1"}])

    with pytest.raises(AnalysisContractError) as caught:
        analyze_csv(
            source,
            {
                "analysis_type": "ranking",
                "dimension": "無効",
                "measure": {"mode": "count", "column": None},
                "top_n": 10,
                "include_other": True,
                "multi_value_mode": "all",
            },
        )
    assert caught.value.code == "analysis.invalid"
    assert caught.value.details == {}

    with pytest.raises(AnalysisContractError) as caught:
        analyze_csv(
            source,
            {
                "analysis_type": "ranking",
                "dimension": "出願人",
                "measure": {"mode": "sum", "column": "無効"},
                "top_n": 10,
                "include_other": True,
                "multi_value_mode": "all",
            },
        )
    assert caught.value.code == "analysis.invalid"
    assert caught.value.details == {}


def test_analyze_csv_is_deterministic_and_receipt_hashes_are_reproducible(tmp_path: Path) -> None:
    source = tmp_path / "stable.csv"
    _write_csv(
        source,
        "出願人,値",
        [
            {"出願人": "A社", "値": "1"},
            {"出願人": "B社", "値": "2"},
            {"出願人": "B社", "値": "3"},
        ],
    )

    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "sum", "column": "値"},
        "top_n": 10,
        "include_other": True,
        "multi_value_mode": "all",
    }

    first = analyze_csv(source, spec)
    second = analyze_csv(source, spec)

    assert first == second
    assert first["receipt"]["result_sha256"] == second["receipt"]["result_sha256"]


def test_receipt_contains_exact_fields_and_canonical_hashes(tmp_path: Path) -> None:
    source = tmp_path / "receipt.csv"
    _write_csv(
        source,
        "出願人,被引用件数",
        [
            {"出願人": "A社", "被引用件数": "1"},
            {"出願人": "B社", "被引用件数": "2"},
        ],
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "count", "column": None},
        "top_n": 2,
        "include_other": False,
        "multi_value_mode": "all",
    }

    result = analyze_csv(source, spec)
    manifest = result["result"]["_manifest"] if "_manifest" in result["result"] else None
    assert manifest is None
    receipt = result["receipt"]

    assert set(receipt.keys()) == {
        "algorithm_id",
        "package_version",
        "input_sha256",
        "spec_sha256",
        "result_sha256",
    }
    assert result["ok"] is True
    assert result["analysis_contract_version"] == "1.0.0"
    assert "timestamp" not in json.dumps(result, ensure_ascii=False)
    assert "content" not in json.dumps(result, ensure_ascii=False)
    assert result["receipt"]["algorithm_id"] == "ranking.v1"
    assert result["receipt"]["package_version"] == "0.2.0"

    expected_input_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    assert result["receipt"]["input_sha256"] == expected_input_sha256
    assert result["receipt"]["spec_sha256"] == _canonical_sha256(spec)
    assert result["receipt"]["result_sha256"] == _canonical_sha256(result["result"])


def test_prepublication_row_kind_rebaseline_preserves_input_and_spec_hashes(
    tmp_path: Path,
) -> None:
    source = tmp_path / "characterization.csv"
    source.write_bytes(
        b"applicant,value\nA|B,0.1\nA,0.2\n,0.3\nC,0.4\nB|D,0.5\n"
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "applicant",
        "measure": {"mode": "average", "column": "value"},
        "top_n": 2,
        "include_other": True,
        "multi_value_mode": "all",
    }

    output = analyze_csv(source, spec)

    assert output["result"] == {
        "analysis_type": "ranking",
        "dimension": "applicant",
        "measure": {"mode": "average", "column": "value"},
        "population": {"input_rows": 5, "analyzed_rows": 7},
        "rows": [
            {
                "row_kind": "dimension_value",
                "label": "D",
                "value": 0.5,
                "count": 1,
                "share": 1 / 7,
            },
            {
                "row_kind": "dimension_value",
                "label": "C",
                "value": 0.4,
                "count": 1,
                "share": 1 / 7,
            },
            {
                "row_kind": "remainder",
                "label": "その他",
                "value": 0.24,
                "count": 5,
                "share": 5 / 7,
            },
        ],
        "warnings": [],
    }
    assert output["receipt"] == {
        "algorithm_id": "ranking.v1",
        "package_version": "0.2.0",
        "input_sha256": "980ddba0023704b1cbbed01ed65ef932ff83f86d0c60dd0b495d62c7285477ab",
        "spec_sha256": "8dd5b8476154afdace2e422c03f560f1bd073bb7738ed63b6318f082acc6da59",
        "result_sha256": "563f2a972c4080c6360cb1969a87b662f0c9a5b1032da1cba2fc78aca997ba79",
    }


def test_all_mode_enforces_exact_raw_token_budget_before_same_cell_deduplication(
    tmp_path: Path,
) -> None:
    exact_source = tmp_path / "raw-token-exact.csv"
    _write_csv(
        exact_source,
        "applicant,value",
        [{"applicant": "|".join(["same"] * 1_000), "value": "1"}],
    )
    over_source = tmp_path / "raw-token-over.csv"
    _write_csv(
        over_source,
        "applicant,value",
        [{"applicant": "|".join(["same"] * 1_001), "value": "1"}],
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "applicant",
        "measure": {"mode": "count", "column": None},
        "top_n": 10,
        "include_other": False,
        "multi_value_mode": "all",
    }

    exact = analyze_csv(exact_source, spec)
    assert exact["result"]["population"]["analyzed_rows"] == 1

    with pytest.raises(DatasetInputError) as caught:
        analyze_csv(over_source, spec)
    assert caught.value.as_dict() == {
        "code": "input.invalid",
        "message": "ranking expansion exceeds published limits",
        "retryable": False,
        "details": {},
    }


def test_first_mode_stops_before_validating_an_over_budget_trailing_tail(
    tmp_path: Path,
) -> None:
    source = tmp_path / "first-long-tail.csv"
    _write_csv(
        source,
        "applicant,value",
        [{"applicant": "first|" + "|".join(["unused"] * 2_000), "value": "1"}],
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "applicant",
        "measure": {"mode": "count", "column": None},
        "top_n": 10,
        "include_other": False,
        "multi_value_mode": "first",
    }

    output = analyze_csv(source, spec)

    assert output["result"]["population"] == {"input_rows": 1, "analyzed_rows": 1}
    assert output["result"]["rows"] == [
        {
            "row_kind": "dimension_value",
            "label": "first",
            "value": 1,
            "count": 1,
            "share": 1.0,
        }
    ]


def test_expanded_contribution_budget_allows_exact_limit_and_rejects_next(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        analysis_module, "MAX_EXPANDED_CONTRIBUTIONS", 2, raising=False
    )
    exact_source = tmp_path / "contribution-exact.csv"
    _write_csv(
        exact_source,
        "applicant,value",
        [{"applicant": "A|B", "value": "1"}],
    )
    over_source = tmp_path / "contribution-over.csv"
    _write_csv(
        over_source,
        "applicant,value",
        [{"applicant": "A|B|C", "value": "1"}],
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "applicant",
        "measure": {"mode": "count", "column": None},
        "top_n": 10,
        "include_other": False,
        "multi_value_mode": "all",
    }

    exact = analyze_csv(exact_source, spec)
    assert exact["result"]["population"]["analyzed_rows"] == 2

    with pytest.raises(DatasetInputError):
        analyze_csv(over_source, spec)


def test_distinct_bucket_budget_allows_exact_limit_and_rejects_next(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(analysis_module, "MAX_DISTINCT_BUCKETS", 2, raising=False)
    exact_source = tmp_path / "bucket-exact.csv"
    _write_csv(
        exact_source,
        "applicant,value",
        [{"applicant": "A|B", "value": "1"}],
    )
    over_source = tmp_path / "bucket-over.csv"
    _write_csv(
        over_source,
        "applicant,value",
        [{"applicant": "A|B|C", "value": "1"}],
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "applicant",
        "measure": {"mode": "count", "column": None},
        "top_n": 10,
        "include_other": False,
        "multi_value_mode": "all",
    }

    exact = analyze_csv(exact_source, spec)
    assert exact["result"]["population"]["analyzed_rows"] == 2

    with pytest.raises(DatasetInputError):
        analyze_csv(over_source, spec)


def test_budget_error_does_not_retain_secret_input_or_exception_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        analysis_module, "MAX_DIMENSION_TOKENS_PER_CELL", 1, raising=False
    )
    secret_label = "SECRET-LABEL-VALUE"
    source = tmp_path / "SECRET-DATASET-PATH.csv"
    _write_csv(
        source,
        "applicant,value",
        [{"applicant": f"safe|{secret_label}", "value": "SECRET-CELL-VALUE"}],
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "applicant",
        "measure": {"mode": "count", "column": None},
        "top_n": 10,
        "include_other": False,
        "multi_value_mode": "all",
    }

    with pytest.raises(DatasetInputError) as caught:
        analyze_csv(source, spec)

    error = caught.value
    rendered = "\n".join(
        [repr(error), json.dumps(error.as_dict()), *traceback.format_exception(error)]
    )
    assert error.__cause__ is None
    assert error.__context__ is None
    assert getattr(error, "__notes__", None) is None
    assert error.as_dict() == {
        "code": "input.invalid",
        "message": "ranking expansion exceeds published limits",
        "retryable": False,
        "details": {},
    }
    for secret in (str(source), source.name, secret_label, "SECRET-CELL-VALUE"):
        assert secret not in rendered


def test_inspect_csv_is_unaffected_by_analysis_only_budgets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        analysis_module, "MAX_DIMENSION_TOKENS_PER_CELL", 0, raising=False
    )
    monkeypatch.setattr(
        analysis_module, "MAX_EXPANDED_CONTRIBUTIONS", 0, raising=False
    )
    monkeypatch.setattr(analysis_module, "MAX_DISTINCT_BUCKETS", 0, raising=False)
    source = tmp_path / "inspect-only.csv"
    _write_csv(
        source,
        "applicant,value",
        [{"applicant": "A|B", "value": "1"}],
    )

    manifest = inspect_csv(source, allowed_root=tmp_path)

    assert manifest["row_count"] == 1
    assert manifest["columns"] == ["applicant", "value"]


def test_other_uses_bucket_insertion_order_for_floating_point_addition(
    tmp_path: Path,
) -> None:
    source = tmp_path / "other-float-order.csv"
    _write_csv(
        source,
        "applicant,value",
        [
            {"applicant": "A", "value": "20000000000000000"},
            {"applicant": "B", "value": "10000000000000000"},
            {"applicant": "C", "value": "-10000000000000000"},
            {"applicant": "B", "value": "1"},
        ],
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "applicant",
        "measure": {"mode": "sum", "column": "value"},
        "top_n": 1,
        "include_other": True,
        "multi_value_mode": "all",
    }

    output = analyze_csv(source, spec)

    assert output["result"]["rows"] == [
        {
            "row_kind": "dimension_value",
            "label": "A",
            "value": 2e16,
            "count": 1,
            "share": 1.0,
        },
        {
            "row_kind": "remainder",
            "label": "その他",
            "value": 0.0,
            "count": 3,
            "share": 0.0,
        },
    ]
