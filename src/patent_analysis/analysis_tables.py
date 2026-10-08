"""Deterministic aggregate tables built only from the shared analysis runner."""

from __future__ import annotations

import csv
import json
import unicodedata
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from patent_analysis.analysis_contracts import AnalysisContractError
from patent_analysis.analysis_runner import run_analysis

MAX_TABLE_BYTES = 16 * 1024 * 1024

# Explicit columns preserve order and headers even when the population is empty.
_TABLES = {
    "ranking.v1": {"rows": "row_kind label value count share"},
    "matrix.v1": {"cells": "x_index y_index x_label y_label value row_count"},
    "timeline.v1": {"series": "label is_other year value row_count"},
    "composition.v1": {"items": "label is_other value row_count share share_basis"},
    "growth.v1": {
        "series": "label is_other year value row_count growth_rate growth_state",
    },
    "concentration.v1": {
        "series": "label is_other year value row_count contribution_count classification",
    },
    "lifecycle.v1": {"points": "label x y size stage"},
    "growth-quadrant.v1": {
        "points": "label total_count quadrant long.previous long.recent long.rate_percent "
        "long.state short.previous short.recent short.rate_percent short.state",
    },
    "entry-exit.v1": {"points": "label count first_year last_year active_recent"},
    "citation.v1": {"points": "point_id label year citation_value"},
    "matrix-composition.v1": {"items": "label count share"},
    "new-entrants.v1": {
        "applicants": "label first_year row_count classification_memberships",
        "cells": "applicant classification count share",
    },
    "compara.v1": {"cells": "x y a_count b_count difference"},
    "cooccurrence.v1": {
        "label_counts": "label count", "pairs": "source target count", "cells": "x y count",
    },
    "collaboration-network.v1": {"nodes": "label count", "edges": "source target count"},
    "inventor-tracking.v1": {
        "inventors": "inventor count first_year last_year",
        "observations": "year inventor cluster_id count missing_applicant_rows applicants",
        "co_inventions": "year source target count",
        "affiliations": "year inventor applicant count",
        "clusters": "cluster_id year members",
        "cluster_links": "source target count split merge inventors",
        "affiliation_changes": "inventor from_year to_year gap_years from_cluster to_cluster "
        "status added_applicants removed_applicants",
    },
    "uniqueness.v1": {
        "groups": "group record_count total_item_count unique_item_count uniqueness_rate "
        "items_truncated unique_items",
    },
    "shared-involvement.v1": {
        "groups": "group record_count total_item_count shared_item_count shared_rate "
        "involvement_record_count items_truncated shared_items",
    },
}


class _Buffer:
    def __init__(self) -> None:
        self.parts: list[str] = []
        self.size = 0

    def write(self, value: str) -> int:
        self.size += len(value.encode("utf-8"))
        if self.size > MAX_TABLE_BYTES:
            raise AnalysisContractError("table output exceeds published limits")
        self.parts.append(value)
        return len(value)

    def result(self) -> str:
        return "".join(self.parts)


def _rows(data: dict[str, Any], table: str) -> Iterator[dict[str, Any]]:
    if table != "series":
        yield from data[table]
        return
    for series in data["series"]:
        for index, year in enumerate(data["x"]):
            row = {
                "label": series["label"], "is_other": series["is_other"], "year": year,
                "value": series["values"][index], "row_count": series["row_counts"][index],
            }
            for field in ("growth_rate", "growth_state"):
                if field in series:
                    row[field] = series[field]
            for array, field in (
                ("contribution_counts", "contribution_count"),
                ("classifications", "classification"),
            ):
                if array in series:
                    row[field] = series[array][index]
            yield row


def _value(row: dict[str, Any], column: str) -> Any:
    value: Any = row
    for key in column.split("."):
        value = value[key]
    return value


def _escape_json_text(encoded: str, *, escape_separator: bool = False) -> str:
    """Keep serialized JSON readable and single-line without changing its value."""
    return "".join(
        "\\u007c" if escape_separator and char == "|"
        else json.dumps(char, ensure_ascii=True)[1:-1]
        if unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        else char
        for char in encoded
    )


