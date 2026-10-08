from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from patent_analysis.errors import DatasetInputError


def _write_json(path: Path, value: object) -> bytes:
    raw = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    path.write_bytes(raw)
    return raw


def test_single_patent_object_is_projected_to_dataset_v2(tmp_path: Path) -> None:
    from patent_analysis.dataset_v2 import read_dataset_v2

    source = tmp_path / "patent.json"
    raw = _write_json(
        source,
        {
            "input": "特願2024-102312",
            "found": True,
            "publication_no": ["JPpub2026-004092"],
            "title": "潅水制御システム",
            "application_date": "2024-06-25",
            "publication_date": "2026-01-14",
            "applicants": ["株式会社クボタ"],
            "inventors": ["片桐  康之", "片岡  麻子", "谷口  啓介"],
            "sections": {"title": "潅水制御システム", "abstract": "要約本文"},
            "truncated": {},
        },
    )

    dataset = read_dataset_v2(source.name, allowed_root=tmp_path)

    assert dataset.manifest.raw_header == (
        "input",
        "found",
        "publication_no",
        "title",
        "application_date",
        "publication_date",
        "applicants",
        "inventors",
        "sections.title",
        "sections.abstract",
        "truncated",
    )
    assert dataset.rows[0].values == (
        "特願2024-102312",
        "true",
        "JPpub2026-004092",
        "潅水制御システム",
        "2024-06-25",
        "2026-01-14",
        "株式会社クボタ",
        "片桐  康之|片岡  麻子|谷口  啓介",
        "潅水制御システム",
        "要約本文",
        "{}",
    )
    assert dataset.manifest.input_rows == 1
    assert dataset.manifest.encoding == "utf-8"
    assert dataset.manifest.preamble is None
    assert dataset.manifest.source_input_sha256 == hashlib.sha256(raw).hexdigest()


def test_json_array_uses_union_of_columns_and_blank_missing_values(tmp_path: Path) -> None:
    from patent_analysis.dataset_v2 import read_dataset_v2

    source = tmp_path / "patents.JSON"
    _write_json(source, [{"title": "A"}, {"title": "B", "applicants": ["X", "Y"]}])

    dataset = read_dataset_v2(source.name, allowed_root=tmp_path)

    assert dataset.manifest.raw_header == ("title", "applicants")
    assert [row.values for row in dataset.rows] == [("A", ""), ("B", "X|Y")]


@pytest.mark.parametrize(
    "raw",
    [
        b"[]",
        b"null",
        b'{"title":"A","title":"B"}',
        b'{"title":[{"nested":"object"}]}',
        b'{"title":"A","sections":{"title":"B"},"sections.title":"C"}',
        b'{"title":NaN}',
        b'{"title":Infinity}',
        b'{"title":"\xff"}',
    ],
)
def test_json_rejects_invalid_or_ambiguous_dataset_shapes(tmp_path: Path, raw: bytes) -> None:
    from patent_analysis.dataset_v2 import read_dataset_v2

    source = tmp_path / "invalid.json"
    source.write_bytes(raw)

    with pytest.raises(DatasetInputError) as caught:
        read_dataset_v2(source.name, allowed_root=tmp_path)

    assert caught.value.code == "input.invalid"


def test_json_rejects_objects_beyond_the_depth_limit(tmp_path: Path) -> None:
    from patent_analysis.dataset_v2 import MAX_JSON_DEPTH, read_dataset_v2

    value: object = "leaf"
    for index in range(MAX_JSON_DEPTH + 1):
        value = {f"level_{index}": value}
    source = tmp_path / "deep.json"
    _write_json(source, {"root": value})

    with pytest.raises(DatasetInputError) as caught:
        read_dataset_v2(source.name, allowed_root=tmp_path)

    assert caught.value.code == "input.invalid"


def test_legacy_ranking_accepts_patent_json_without_changing_source(tmp_path: Path) -> None:
    from patent_analysis.api import run_analysis

    source = tmp_path / "patents.json"
    before = _write_json(
        source,
        [
            {"title": "A", "applicants": ["株式会社クボタ"]},
            {"title": "B", "applicants": ["株式会社クボタ", "B社"]},
        ],
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "applicants",
        "measure": {"mode": "count", "column": None},
        "top_n": 10,
        "include_other": True,
        "multi_value_mode": "all",
    }

    result = run_analysis(
        source.name,
        json.dumps(spec).encode("utf-8"),
        allowed_root=tmp_path,
    )

    assert result["result"]["population"] == {"input_rows": 2, "analyzed_rows": 3}
    assert [(row["label"], row["count"]) for row in result["result"]["rows"]] == [
        ("株式会社クボタ", 2),
        ("B社", 1),
    ]
    assert source.read_bytes() == before


