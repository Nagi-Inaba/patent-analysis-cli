"""Strict immutable CSV/JSON reader for v2 analysis inputs."""

from __future__ import annotations

import csv
import hashlib
import unicodedata
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from patent_analysis.access import read_verified_bytes
from patent_analysis.canonical_v2 import (
    CanonicalizationError,
    canonical_json_bytes,
    parse_strict_json_bytes,
)
from patent_analysis.column_resolution import (
    get_preamble_policies,
    normalize_header,
    trim_ecmascript_whitespace,
)
from patent_analysis.data import (
    MAX_CSV_BYTES,
    MAX_CSV_CELL_CHARACTERS,
    MAX_CSV_CELLS,
    MAX_CSV_COLUMNS,
    MAX_CSV_ROWS,
    _decoded_csv_stream,
    _temporary_field_size_limit,
)
from patent_analysis.errors import DatasetInputError

DATASET_CONTRACT_VERSION = "2.0.0"
MAX_JSON_BYTES = 32 * 1024 * 1024
MAX_JSON_DEPTH = 64


@dataclass(frozen=True, slots=True)
class DatasetRow:
    source_ordinal: int
    values: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DatasetManifestV2:
    dataset_contract_version: str
    raw_header: tuple[str, ...]
    input_rows: int
    input_columns: int
    byte_size: int
    encoding: str
    source_input_sha256: str
    preamble: str | None


@dataclass(frozen=True, slots=True)
class DatasetV2:
    manifest: DatasetManifestV2
    rows: tuple[DatasetRow, ...]


def _detect_encoding(raw: bytes) -> str:
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if raw.startswith(b"\xfe\xff") or raw.startswith(b"\xff\xfe"):
        return "utf-16"
    return "utf-8"


def _blank_record(record: list[str]) -> bool:
    return not record or all(trim_ecmascript_whitespace(value) == "" for value in record)


def _normalized_preamble_text(value: str) -> str:
    return trim_ecmascript_whitespace(unicodedata.normalize("NFKC", value)).lower()


def _preamble_policy(record: list[str]):
    marker = _normalized_preamble_text(record[0] if record else "")
    for policy in get_preamble_policies():
        if marker == _normalized_preamble_text(policy.marker):
            return policy
    return None


def _has_exact_host(record: list[str], expected_host: str) -> bool:
    raw_url = trim_ecmascript_whitespace(",".join(record[1:]))
    try:
        parsed = urlsplit(raw_url)
    except ValueError:
        return False
    return (
        parsed.scheme != ""
        and parsed.hostname is not None
        and parsed.hostname.lower() == _normalized_preamble_text(expected_host)
    )


def _iter_records(text: Iterator[str]) -> Iterator[list[str]]:
    total_cells = 0
    decode_failed = False
    try:
        reader = csv.reader(text, strict=True)
        for record in reader:
            total_cells += len(record)
            if total_cells > MAX_CSV_CELLS:
                raise DatasetInputError("csv input exceeds published limits")
            if any(len(value) > MAX_CSV_CELL_CHARACTERS for value in record):
                raise DatasetInputError("csv input exceeds published limits")
            if not _blank_record(record):
                yield record
    except csv.Error:
        raise DatasetInputError("dataset CSV format is invalid") from None
    except UnicodeDecodeError:
        decode_failed = True
    if decode_failed:
        raise DatasetInputError("dataset encoding is invalid") from None


def _validate_header(header: list[str]) -> None:
    if (
        not header
        or len(header) > MAX_CSV_COLUMNS
        or any(trim_ecmascript_whitespace(name) == "" for name in header)
        or len(set(header)) != len(header)
        or any(len(name) > MAX_CSV_CELL_CHARACTERS for name in header)
    ):
        raise DatasetInputError("dataset header is invalid")


