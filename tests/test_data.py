import csv
import hashlib
import json
import os
import traceback
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path

import pytest

from patent_analysis import DatasetInputError, access, data
from patent_analysis import inspect_csv as _inspect_csv


def inspect_csv(source: Path) -> dict[str, object]:
    return _inspect_csv(source, allowed_root=source.parent)


def test_inspect_csv_returns_bounded_metadata_without_values_or_path(tmp_path: Path) -> None:
    source = tmp_path / "private-name.csv"
    source.write_text(
        "出願人,被引用件数\nA社,10\nB社,20\n", encoding="utf-8-sig"
    )

    manifest = inspect_csv(source)

    assert manifest["columns"] == ["出願人", "被引用件数"]
    assert manifest["row_count"] == 2
    assert manifest["column_count"] == 2
    assert manifest["encoding"] == "utf-8-sig"
    assert manifest["byte_size"] == source.stat().st_size
    assert len(manifest["content_sha256"]) == 64
    assert manifest["content_sha256"] == hashlib.sha256(
        source.read_bytes()
    ).hexdigest()
    payload = json.dumps(manifest, ensure_ascii=False)
    assert "private-name.csv" not in payload
    assert "A社" not in payload
    assert "10" not in payload


def test_inspect_csv_supports_utf16_with_bom(tmp_path: Path) -> None:
    source = tmp_path / "utf16.csv"
    source.write_bytes("A,B\n1,2\n3,4\n".encode("utf-16"))

    manifest = inspect_csv(source)

    assert manifest["columns"] == ["A", "B"]
    assert manifest["row_count"] == 2
    assert manifest["column_count"] == 2
    assert manifest["encoding"] == "utf-16"
    assert manifest["content_sha256"] == hashlib.sha256(
        source.read_bytes()
    ).hexdigest()


def test_duplicate_headers_are_rejected(tmp_path: Path) -> None:
    source = tmp_path / "duplicate.csv"
    source.write_text("出願人,出願人\nA社,B社\n", encoding="utf-8")

    with pytest.raises(DatasetInputError) as caught:
        inspect_csv(source)

    assert caught.value.code == "input.invalid"
    assert caught.value.as_dict()["details"] == {}
    assert str(source) not in str(caught.value.as_dict())


def test_empty_headers_are_rejected(tmp_path: Path) -> None:
    source = tmp_path / "blank-header.csv"
    source.write_text("出願人,\nA社,10\n", encoding="utf-8")

    with pytest.raises(DatasetInputError) as caught:
        inspect_csv(source)

    assert caught.value.code == "input.invalid"
    assert caught.value.as_dict()["details"] == {}


def test_row_width_mismatch_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "width-mismatch.csv"
    source.write_text("a,b\n1,2,3\n", encoding="utf-8")

    with pytest.raises(DatasetInputError) as caught:
        inspect_csv(source)

    assert caught.value.code == "input.invalid"
    assert caught.value.as_dict()["details"] == {}


def test_invalid_file_path_is_rejected(tmp_path: Path) -> None:
    missing = tmp_path / "missing.csv"

    with pytest.raises(DatasetInputError) as caught:
        inspect_csv(missing)

    assert caught.value.code == "input.invalid"
    assert caught.value.as_dict()["details"] == {}
    assert missing.name not in str(caught.value.as_dict())


def test_invalid_encoding_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "invalid-encoding.csv"
    source.write_bytes(b"\xff\xfe\x00")

    with pytest.raises(DatasetInputError) as caught:
        inspect_csv(source)

    assert caught.value.code == "input.invalid"
    assert caught.value.as_dict()["details"] == {}


def test_excessive_rows_are_rejected(tmp_path: Path) -> None:
    source = tmp_path / "too-many-rows.csv"
    rows = ["1,2"] * 100_001
    source.write_text("a,b\n" + "\n".join(rows) + "\n", encoding="utf-8")

    with pytest.raises(DatasetInputError) as caught:
        inspect_csv(source)

    assert caught.value.code == "input.invalid"
    assert caught.value.as_dict()["details"] == {}


