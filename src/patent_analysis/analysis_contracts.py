from __future__ import annotations

import json
import math
from copy import deepcopy
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator, validators

ANALYSIS_CONTRACT_VERSION = "1.0.0"


class AnalysisContractError(ValueError):
    """Raised when an AnalysisSpec violates the public analysis contract."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "analysis.invalid",
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.safe_message = message
        self.retryable = retryable
        self.details = details or {}

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.safe_message,
            "retryable": self.retryable,
            "details": self.details,
        }


def _is_integer(_checker: Any, instance: Any) -> bool:
    if isinstance(instance, bool):
        return False
    if isinstance(instance, int):
        return True
    return isinstance(instance, float) and math.isfinite(instance) and instance.is_integer()


def _is_strict_number(_checker: Any, instance: Any) -> bool:
    return (
        isinstance(instance, (int, float))
        and not isinstance(instance, bool)
        and (not isinstance(instance, float) or math.isfinite(instance))
    )


_strict_type_checker = Draft202012Validator.TYPE_CHECKER.redefine_many(
    {"integer": _is_integer, "number": _is_strict_number}
)
StrictDraft202012Validator = validators.extend(
    Draft202012Validator,
    type_checker=_strict_type_checker,
)


def get_analysis_spec_schema() -> dict[str, Any]:
    schema_text = (
        files("patent_analysis")
        .joinpath("schemas", "analysis-spec.schema.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(schema_text)


def get_analysis_result_schema() -> dict[str, Any]:
    schema_text = (
        files("patent_analysis")
        .joinpath("schemas", "analysis-result.schema.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(schema_text)


def _is_blank_text(value: Any) -> bool:
    return isinstance(value, str) and not value.strip()


def _validate_semantic_fields(spec: dict[str, Any]) -> None:
    if _is_blank_text(spec.get("dimension")):
        raise AnalysisContractError(
            "analysis spec contains blank fields",
            code="analysis.invalid",
            details={},
        )

    measure = spec.get("measure")
    if isinstance(measure, dict) and _is_blank_text(measure.get("column")):
        raise AnalysisContractError(
            "analysis spec contains blank fields",
            code="analysis.invalid",
            details={},
        )


def validate_analysis_spec(spec: Any) -> dict[str, Any]:
    schema = get_analysis_spec_schema()
    if not isinstance(spec, dict):
        raise AnalysisContractError(
            "analysis spec must be an object",
            code="analysis.invalid",
            details={},
        )

    _validate_semantic_fields(spec)

    errors = sorted(
        StrictDraft202012Validator(schema).iter_errors(spec),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        raise AnalysisContractError(
            "analysis spec violates the schema",
            code="analysis.invalid",
            details={},
        )
    return dict(spec)


def _validate_result_semantics(result: dict[str, Any]) -> None:
    rows = result["rows"]
    seen_rows: set[tuple[str, str]] = set()
    remainder_count = 0
    dimension_value_seen = False

    if _is_blank_text(result["dimension"]):
        raise AnalysisContractError(
            "analysis result violates semantic rules",
            code="analysis.invalid",
            details={},
        )

    for index, row in enumerate(rows):
        if _is_blank_text(row["label"]):
            raise AnalysisContractError(
                "analysis result violates semantic rules",
                code="analysis.invalid",
                details={},
            )

        row_key = (row["row_kind"], row["label"])
        if row_key in seen_rows:
            raise AnalysisContractError(
                "analysis result violates semantic rules",
                code="analysis.invalid",
                details={},
            )
        seen_rows.add(row_key)

        if row["row_kind"] == "dimension_value":
            dimension_value_seen = True
            continue

        remainder_count += 1
        if (
            remainder_count > 1
            or not dimension_value_seen
            or row["label"] != "その他"
            or index != len(rows) - 1
        ):
            raise AnalysisContractError(
                "analysis result violates semantic rules",
                code="analysis.invalid",
                details={},
            )


def validate_analysis_result(result: Any) -> dict[str, Any]:
    schema = get_analysis_result_schema()
    if not isinstance(result, dict):
        raise AnalysisContractError(
            "analysis result must be an object",
            code="analysis.invalid",
            details={},
        )

    errors = sorted(
        StrictDraft202012Validator(schema).iter_errors(result),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        raise AnalysisContractError(
            "analysis result violates the schema",
            code="analysis.invalid",
            details={},
        )

    _validate_result_semantics(result)
    return deepcopy(result)