def _cell(value: Any, *, csv_mode: bool) -> str:
    if value is None:
        return "" if csv_mode else "null"
    if isinstance(value, str):
        value = "".join(
            f"\\u{ord(char):04x}" if unicodedata.category(char) in {"Cc", "Cf"}
            and char not in "\t\n\r" else char for char in value
        )
        if not csv_mode:
            # Never emit terminal control characters or ambiguous table separators.
            return (json.dumps(value, ensure_ascii=False)[1:-1].replace("|", "\\|")
                    .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))
        if value.lstrip().startswith(("=", "+", "-", "@", "＝", "＋", "－", "＠")) or (
            value.startswith(("\t", "\r", "\n"))
        ):
            return "'" + value
        return value
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return _escape_json_text(encoded, escape_separator=not csv_mode)


def run_analysis_table(
    source: str | Path,
    spec_bytes: bytes,
    *,
    allowed_root: str | Path,
    table_format: str = "csv",
    include_context: bool = False,
) -> str:
    """Analyze once and return UTF-8-ready CSV or plain text aggregate tables.

    Optional context retains the complete Spec and result as JSON Pointer/value rows.
    No caller-supplied result, path output or rendering runtime is accepted here.
    """
    if table_format not in ("csv", "text"):
        raise AnalysisContractError("table format must be csv or text")
    if type(include_context) is not bool:
        raise AnalysisContractError("include_context must be boolean")
    document = run_analysis(source, spec_bytes, allowed_root=allowed_root)
    analysis_id = document.get("analysis_id", "ranking.v1")
    data = document["result" if analysis_id == "ranking.v1" else "data"]
    tables = {name: columns.split() for name, columns in _TABLES[analysis_id].items()}
    output = _Buffer()
    if table_format == "csv":
        columns = list(dict.fromkeys(column for fields in tables.values() for column in fields))
        writer = csv.writer(output, lineterminator="\n")
        context_columns = ["context_path", "context_value"] if include_context else []
        writer.writerow(["analysis_id", "table", *columns, *context_columns])
        for table, fields in tables.items():
            for row in _rows(data, table):
                writer.writerow([
                    analysis_id, table,
                    *(_cell(_value(row, column), csv_mode=True) if column in fields else ""
                      for column in columns),
                    *(["", ""] if include_context else []),
                ])
    else:
        output.write(analysis_id + "\n")
        for table, fields in tables.items():
            output.write(f"\n[{table}]\n" + " | ".join(fields) + "\n")
            found = False
            for row in _rows(data, table):
                found = True
                output.write(" | ".join(
                    _cell(_value(row, column), csv_mode=False) for column in fields
                ) + "\n")
            if not found:
                output.write("(no rows)\n")
    if include_context:
        context = {"spec": json.loads(spec_bytes), "analysis": document}
        if table_format == "text":
            output.write("\n[context]\nJSON Pointer | JSON value\n")
        for path, value in _context_rows(context):
            # JSON strings start with a literal quote; negative JSON numbers are data,
            # not caller-provided formula strings. ASCII escapes preserve all controls.
            encoded = json.dumps(value, ensure_ascii=table_format == "csv", allow_nan=False,
                                 separators=(",", ":"))
            if table_format == "csv":
                writer.writerow([analysis_id, "context", *([""] * len(columns)),
                                 json.dumps(path, ensure_ascii=True), encoded])
            else:
                # Retain readable Unicode while keeping each value valid, single-line JSON.
                encoded = _escape_json_text(encoded, escape_separator=True)
                output.write(_cell(path, csv_mode=False) + " | " + encoded + "\n")
    return output.result()


def _context_rows(value: Any, path: str = "") -> Iterator[tuple[str, Any]]:
    """Emit containers before children, including empty containers and typed scalars."""
    if isinstance(value, dict):
        yield path, {}
        for key, item in value.items():
            pointer = key.replace("~", "~0").replace("/", "~1")
            yield from _context_rows(item, path + "/" + pointer)
    elif isinstance(value, list):
        yield path, []
        for index, item in enumerate(value):
            yield from _context_rows(item, f"{path}/{index}")
    else:
        yield path, value