def test_excessive_columns_are_rejected(tmp_path: Path) -> None:
    source = tmp_path / "too-many-columns.csv"
    header = ",".join(f"c{index}" for index in range(1001))
    row = ",".join("x" for _ in range(1001))
    source.write_text(f"{header}\n{row}\n", encoding="utf-8")

    with pytest.raises(DatasetInputError) as caught:
        inspect_csv(source)

    assert caught.value.code == "input.invalid"
    assert caught.value.as_dict()["details"] == {}


def test_csv_row_cells_are_read_into_dicts(tmp_path: Path) -> None:
    source = tmp_path / "rows.csv"
    header = "a,b\n"
    rows = "x,y\nz,w\n"
    source.write_text(header + rows, encoding="utf-8")

    rows_data, manifest = data.read_csv_rows(source, allowed_root=tmp_path)

    assert manifest["row_count"] == 2
    assert rows_data == [{"a": "x", "b": "y"}, {"a": "z", "b": "w"}]
    assert manifest["columns"] == ["a", "b"]


def test_row_width_mismatch_discloses_no_cell_values(tmp_path: Path) -> None:
    source = tmp_path / "values-not-leaked.csv"
    source.write_text("a,b\n1,2,3\n", encoding="utf-8")

    with pytest.raises(DatasetInputError) as caught:
        inspect_csv(source)

    assert "1,2,3" not in str(caught.value.as_dict())
    assert "a,b" not in str(caught.value.as_dict())


def test_embedded_newline_in_quoted_field_is_preserved(tmp_path: Path) -> None:
    source = tmp_path / "quoted-newline.csv"
    source.write_text('name,comment\nAlice,"line1\nline2"\n', encoding="utf-8")

    rows, manifest = data.read_csv_rows(source, allowed_root=tmp_path)

    assert manifest["row_count"] == 1
    assert rows[0]["comment"].replace("\r\n", "\n") == "line1\nline2"


def test_large_field_within_published_limit_and_above_default_is_accepted(tmp_path: Path) -> None:
    default_limit = csv.field_size_limit()
    if default_limit >= data.MAX_CSV_CELL_CHARACTERS:
        pytest.skip(
            "Parser default limit is not lower than published limit in this runtime"
        )

    source = tmp_path / "large-field.csv"
    payload = "x" * (default_limit + 1)
    source.write_text(f"a\n{payload}\n", encoding="utf-8")

    manifest = inspect_csv(source)

    assert manifest["row_count"] == 1
    assert manifest["column_count"] == 1


def test_malformed_csv_becomes_dataset_input_error_without_payload_leak(tmp_path: Path) -> None:
    source = tmp_path / "malformed.csv"
    source.write_text('name,value\n"abc,100\n', encoding="utf-8")

    with pytest.raises(DatasetInputError) as caught:
        inspect_csv(source)

    assert caught.value.code == "input.invalid"
    payload = json.dumps(caught.value.as_dict(), ensure_ascii=False)
    assert "abc" not in payload
    assert source.name not in payload


def test_malformed_same_width_quotes_are_rejected(tmp_path: Path) -> None:
    source = tmp_path / "same-width-malformed.csv"
    source.write_text('name,value\n"abc"x,100\n', encoding="utf-8")

    with pytest.raises(DatasetInputError) as caught:
        inspect_csv(source)

    assert caught.value.code == "input.invalid"


def test_oversized_file_is_rejected_by_bounded_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "small.csv"
    source.write_text("a,b\n1,2\n", encoding="utf-8")

    original_lstat = access._lstat

    def oversized_lstat(path: Path):
        result = original_lstat(path)
        if path != source:
            return result
        fields = list(result)
        fields[6] = data.MAX_CSV_BYTES + 1
        return os.stat_result(fields)

    monkeypatch.setattr(access, "_lstat", oversized_lstat)

    with pytest.raises(DatasetInputError) as caught:
        inspect_csv(source)

    assert caught.value.code == "input.invalid"