def test_registered_v2_analysis_accepts_json_string_arrays(tmp_path: Path) -> None:
    from patent_analysis.api import run_analysis

    source = tmp_path / "patents.json"
    _write_json(
        source,
        [
            {"applicants": ["A社"], "classifications": ["H01L", "G06F"]},
            {"applicants": ["B社"], "classifications": ["H01L"]},
        ],
    )
    spec = {
        "analysis_contract_version": "2.0.0",
        "analysis_id": "matrix.v1",
        "normalization": {"profiles": []},
        "parameters": {
            "include_axis_other": True,
            "measure": "count",
            "x_limit": 2,
            "x_role": "applicant",
            "y_classification_level": "subclass",
            "y_limit": 2,
            "y_role": "classification",
        },
        "population": {"family_mode": "records", "filters": [], "selection_sets": []},
        "resolution": {
            "bindings": {"applicant": "applicants", "classification": "classifications"}
        },
    }

    result = run_analysis(
        source.name,
        json.dumps(spec).encode("utf-8"),
        allowed_root=tmp_path,
    )

    assert result["analysis_id"] == "matrix.v1"
    assert result["population"] == {"input_rows": 2, "analyzed_rows": 2, "excluded_rows": 0}


def test_cli_analyze_accepts_patent_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from patent_analysis.cli import main

    source = tmp_path / "patents.json"
    _write_json(source, [{"applicants": ["A社"]}, {"applicants": ["A社", "B社"]}])
    spec = tmp_path / "spec.json"
    _write_json(
        spec,
        {
            "analysis_type": "ranking",
            "dimension": "applicants",
            "measure": {"mode": "count", "column": None},
            "top_n": 10,
            "include_other": True,
            "multi_value_mode": "all",
        },
    )
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))

    assert main(["analyze", source.name, "--spec", spec.name, "--json"]) == 0
    document = json.loads(capsys.readouterr().out)
    assert [(row["label"], row["count"]) for row in document["result"]["rows"]] == [
        ("A社", 2),
        ("B社", 1),
    ]


def test_analysis_table_accepts_patent_json(tmp_path: Path) -> None:
    from patent_analysis.api import run_analysis_table

    source = tmp_path / "patents.json"
    _write_json(source, [{"applicants": ["A社"]}, {"applicants": ["B社"]}])
    spec = {
        "analysis_type": "ranking",
        "dimension": "applicants",
        "measure": {"mode": "count", "column": None},
        "top_n": 10,
        "include_other": True,
        "multi_value_mode": "all",
    }

    table = run_analysis_table(
        source.name,
        json.dumps(spec).encode("utf-8"),
        allowed_root=tmp_path,
    )

    assert "A社" in table
    assert "B社" in table


def test_mcp_analyze_accepts_patent_json(tmp_path: Path) -> None:
    from patent_analysis_mcp.roots import ApprovedRoot, RootRegistry
    from patent_analysis_mcp.tool_handlers import ToolHandlers

    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    input_root.mkdir()
    output_root.mkdir()
    _write_json(input_root / "patents.json", {"applicants": ["A社"]})
    roots = RootRegistry(
        input_roots=(ApprovedRoot("input", input_root),),
        output_roots=(ApprovedRoot("output", output_root),),
    )
    spec = {
        "analysis_type": "ranking",
        "dimension": "applicants",
        "measure": {"mode": "count", "column": None},
        "top_n": 10,
        "include_other": True,
        "multi_value_mode": "all",
    }

    result = ToolHandlers(roots=roots).call(
        "patent_analysis.analyze",
        {"input_root_id": "input", "path": "patents.json", "spec": spec},
    )

    assert result["ok"] is True
    assert result["content"]["result"]["rows"][0]["label"] == "A社"


def test_cli_inspect_accepts_patent_json_without_exposing_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from patent_analysis.cli import main

    source = tmp_path / "private.json"
    _write_json(source, {"title": "PRIVATE-TITLE", "applicants": ["PRIVATE-APPLICANT"]})
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))

    assert main(["inspect", source.name, "--json"]) == 0
    output = capsys.readouterr().out
    document = json.loads(output)
    assert document["dataset"]["row_count"] == 1
    assert document["dataset"]["columns"] == ["title", "applicants"]
    assert "PRIVATE-TITLE" not in output
    assert "PRIVATE-APPLICANT" not in output
