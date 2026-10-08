from __future__ import annotations

import json
import math
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator, validators

CONTRACT_VERSION = "1.0.0"
MAX_DOCUMENT_DEPTH = 64


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

SUPPORTED_RENDER_MARKS_BY_ANALYSIS = {
    "ranking": {"bar"},
    "timeline": {"line", "area"},
    "matrix": {"bubble", "heatmap", "scatter", "matrix_pie_glyph"},
    "compara": {"heatmap"},
    "composition": {"donut", "pie", "treemap"},
    "growth": {"bar", "quadrant"},
    "entry_exit": {"bubble"},
    "concentration": {"line"},
    "cooccurrence": {"heatmap"},
    "citation": {"bubble"},
    "network": {"network"},
    "lifecycle": {"bubble"},
}


class OperationContractError(ValueError):
    """Raised when an OperationPlan violates the public contract."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "contract.invalid",
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


def get_operation_schema() -> dict[str, Any]:
    schema_text = (
        files("patent_analysis")
        .joinpath("schemas", "operation.schema.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(schema_text)


def get_operation_plan_cases() -> dict[str, Any]:
    cases_text = (
        files("patent_analysis")
        .joinpath("schemas", "operation-plan-cases.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(cases_text)


def _operation_names(schema: dict[str, Any]) -> tuple[str, ...]:
    definitions = schema.get("$defs", {})
    operation_union = definitions.get("operation", {})
    names: list[str] = []
    for choice in operation_union.get("oneOf", []):
        reference = choice.get("$ref")
        if not isinstance(reference, str):
            continue
        definition = definitions.get(reference.rsplit("/", 1)[-1], {})
        for part in definition.get("allOf", []):
            operation_type = part.get("properties", {}).get("type", {})
            name = operation_type.get("const")
            if isinstance(name, str):
                names.append(name)
    return tuple(sorted(set(names)))


def list_operations() -> tuple[str, ...]:
    return _operation_names(get_operation_schema())


def describe_contract() -> dict[str, Any]:
    schema = get_operation_schema()
    return {
        "contract_version": CONTRACT_VERSION,
        "schema_id": schema["$id"],
        "operations": list(list_operations()),
        "commands": ["contract", "validate-plan"],
    }


def _enforce_value_bounds(value: Any) -> None:
    stack: list[tuple[Any, int]] = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        if depth > MAX_DOCUMENT_DEPTH:
            raise OperationContractError(
                "operation plan is nested too deeply",
                details={"limit": MAX_DOCUMENT_DEPTH},
            )
        if isinstance(current, float) and not math.isfinite(current):
            raise OperationContractError(
                "operation plan contains a non-finite number",
                details={},
            )
        if isinstance(current, dict):
            stack.extend((nested, depth + 1) for nested in current.values())
        elif isinstance(current, list):
            stack.extend((nested, depth + 1) for nested in current)


def _preflight_operations(plan: Any, operation_names: set[str]) -> None:
    if not isinstance(plan, dict):
        raise OperationContractError("operation plan must be an object")
    intent = plan.get("intent")
    if isinstance(intent, str) and not intent.strip():
        raise OperationContractError("operation plan intent is required")
    operations = plan.get("operations")
    if not isinstance(operations, list):
        return
    for index, operation in enumerate(operations):
        if not isinstance(operation, dict):
            continue
        operation_type = operation.get("type")
        if isinstance(operation_type, str) and operation_type not in operation_names:
            raise OperationContractError(
                "unknown operation",
                code="operation.unknown",
                details={"operation_index": index},
            )


def _validate_semantics(plan: dict[str, Any]) -> None:
    operations = plan["operations"]
    analysis_operations = [
        operation for operation in operations if operation.get("type") == "create_analysis"
    ]
    if len(analysis_operations) > 1:
        raise OperationContractError(
            "operation plan cannot include multiple create_analysis operations"
        )
    render_operations = [
        operation for operation in operations if operation.get("type") == "set_render_mode"
    ]
    if len(render_operations) > 1:
        raise OperationContractError(
            "operation plan cannot include multiple set_render_mode operations"
        )

    analysis_type = "ranking"
    if analysis_operations:
        analysis_type = analysis_operations[0]["params"]["analysis_type"]
    if render_operations:
        mark = render_operations[0]["params"]["mark"]
        supported = SUPPORTED_RENDER_MARKS_BY_ANALYSIS.get(analysis_type)
        if supported is not None and mark not in supported:
            raise OperationContractError(
                f"{mark} is not supported for {analysis_type}",
                code="operation.incompatible_render",
                details={"analysis_type": analysis_type, "mark": mark},
            )


def validate_operation_plan(plan: Any) -> None:
    schema = get_operation_schema()
    _enforce_value_bounds(plan)
    _preflight_operations(plan, set(_operation_names(schema)))
    errors = sorted(
        StrictDraft202012Validator(schema).iter_errors(plan),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        raise OperationContractError(
            "operation plan violates the schema",
            details={},
        )
    _validate_semantics(plan)
