from __future__ import annotations

import csv
import hashlib
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from io import BytesIO, TextIOWrapper
from pathlib import Path

from patent_analysis.access import read_verified_bytes
from patent_analysis.errors import DatasetInputError

MAX_CSV_BYTES = 300 * 1024 * 1024
MAX_CSV_COLUMNS = 1_000
MAX_CSV_ROWS = 100_000
MAX_CSV_CELLS = 2_000_000
MAX_CSV_CELL_CHARACTERS = 1_000_000
_CSV_PARSE_LOCK = threading.RLock()


def _detect_encoding(raw: bytes) -> str:
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if raw.startswith(b"\xfe\xff") or raw.startswith(b"\xff\xfe"):
        return "utf-16"
    return "utf-8"


def _enforce_limit(condition: bool, *, details: dict[str, object]) -> None:
    if not condition:
        raise DatasetInputError("csv input exceeds published limits", details=details)


def inspect_csv(source: str | Path, *, allowed_root: str | Path) -> dict[str, object]:
    _, manifest = read_csv_rows(source, allowed_root=allowed_root)
    return manifest


@contextmanager
def _temporary_field_size_limit() -> Iterator[None]:
    with _CSV_PARSE_LOCK:
        previous = csv.field_size_limit()
        csv.field_size_limit(MAX_CSV_CELL_CHARACTERS)
        try:
            yield
        finally:
            csv.field_size_limit(previous)


@contextmanager
def _decoded_csv_stream(raw: bytes, encoding: str) -> Iterator[TextIOWrapper]:
    """Decode the verified byte snapshot incrementally, preserving quoted newlines."""
    with TextIOWrapper(BytesIO(raw), encoding=encoding, newline="") as stream:
        yield stream


def read_csv_rows(
    source: str | Path,
    *,
    allowed_root: str | Path,
) -> tuple[list[dict[str, str]], dict[str, object]]:
    raw = read_verified_bytes(
        source,
        allowed_root=allowed_root,
        max_bytes=MAX_CSV_BYTES,
    )

    encoding = _detect_encoding(raw)
    with _temporary_field_size_limit(), _decoded_csv_stream(raw, encoding) as text:
        rows = _iter_rows(text)

        header_error: str | None = None
        try:
            header = next(rows)
        except StopIteration:
            header_error = "dataset header is invalid"
            header = []
        except csv.Error:
            header_error = "dataset CSV format is invalid"
            header = []
        if header_error is not None:
            raise DatasetInputError(header_error) from None

        _enforce_limit(len(header) > 0, details={})
        _enforce_limit(len(header) <= MAX_CSV_COLUMNS, details={})
        _enforce_limit(all(name.strip() != "" for name in header), details={})
        _enforce_limit(len(set(header)) == len(header), details={})
        _enforce_limit(
            all(len(name) <= MAX_CSV_CELL_CHARACTERS for name in header),
            details={},
        )

        columns = list(header)
        data: list[dict[str, str]] = []
        total_cells = len(columns)
        row_count = 0

        csv_failed = False
        try:
            for row in rows:
                row_count += 1
                if row_count > MAX_CSV_ROWS:
                    raise DatasetInputError("dataset exceeds row limit", details={})
                _enforce_limit(len(row) == len(columns), details={})
                total_cells += len(row)
                _enforce_limit(total_cells <= MAX_CSV_CELLS, details={})
                for cell in row:
                    _enforce_limit(len(cell) <= MAX_CSV_CELL_CHARACTERS, details={})
                data.append(dict(zip(columns, row, strict=False)))
        except csv.Error:
            csv_failed = True
        if csv_failed:
            raise DatasetInputError("dataset CSV format is invalid") from None

    manifest: dict[str, object] = {
        "columns": columns,
        "row_count": row_count,
        "column_count": len(columns),
        "byte_size": len(raw),
        "encoding": encoding,
        "content_sha256": hashlib.sha256(raw).hexdigest(),
    }
    return data, manifest


def _iter_rows(text: Iterator[str]) -> Iterator[list[str]]:
    reader = csv.reader(text, strict=True)
    failed = False
    try:
        for row in reader:
            if row:
                yield row
    except UnicodeDecodeError:
        failed = True
    if failed:
        raise DatasetInputError("dataset encoding is invalid") from None
