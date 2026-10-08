from __future__ import annotations

import json
import math
from collections.abc import Callable
from copy import deepcopy
from importlib.resources import files
from typing import Any

from patent_analysis._render_canonical import (
    CanonicalJsonError,
    canonical_json_bytes,
    parse_canonical_json_bytes,
    sha256_bytes,
    strict_b64decode,
)
from patent_analysis._render_text import (
    RenderTextError,
    grapheme_count,
    truncate_title_dimension,
    validate_safe_text,
)
from patent_analysis.analysis_contracts import StrictDraft202012Validator

_MAX_TREE_DEPTH = 64
_MAX_TREE_NODES = 250_000
_MAX_STRING_CODE_POINTS = 2_000_000
_MAX_DISPLAY_GRAPHEMES = 20_000
_MAX_CHART_MODEL_BYTES = 2 * 1024 * 1024
_MAX_RENDER_SPEC_BYTES = 16 * 1024
_MAX_RENDER_PIXELS = 16_777_216


class RenderContractError(ValueError):
    """Safe fixed error for invalid renderer contract data."""

    def __init__(
        self,
        message: object = None,
        *,
        code: object = None,
        retryable: object = None,
        details: object = None,
    ) -> None:
        del message, code, retryable, details
        super().__init__("Render contract is invalid")
        self.code = "render.contract_invalid"
        self.safe_message = "Render contract is invalid"
        self.retryable = False
        self.details: dict[str, object] = {}
        self.__suppress_context__ = True

    def as_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "safe_message": self.safe_message,
            "retryable": self.retryable,
            "details": {},
        }


class _ContractViolation(ValueError):
    pass


def _load_schema(name: str) -> dict[str, Any]:
    text = files("patent_analysis").joinpath("schemas", name).read_text(encoding="utf-8")
    loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise _ContractViolation
    return loaded


def get_label_overlay_pack_schema() -> dict[str, Any]:
    return _load_schema("label-overlay-pack.schema.json")


def get_chart_model_schema() -> dict[str, Any]:
    return _load_schema("chart-model.schema.json")


def get_chart_model_build_receipt_schema() -> dict[str, Any]:
    return _load_schema("chart-model-build-receipt.schema.json")


def get_render_spec_schema() -> dict[str, Any]:
    return _load_schema("render-spec.schema.json")


def _preflight_tree(value: Any) -> None:
    node_count = 0
    string_code_points = 0
    active_containers: set[int] = set()
    stack: list[tuple[Any, int, bool]] = [(value, 0, False)]

    while stack:
        current, depth, exiting = stack.pop()
        if exiting:
            active_containers.remove(id(current))
            continue

        if depth > _MAX_TREE_DEPTH:
            raise _ContractViolation
        node_count += 1
        if node_count > _MAX_TREE_NODES:
            raise _ContractViolation

        if isinstance(current, str):
            string_code_points += len(current)
            if string_code_points > _MAX_STRING_CODE_POINTS or any(
                0xD800 <= ord(character) <= 0xDFFF for character in current
            ):
                raise _ContractViolation
            continue
        if current is None or isinstance(current, (bool, int)):
            continue
        if isinstance(current, float):
            if not math.isfinite(current) or (
                current == 0.0 and math.copysign(1.0, current) < 0
            ):
                raise _ContractViolation
            continue
        if isinstance(current, dict):
            container_id = id(current)
            if container_id in active_containers:
                raise _ContractViolation
            active_containers.add(container_id)
            stack.append((current, depth, True))
            for key, item in reversed(tuple(current.items())):
                if not isinstance(key, str):
                    raise _ContractViolation
                node_count += 1
                string_code_points += len(key)
                if (
                    node_count > _MAX_TREE_NODES
                    or string_code_points > _MAX_STRING_CODE_POINTS
                    or any(0xD800 <= ord(character) <= 0xDFFF for character in key)
                ):
                    raise _ContractViolation
                stack.append((item, depth + 1, False))
            continue
        if isinstance(current, (list, tuple)):
            container_id = id(current)
            if container_id in active_containers:
                raise _ContractViolation
            active_containers.add(container_id)
            stack.append((current, depth, True))
            for item in reversed(current):
                stack.append((item, depth + 1, False))
            continue
        raise _ContractViolation


def _schema_validate(value: Any, schema: dict[str, Any]) -> None:
    _preflight_tree(value)
    if next(StrictDraft202012Validator(schema).iter_errors(value), None) is not None:
        raise _ContractViolation


def _check_graphemes(value: str, minimum: int, maximum: int) -> None:
    count = grapheme_count(value)
    if count < minimum or count > maximum:
        raise _ContractViolation


def _check_optional_graphemes(value: str | None, maximum: int) -> None:
    if value is not None:
        _check_graphemes(value, 0, maximum)


def _validate_overlay_impl(value: Any) -> dict[str, Any]:
    schema = get_label_overlay_pack_schema()
    _schema_validate(value, schema)
    if not isinstance(value, dict):
        raise _ContractViolation

    dimension = value["dimension"]
    _check_graphemes(dimension["source_label"], 1, 256)
    _check_graphemes(dimension["display_label"], 1, 256)
    _check_optional_graphemes(dimension["description"], 256)

    for row in value["rows"]:
        _check_graphemes(row["display_label"], 1, 256)
        _check_optional_graphemes(row["description"], 256)
        for evidence_id in row["evidence_ids"]:
            _check_graphemes(evidence_id, 1, 256)
    return value


