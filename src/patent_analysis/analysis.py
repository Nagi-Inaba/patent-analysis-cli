from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any, NoReturn

from patent_analysis._version import PACKAGE_VERSION
from patent_analysis.access import validate_allowed_root
from patent_analysis.analysis_contracts import (
    ANALYSIS_CONTRACT_VERSION,
    AnalysisContractError,
    validate_analysis_result,
    validate_analysis_spec,
)
from patent_analysis.data import read_csv_rows
from patent_analysis.dataset_v2 import read_dataset_v2
from patent_analysis.errors import DatasetInputError

ALGORITHM_ID = "ranking.v1"
BLANK_LABEL = "(空白)"
MAX_DIMENSION_TOKENS_PER_CELL = 1_000
MAX_EXPANDED_CONTRIBUTIONS = 500_000
MAX_DISTINCT_BUCKETS = 100_000
DEFAULT_DELIMITERS = ("|", ";", "；", "、", "，", "\r", "\n")
CLASSIFICATION_CODE_PATTERN = re.compile(
    r"(?:^|[^A-Za-z0-9])(?:ic|ipc|cpc|fi|ftm)(?:$|[^A-Za-z0-9])",
    re.IGNORECASE,
)
CLASSIFICATION_F_TERM_PATTERN = re.compile(r"f[\s_-]*term", re.IGNORECASE)
CLASSIFICATION_JAPANESE_PATTERN = re.compile(r"[ＦF]ターム|サブクラス|メイングループ")
NUMERIC_PLAIN_PATTERN = re.compile(r"^-?[0-9]+(\.[0-9]+)?$")
NUMERIC_CITATION_PREFIX_PATTERN = re.compile(
    r"^(?:被引用(?:件数|数|回数)?|引用(?:件数|数|回数)?|cited\s*by|citation\s*count|citations?|forward\s*citations?)\s*[:：]\s*(-?[0-9]+(?:\.[0-9]+)?)$",
    re.IGNORECASE,
)


def _column_looks_like_classification(column_name: str) -> bool:
    normalized = column_name.strip()
    if not normalized:
        return False
    return bool(
        CLASSIFICATION_CODE_PATTERN.search(normalized)
        or CLASSIFICATION_F_TERM_PATTERN.search(normalized)
        or CLASSIFICATION_JAPANESE_PATTERN.search(normalized)
    )


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_sha256(value: Any) -> str:
    return _sha256(_canonical_json(value))


def _dimension_delimiter_pattern(dimension: str) -> re.Pattern[str]:
    delimiters = "".join(DEFAULT_DELIMITERS)
    if _column_looks_like_classification(dimension):
        delimiters += ","
    return re.compile(f"[{re.escape(delimiters)}]+")


def _iter_non_empty_dimension_tokens(
    column_value: str,
    delimiter_pattern: re.Pattern[str],
) -> Iterator[str]:
    start = 0
    for match in delimiter_pattern.finditer(column_value):
        token = column_value[start : match.start()].strip()
        if token:
            yield token
        start = match.end()

    token = column_value[start:].strip()
    if token:
        yield token


def _raise_ranking_budget_error() -> NoReturn:
    raise DatasetInputError("ranking expansion exceeds published limits") from None


def _iter_dimension_values(
    raw_value: Any,
    mode: str,
    delimiter_pattern: re.Pattern[str],
) -> Iterator[str]:
    if not isinstance(raw_value, str):
        yield BLANK_LABEL
        return

    tokens = _iter_non_empty_dimension_tokens(raw_value, delimiter_pattern)
    if mode == "first":
        for token in tokens:
            yield token
            return
        yield BLANK_LABEL
        return

    seen: set[str] = set()
    raw_token_count = 0
    for token in tokens:
        raw_token_count += 1
        if raw_token_count > MAX_DIMENSION_TOKENS_PER_CELL:
            _raise_ranking_budget_error()
        if token in seen:
            continue
        seen.add(token)
        yield token

    if raw_token_count == 0:
        yield BLANK_LABEL


def _canonical_label(label: Any) -> str:
    if not isinstance(label, str):
        return BLANK_LABEL
    stripped = label.strip()
    return stripped if stripped else BLANK_LABEL


def _strip_measure_prefix(value: str) -> str:
    text = value.strip()
    match = NUMERIC_CITATION_PREFIX_PATTERN.match(text)
    if not match:
        return value
    return match.group(1)