def _json_scalar(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if type(value) in (bool, int, float):
        try:
            return canonical_json_bytes(value).decode("utf-8")
        except (CanonicalizationError, UnicodeError):
            raise DatasetInputError("input is invalid") from None
    raise DatasetInputError("input is invalid")


def _flatten_json_record(record: Mapping[str, object]) -> dict[str, str]:
    flattened: dict[str, str] = {}

    def add(name: str, value: object, depth: int) -> None:
        if depth > MAX_JSON_DEPTH or not name:
            raise DatasetInputError("input is invalid")
        if isinstance(value, Mapping):
            if not value:
                candidate = "{}"
                if name in flattened:
                    raise DatasetInputError("input is invalid")
                flattened[name] = candidate
                return
            for key, child in value.items():
                if not isinstance(key, str) or not key:
                    raise DatasetInputError("input is invalid")
                add(f"{name}.{key}" if name else key, child, depth + 1)
            return
        if isinstance(value, list):
            parts: list[str] = []
            cell_characters = 0
            for item in value:
                part = _json_scalar(item)
                cell_characters += len(part) + bool(parts)
                if cell_characters > MAX_CSV_CELL_CHARACTERS:
                    raise DatasetInputError("dataset input exceeds published limits")
                parts.append(part)
            candidate = "|".join(parts)
        else:
            candidate = _json_scalar(value)
        if name in flattened:
            raise DatasetInputError("input is invalid")
        if len(candidate) > MAX_CSV_CELL_CHARACTERS:
            raise DatasetInputError("dataset input exceeds published limits")
        flattened[name] = candidate

    for key, value in record.items():
        if not isinstance(key, str) or not key:
            raise DatasetInputError("input is invalid")
        add(key, value, 1)
    return flattened


def _read_json_records(raw: bytes) -> tuple[list[str], list[DatasetRow]]:
    try:
        document = parse_strict_json_bytes(raw, allow_bom=True)
    except CanonicalizationError:
        raise DatasetInputError("input is invalid") from None
    raw_records = document if isinstance(document, list) else [document]
    if not raw_records or len(raw_records) > MAX_CSV_ROWS:
        raise DatasetInputError("dataset header is invalid")
    if not all(isinstance(record, Mapping) for record in raw_records):
        raise DatasetInputError("input is invalid")

    flattened_records: list[dict[str, str]] = []
    header: list[str] = []
    seen: set[str] = set()
    for raw_record in raw_records:
        flattened = _flatten_json_record(raw_record)
        if not flattened:
            raise DatasetInputError("dataset header is invalid")
        flattened_records.append(flattened)
        for name in flattened:
            if name not in seen:
                seen.add(name)
                header.append(name)
                if len(header) > MAX_CSV_COLUMNS:
                    raise DatasetInputError("dataset header is invalid")
        if len(header) * (len(flattened_records) + 1) > MAX_CSV_CELLS:
            raise DatasetInputError("dataset input exceeds published limits")
    _validate_header(header)
    rows = [
        DatasetRow(index, tuple(record.get(name, "") for name in header))
        for index, record in enumerate(flattened_records, 1)
    ]
    return header, rows


def read_dataset_v2(
    source: str | Path,
    *,
    allowed_root: str | Path,
) -> DatasetV2:
    is_json = Path(source).suffix.casefold() == ".json"
    raw = read_verified_bytes(
        source,
        allowed_root=allowed_root,
        max_bytes=MAX_JSON_BYTES if is_json else MAX_CSV_BYTES,
    )
    if is_json:
        encoding = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"
        header, data_rows = _read_json_records(raw)
        preamble = None
    else:
        encoding = _detect_encoding(raw)
        with _temporary_field_size_limit(), _decoded_csv_stream(raw, encoding) as text:
            records = _iter_records(text)
            try:
                first_record = next(records)
            except StopIteration:
                raise DatasetInputError("dataset header is invalid") from None

            preamble = None
            policy = _preamble_policy(first_record)
            if policy is None:
                header = first_record
            else:
                if not _has_exact_host(first_record, policy.host):
                    raise DatasetInputError("dataset header is invalid")
                try:
                    header = next(records)
                except StopIteration:
                    raise DatasetInputError("dataset header is invalid") from None
                expected = tuple(normalize_header(value) for value in policy.header_signature)
                candidate = tuple(normalize_header(value) for value in header)
                if candidate != expected:
                    raise DatasetInputError("dataset header is invalid")
                preamble = policy.source_id

            _validate_header(header)
            data_rows = []
            for record in records:
                if len(data_rows) >= MAX_CSV_ROWS:
                    raise DatasetInputError("dataset exceeds row limit")
                if len(record) != len(header):
                    raise DatasetInputError("dataset header is invalid")
                data_rows.append(
                    DatasetRow(source_ordinal=len(data_rows) + 1, values=tuple(record))
                )

    manifest = DatasetManifestV2(
        dataset_contract_version=DATASET_CONTRACT_VERSION,
        raw_header=tuple(header),
        input_rows=len(data_rows),
        input_columns=len(header),
        byte_size=len(raw),
        encoding=encoding,
        source_input_sha256=hashlib.sha256(raw).hexdigest(),
        preamble=preamble,
    )
    return DatasetV2(manifest=manifest, rows=tuple(data_rows))


def manifest_to_public_dict(manifest: DatasetManifestV2) -> dict[str, object]:
    return {
        "columns": list(manifest.raw_header),
        "row_count": manifest.input_rows,
        "column_count": manifest.input_columns,
        "byte_size": manifest.byte_size,
        "encoding": manifest.encoding,
        "preamble": manifest.preamble,
    }