def _chart_display_texts(value: dict[str, Any]) -> list[str]:
    dimension = value["dimension"]
    texts = [
        value["title"],
        dimension["source_label"],
        dimension["display_label"],
    ]
    if dimension["description"] is not None:
        texts.append(dimension["description"])
    if value["measure"]["column"] is not None:
        texts.append(value["measure"]["column"])
    for row in value["rows"]:
        texts.extend(
            [
                row["source_label"],
                row["display_label"],
                row["semantic_label"],
            ]
        )
        if row["description"] is not None:
            texts.append(row["description"])
    texts.extend(value["warnings"])
    return texts


def _validate_chart_model_impl(value: Any) -> dict[str, Any]:
    schema = get_chart_model_schema()
    _schema_validate(value, schema)
    if not isinstance(value, dict):
        raise _ContractViolation

    dimension = value["dimension"]
    _check_graphemes(value["title"], 1, 256)
    _check_graphemes(dimension["source_label"], 1, 256)
    _check_graphemes(dimension["display_label"], 1, 256)
    _check_optional_graphemes(dimension["description"], 256)
    column = value["measure"]["column"]
    if column is not None:
        _check_graphemes(column, 1, 256)

    expected_title = truncate_title_dimension(dimension["display_label"])
    if value["title"] != expected_title:
        raise _ContractViolation

    rows = value["rows"]
    analyzed_rows = value["population"]["analyzed_rows"]
    if (analyzed_rows == 0) != (len(rows) == 0):
        raise _ContractViolation

    remainder_seen = False
    count_sum = 0
    for expected_index, row in enumerate(rows):
        if row["index"] != expected_index:
            raise _ContractViolation
        _check_graphemes(row["display_label"], 1, 256)
        _check_optional_graphemes(row["description"], 256)
        expected_semantic_label = (
            "データ中の分類値"
            if row["row_kind"] == "dimension_value"
            else "上位表示外の合計"
        )
        if row["semantic_label"] != expected_semantic_label:
            raise _ContractViolation
        if row["row_kind"] == "remainder":
            if remainder_seen or expected_index != len(rows) - 1 or row["source_label"] != "その他":
                raise _ContractViolation
            remainder_seen = True
        count_sum += row["count"]

    if count_sum > analyzed_rows:
        raise _ContractViolation

    display_graphemes = 0
    for text in _chart_display_texts(value):
        validate_safe_text(text)
        display_graphemes += grapheme_count(text)
        if display_graphemes > _MAX_DISPLAY_GRAPHEMES:
            raise _ContractViolation
    return value


def _validate_receipt_impl(
    value: Any, *, chart_model: dict[str, Any] | None = None
) -> dict[str, Any]:
    schema = get_chart_model_build_receipt_schema()
    _schema_validate(value, schema)
    if not isinstance(value, dict):
        raise _ContractViolation

    raw = strict_b64decode(value["chart_model_bytes"], _MAX_CHART_MODEL_BYTES)
    if sha256_bytes(raw) != value["chart_model_sha256"]:
        raise _ContractViolation
    decoded_model = parse_canonical_json_bytes(raw, _MAX_CHART_MODEL_BYTES)
    _validate_chart_model_impl(decoded_model)

    if chart_model is not None:
        _validate_chart_model_impl(chart_model)
        if canonical_json_bytes(chart_model) != raw:
            raise _ContractViolation
    if (
        value["analysis_result_sha256"] != decoded_model["analysis_result_sha256"]
        or value["label_overlay_sha256"] != decoded_model["label_overlay_sha256"]
        or value["row_count"] != len(decoded_model["rows"])
    ):
        raise _ContractViolation
    return value


def _validate_render_spec_impl(value: Any, *, row_count: int | None = None) -> dict[str, Any]:
    schema = get_render_spec_schema()
    _schema_validate(value, schema)
    if not isinstance(value, dict):
        raise _ContractViolation

    height = value["height"]
    allowed_heights = {675, *(160 + 36 * count for count in range(15, 102))}
    if height not in allowed_heights:
        raise _ContractViolation
    if row_count is not None:
        if (
            isinstance(row_count, bool)
            or not isinstance(row_count, int)
            or not 0 <= row_count <= 101
        ):
            raise _ContractViolation
        if height != max(675, 160 + 36 * row_count):
            raise _ContractViolation
    if value["width"] * height > _MAX_RENDER_PIXELS:
        raise _ContractViolation
    if len(canonical_json_bytes(value)) > _MAX_RENDER_SPEC_BYTES:
        raise _ContractViolation
    return value


_KNOWN_FAILURES = (
    CanonicalJsonError,
    RenderTextError,
    _ContractViolation,
    RecursionError,
    TypeError,
    ValueError,
    OverflowError,
)


def _validated_copy(operation: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    failed = False
    validated_copy: dict[str, Any] | None = None
    try:
        validated_copy = deepcopy(operation())
    except _KNOWN_FAILURES:
        failed = True
    if failed or validated_copy is None:
        raise RenderContractError()
    return validated_copy


def validate_label_overlay_pack(value: Any) -> dict[str, Any]:
    return _validated_copy(lambda: _validate_overlay_impl(value))


def validate_chart_model(value: Any) -> dict[str, Any]:
    return _validated_copy(lambda: _validate_chart_model_impl(value))


def validate_chart_model_build_receipt(
    value: Any, *, chart_model: dict[str, Any] | None = None
) -> dict[str, Any]:
    return _validated_copy(lambda: _validate_receipt_impl(value, chart_model=chart_model))


def validate_render_spec(
    value: Any, *, row_count: int | None = None
) -> dict[str, Any]:
    return _validated_copy(lambda: _validate_render_spec_impl(value, row_count=row_count))