def _parse_numeric(value: Any) -> float | None:
    if not isinstance(value, str):
        return None

    stripped = value.strip()
    if not stripped:
        return None

    normalized = stripped.replace(",", "")
    normalized = _strip_measure_prefix(normalized)
    if not NUMERIC_PLAIN_PATTERN.fullmatch(normalized):
        return None

    parsed = float(normalized)
    if not math.isfinite(parsed):
        return None
    return parsed


def _measure_row_value(mode: str, state: dict[str, Any]) -> float | int:
    if mode == "count":
        return state["count"]
    if mode == "sum":
        return state["sum"]
    if mode == "average":
        if state["numeric_count"] == 0:
            return 0.0
        return state["sum"] / state["numeric_count"]
    if mode == "max":
        max_value = state["max"]
        return 0.0 if max_value is None else max_value
    if mode == "min":
        min_value = state["min"]
        return 0.0 if min_value is None else min_value
    raise ValueError(f"unsupported mode: {mode}")


def _measure_share(mode: str, state: dict[str, Any], total_value: float, total_count: int) -> float:
    if mode == "sum" and total_value > 0:
        return _measure_row_value(mode, state) / total_value
    if total_count == 0:
        return 0
    return state["count"] / total_count


def _validate_finite_measure_value(mode: str, value: float | int) -> float | int:
    if mode == "count":
        return value
    if not math.isfinite(value):
        raise AnalysisContractError("analysis result is not finite", details={})
    return value