def test_header_limit_exact_and_one_over_for_columns(tmp_path: Path) -> None:
    allowed = "c" * data.MAX_CSV_CELL_CHARACTERS
    source = tmp_path / "header-limit.csv"
    source.write_text(f"{allowed}\nvalue\n", encoding="utf-8")
    manifest = inspect_csv(source)
    assert manifest["columns"] == [allowed]

    source = tmp_path / "header-limit-over.csv"
    source.write_text(f"{allowed}x\nvalue\n", encoding="utf-8")
    with pytest.raises(DatasetInputError) as caught:
        inspect_csv(source)
    assert caught.value.code == "input.invalid"


def test_cell_limit_exact_and_one_over(tmp_path: Path) -> None:
    source = tmp_path / "cell-limit.csv"
    payload = "x" * data.MAX_CSV_CELL_CHARACTERS
    source.write_text(f"a\n{payload}\n", encoding="utf-8")
    manifest = inspect_csv(source)
    assert manifest["row_count"] == 1

    source = tmp_path / "cell-limit-over.csv"
    source.write_text(
        f"a\n{'x' * (data.MAX_CSV_CELL_CHARACTERS + 1)}\n",
        encoding="utf-8",
    )
    with pytest.raises(DatasetInputError) as caught:
        inspect_csv(source)
    assert caught.value.code == "input.invalid"


def test_aggregate_cell_limit_boundary_is_enforced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "cells.csv"
    monkeypatch.setattr(data, "MAX_CSV_CELLS", 4)
    source.write_text("a,b\n1,2\n", encoding="utf-8")
    inspect_csv(source)

    source = tmp_path / "cells-over.csv"
    source.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
    with pytest.raises(DatasetInputError):
        inspect_csv(source)


def test_manifest_only_exposes_allowed_keys(tmp_path: Path) -> None:
    source = tmp_path / "private-name.csv"
    source.write_text("a,b\n1,2\n", encoding="utf-8")
    manifest = inspect_csv(source)

    assert set(manifest.keys()) == {
        "columns",
        "row_count",
        "column_count",
        "byte_size",
        "encoding",
        "content_sha256",
    }


def test_concurrent_inspects_with_large_fields_stay_under_default_parser_limit(
    tmp_path: Path,
) -> None:
    default_limit = csv.field_size_limit()
    if default_limit >= data.MAX_CSV_CELL_CHARACTERS:
        pytest.skip(
            "Parser default limit is not lower than published limit in this runtime"
        )

    payload = "x" * (default_limit + 1)
    sources = []
    for index in range(4):
        source = tmp_path / f"large-{index}.csv"
        source.write_text(f"a\n{payload}\n", encoding="utf-8")
        sources.append(source)

    with ThreadPoolExecutor(max_workers=4) as executor:
        manifests = list(
            executor.map(partial(data.inspect_csv, allowed_root=tmp_path), sources)
        )

    assert len(manifests) == 4
    assert all(manifest["row_count"] == 1 for manifest in manifests)
    assert csv.field_size_limit() == default_limit


@pytest.mark.parametrize("failure_kind", ["missing", "encoding", "csv", "limit"])
def test_dataset_input_error_removes_private_exception_graph_and_traceback_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_kind: str,
) -> None:
    secret = "TASK-5A-PRIVATE-VALUE"
    source = tmp_path / f"{secret}.csv"
    if failure_kind == "encoding":
        source.write_bytes(b"\xff\xfe\x00")
    elif failure_kind == "csv":
        source.write_text(f'name,value\n"{secret},100\n', encoding="utf-8")
    elif failure_kind == "limit":
        source.write_text("a\nvalue\n", encoding="utf-8")
        monkeypatch.setattr(data, "MAX_CSV_BYTES", 1)

    with pytest.raises(DatasetInputError) as caught:
        _inspect_csv(source, allowed_root=tmp_path)

    error = caught.value
    rendered = "".join(traceback.format_exception(error))
    public_surfaces = (
        repr(error),
        str(error),
        repr(error.as_dict()),
        rendered,
        repr(error.__cause__),
        repr(error.__context__),
        repr(getattr(error, "__notes__", None)),
    )
    assert error.__cause__ is None
    assert error.__context__ is None
    assert all(secret not in surface for surface in public_surfaces)
