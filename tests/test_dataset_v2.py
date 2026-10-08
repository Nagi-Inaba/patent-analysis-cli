from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from patent_analysis.errors import DatasetInputError

GOOGLE_SIGNATURE = (
    "id,title,assignee,inventor/author,priority date,filing/creation date,"
    "publication date,grant date,result link,representative figure link"
)


def _read(source: Path):
    from patent_analysis.dataset_v2 import read_dataset_v2

    return read_dataset_v2(source, allowed_root=source.parent)


def test_reader_retains_raw_text_and_assigns_ordinals_only_to_data_records(
    tmp_path: Path,
) -> None:
    source = tmp_path / "raw.csv"
    source.write_text(
        " Applicants ,Title\n  A Corp  ,Exact Title\n\n  ,  \nB Corp,Second\n",
        encoding="utf-8",
    )

    dataset = _read(source)

    assert dataset.manifest.raw_header == (" Applicants ", "Title")
    assert dataset.manifest.input_rows == 2
    assert [(row.source_ordinal, row.values) for row in dataset.rows] == [
        (1, ("  A Corp  ", "Exact Title")),
        (2, ("B Corp", "Second")),
    ]

    with pytest.raises(FrozenInstanceError):
        dataset.rows[0].source_ordinal = 9  # type: ignore[misc]


def test_manifest_projection_is_bounded_and_contains_no_rows_or_path(tmp_path: Path) -> None:
    from patent_analysis.dataset_v2 import manifest_to_public_dict

    source = tmp_path / "PRIVATE-DATASET.csv"
    raw = b"Applicants\nPRIVATE-CELL\n"
    source.write_bytes(raw)

    manifest = manifest_to_public_dict(_read(source).manifest)

    assert manifest == {
        "columns": ["Applicants"],
        "row_count": 1,
        "column_count": 1,
        "byte_size": len(raw),
        "encoding": "utf-8",
        "preamble": None,
    }
    assert _read(source).manifest.source_input_sha256 == hashlib.sha256(raw).hexdigest()
    rendered = repr(manifest)
    assert "PRIVATE-CELL" not in rendered
    assert source.name not in rendered


def test_valid_quoted_comma_google_preamble_is_skipped_strictly(tmp_path: Path) -> None:
    source = tmp_path / "google.csv"
    source.write_text(
        '"search URL:","https://patents.google.com/xhr/query?url=synthetic,quoted"\n'
        f"{GOOGLE_SIGNATURE}\n"
        "P-1,T,A,I,2020,2021,2022,2023,R,F\n",
        encoding="utf-8",
    )

    dataset = _read(source)

    assert dataset.manifest.preamble == "google_patents"
    assert dataset.manifest.raw_header[0] == "id"
    assert dataset.rows[0].source_ordinal == 1
    assert dataset.rows[0].values[0] == "P-1"


@pytest.mark.parametrize(
    ("url", "signature"),
    [
        ("https://example.test/query", GOOGLE_SIGNATURE),
        ("https://example.test/?next=patents.google.com", GOOGLE_SIGNATURE),
        ("https://patents.google.com./query", GOOGLE_SIGNATURE),
        ("//patents.google.com/query", GOOGLE_SIGNATURE),
        ("https://patents.google.com/query", "id,title,assignee,extra"),
    ],
    ids=(
        "wrong-host",
        "query-host",
        "trailing-dot",
        "scheme-relative",
        "wrong-signature",
    ),
)
def test_known_google_marker_rejects_wrong_host_or_signature_without_fallback(
    tmp_path: Path,
    url: str,
    signature: str,
) -> None:
    source = tmp_path / "invalid-google.csv"
    source.write_text(
        f'"search URL:","{url}"\n{signature}\nP-1,T,A,I,2020,2021,2022,2023,R,F\n',
        encoding="utf-8",
    )

    with pytest.raises(DatasetInputError) as caught:
        _read(source)

    assert caught.value.code == "input.invalid"
    assert str(caught.value) == "dataset header is invalid"
    assert url not in repr(caught.value.as_dict())


def test_first_excess_compact_row_is_rejected_before_parsing_later_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import patent_analysis.dataset_v2 as dataset_v2

    monkeypatch.setattr(dataset_v2, "MAX_CSV_ROWS", 2)
    source = tmp_path / "compact-row-limit.csv"
    source.write_text('a\n1\n2\n3\n"malformed-tail\n', encoding="utf-8")

    with pytest.raises(DatasetInputError) as caught:
        _read(source)

    assert str(caught.value) == "dataset exceeds row limit"


def test_blank_records_do_not_bypass_the_parsed_cell_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import patent_analysis.dataset_v2 as dataset_v2

    monkeypatch.setattr(dataset_v2, "MAX_CSV_CELLS", 3)
    source = tmp_path / "blank-cell-limit.csv"
    source.write_text("a\n \n \n \nvalue\n", encoding="utf-8")

    with pytest.raises(DatasetInputError) as caught:
        _read(source)

    assert str(caught.value) == "csv input exceeds published limits"


@pytest.mark.parametrize(
    ("content", "limit_name", "limit_value"),
    [
        ("a,a\n1,2\n", None, None),
        ("a, \n1,2\n", None, None),
        ("a,b\n1,2,3\n", None, None),
        ("a,b,c\n1,2,3\n", "MAX_CSV_COLUMNS", 2),
        ("a\n1\n2\n", "MAX_CSV_ROWS", 1),
        ("a,b\n1,2\n", "MAX_CSV_CELLS", 3),
        ("header\nvalue\n", "MAX_CSV_CELL_CHARACTERS", 5),
    ],
    ids=(
        "duplicate-header",
        "blank-header",
        "row-width",
        "column-limit",
        "row-limit",
        "cell-count-limit",
        "character-limit",
    ),
)
def test_reader_rejects_invalid_header_width_and_limits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    content: str,
    limit_name: str | None,
    limit_value: int | None,
) -> None:
    import patent_analysis.dataset_v2 as dataset_v2

    if limit_name is not None:
        monkeypatch.setattr(dataset_v2, limit_name, limit_value)
    source = tmp_path / "invalid.csv"
    source.write_text(content, encoding="utf-8")

    with pytest.raises(DatasetInputError) as caught:
        _read(source)

    assert caught.value.code == "input.invalid"


def test_reader_accepts_the_same_utf16_bom_encoding_as_v1(tmp_path: Path) -> None:
    source = tmp_path / "utf16.csv"
    source.write_bytes("A,B\n1,2\n".encode("utf-16"))

    dataset = _read(source)

    assert dataset.manifest.encoding == "utf-16"
    assert dataset.manifest.raw_header == ("A", "B")
    assert dataset.rows[0].values == ("1", "2")


def test_reader_rejects_shift_jis_without_fallback(tmp_path: Path) -> None:
    source = tmp_path / "shift-jis.csv"
    source.write_bytes("出願人\nA社\n".encode("shift_jis"))

    with pytest.raises(DatasetInputError) as caught:
        _read(source)

    assert caught.value.code == "input.invalid"
    assert str(caught.value) == "dataset encoding is invalid"