def _build_rows(
    mode: str,
    buckets: dict[str, dict[str, Any]],
    total_value: float,
    total_count: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label, state in buckets.items():
        value = _measure_row_value(mode, state)
        value = _validate_finite_measure_value(mode, value)

        rows.append(
            {
                "row_kind": "dimension_value",
                "label": _canonical_label(label),
                "value": value,
                "count": state["count"],
                "share": _measure_share(
                    mode, state, total_value=total_value, total_count=total_count
                ),
            }
        )

        if mode in {"count", "sum"} and not math.isfinite(rows[-1]["share"]):
            raise AnalysisContractError("analysis result is not finite", details={})

    return sorted(
        rows,
        key=lambda item: (
            -item["value"] if isinstance(item["value"], (int, float)) else 0,
            -item["count"],
            item["label"],
        ),
    )


def _new_bucket_state() -> dict[str, Any]:
    return {"count": 0, "sum": 0.0, "numeric_count": 0, "max": None, "min": None}


def _update_bucket_state(
    state: dict[str, Any],
    parsed: float | None,
    mode: str,
) -> None:
    state["count"] += 1
    if mode == "count" or parsed is None:
        return
    state["sum"] += parsed
    state["numeric_count"] += 1
    state["max"] = parsed if state["max"] is None else max(state["max"], parsed)
    state["min"] = parsed if state["min"] is None else min(state["min"], parsed)


def _aggregate_rows(
    expanded_rows: Iterable[tuple[str, float | None]],
    mode: str,
) -> tuple[dict[str, dict[str, Any]], int]:
    buckets: dict[str, dict[str, Any]] = {}
    analyzed_rows = 0

    for label, parsed in expanded_rows:
        next_analyzed_rows = analyzed_rows + 1
        if next_analyzed_rows > MAX_EXPANDED_CONTRIBUTIONS:
            _raise_ranking_budget_error()

        bucket = buckets.get(label)
        if bucket is None:
            if len(buckets) >= MAX_DISTINCT_BUCKETS:
                _raise_ranking_budget_error()
            bucket = _new_bucket_state()
            buckets[label] = bucket

        _update_bucket_state(bucket, parsed, mode)
        analyzed_rows = next_analyzed_rows

    return buckets, analyzed_rows


def _iter_expanded_rows(
    rows: list[dict[str, str]],
    spec: dict[str, Any],
) -> Iterator[tuple[str, float | None]]:
    dimension = spec["dimension"]
    measure = spec["measure"]
    mode = measure["mode"]
    multi_value_mode = spec["multi_value_mode"]
    measure_column = measure["column"] if measure["column"] is not None else ""
    delimiter_pattern = _dimension_delimiter_pattern(dimension)

    for row in rows:
        parsed_value: float | None = None
        if mode != "count":
            parsed_value = _parse_numeric(row.get(measure_column, ""))

        yield from (
            (label, parsed_value)
            for label in _iter_dimension_values(
                row.get(dimension, ""),
                multi_value_mode,
                delimiter_pattern,
            )
        )


def _merge_bucket_state(target: dict[str, Any], source: dict[str, Any]) -> None:
    target["count"] += source["count"]
    target["sum"] += source["sum"]
    target["numeric_count"] += source["numeric_count"]
    if source["max"] is not None:
        target["max"] = (
            source["max"] if target["max"] is None else max(target["max"], source["max"])
        )
    if source["min"] is not None:
        target["min"] = (
            source["min"] if target["min"] is None else min(target["min"], source["min"])
        )


def analyze_csv(
    source: str | Path,
    spec: dict[str, Any],
    *,
    allowed_root: str | Path,
) -> dict[str, Any]:
    validate_allowed_root(allowed_root)
    validated = validate_analysis_spec(spec)
    if Path(source).suffix.casefold() == ".json":
        dataset = read_dataset_v2(source, allowed_root=allowed_root)
        columns = list(dataset.manifest.raw_header)
        rows = [
            dict(zip(columns, row.values, strict=True))
            for row in dataset.rows
        ]
        manifest: dict[str, object] = {
            "columns": columns,
            "row_count": dataset.manifest.input_rows,
            "content_sha256": dataset.manifest.source_input_sha256,
        }
    else:
        rows, manifest = read_csv_rows(source, allowed_root=allowed_root)

    if validated["dimension"] not in manifest["columns"]:
        raise AnalysisContractError(
            "analysis spec references missing dimension",
            details={},
        )

    measure = validated["measure"]
    if measure["mode"] != "count":
        if measure["column"] not in manifest["columns"]:
            raise AnalysisContractError(
                "analysis spec references missing measure column",
                details={},
            )

    mode = measure["mode"]
    expanded_rows = _iter_expanded_rows(rows, validated)
    buckets, analyzed_rows = _aggregate_rows(expanded_rows, mode)
    input_rows = manifest["row_count"]
    top_n = int(validated["top_n"])

    total_count = analyzed_rows
    if mode in {"count", "sum"}:
        total_value = sum(_measure_row_value(mode, state) for state in buckets.values())
        total_value = _validate_finite_measure_value(mode, total_value)
    else:
        total_value = 0.0

    ranked_rows = _build_rows(mode, buckets, total_value, total_count)
    ranked_rows = ranked_rows[:top_n]

    if validated["include_other"] and len(ranked_rows) < len(buckets):
        top_rows = ranked_rows
        top_labels = {row["label"] for row in top_rows}
        other_state = _new_bucket_state()
        for label, state in buckets.items():
            if label in top_labels:
                continue
            _merge_bucket_state(other_state, state)

        if other_state["count"] > 0:
            other_value = _validate_finite_measure_value(
                mode, _measure_row_value(mode, other_state)
            )
            other_share = _measure_share(
                mode,
                other_state,
                total_value=total_value,
                total_count=total_count,
            )
            if mode in {"count", "sum"} and not math.isfinite(other_share):
                raise AnalysisContractError("analysis result is not finite", details={})

            ranked_rows = top_rows + [
                {
                    "row_kind": "remainder",
                    "label": "その他",
                    "value": other_value,
                    "count": other_state["count"],
                    "share": other_share,
                }
            ]
        else:
            ranked_rows = top_rows

    result = {
        "analysis_type": "ranking",
        "dimension": validated["dimension"],
        "measure": {
            "mode": mode,
            "column": measure["column"],
        },
        "population": {
            "input_rows": input_rows,
            "analyzed_rows": analyzed_rows,
        },
        "rows": ranked_rows,
        "warnings": [],
    }
    result = validate_analysis_result(result)

    output = {
        "analysis_contract_version": ANALYSIS_CONTRACT_VERSION,
        "ok": True,
        "result": result,
        "receipt": {
            "algorithm_id": ALGORITHM_ID,
            "package_version": PACKAGE_VERSION,
            "input_sha256": manifest["content_sha256"],
            "spec_sha256": _canonical_sha256(validated),
            "result_sha256": _canonical_sha256(result),
        },
    }

    return output
