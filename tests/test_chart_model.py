from __future__ import annotations

import json
import math
from collections import defaultdict
from copy import deepcopy
from importlib.resources import files
from typing import Any

import pytest
from jsonschema.exceptions import SchemaError, ValidationError

from patent_analysis import (
    build_ranking_chart_model as public_build_ranking_chart_model,
)
from patent_analysis import (
    build_ranking_render_spec as public_build_ranking_render_spec,
)
from patent_analysis._render_canonical import (
    CanonicalJsonError,
    canonical_json_bytes,
    sha256_bytes,
    strict_b64decode,
    strict_b64encode,
)
from patent_analysis._render_contracts import (
    RenderContractError,
    validate_chart_model_build_receipt,
)
from patent_analysis._render_text import RenderTextError
from patent_analysis._version import PACKAGE_VERSION
from patent_analysis.analysis import _canonical_sha256 as existing_result_sha256
from patent_analysis.analysis_contracts import AnalysisContractError
from patent_analysis.chart_model import (
    _resolve_chart_inputs,
    _translate_contract_failure,
    build_ranking_chart_model,
    build_ranking_render_spec,
)


def success_envelope() -> dict[str, object]:
    result = {
        "analysis_type": "ranking",
        "dimension": "IPC",
        "measure": {"mode": "count", "column": None},
        "population": {"input_rows": 3, "analyzed_rows": 3},
        "rows": [
            {
                "row_kind": "dimension_value",
                "label": "その他",
                "value": 2,
                "count": 2,
                "share": 2 / 3,
            },
            {
                "row_kind": "remainder",
                "label": "その他",
                "value": 1,
                "count": 1,
                "share": 1 / 3,
            },
        ],
        "warnings": [],
    }
    return {
        "analysis_contract_version": "1.0.0",
        "ok": True,
        "result": result,
        "receipt": {
            "algorithm_id": "ranking.v1",
            "package_version": PACKAGE_VERSION,
            "input_sha256": "1" * 64,
            "spec_sha256": "2" * 64,
            "result_sha256": existing_result_sha256(result),
        },
    }


def label_overlay(envelope: dict[str, object]) -> dict[str, object]:
    result = envelope["result"]
    receipt = envelope["receipt"]
    assert isinstance(result, dict)
    assert isinstance(receipt, dict)
    rows = result["rows"]
    assert isinstance(rows, list)
    return {
        "label_overlay_contract_version": "1.0.0",
        "analysis_result_sha256": receipt["result_sha256"],
        "dimension": {
            "source_label": result["dimension"],
            "display_label": "国際特許分類",
            "description": None,
        },
        "producer": {"id": "test-workflow", "version": "1.0.0"},
        "selection_policy_id": "identity.v1",
        "rows": [
            {
                "index": index,
                "row_kind": row["row_kind"],
                "source_label": row["label"],
                "display_label": f"表示{index}",
                "description": None,
                "provenance_state": "manual",
                "review_state": "reviewed",
                "evidence_ids": [],
                "evidence_sha256": [],
            }
            for index, row in enumerate(rows)
        ],
    }


def _refresh_result_hash(envelope: dict[str, object]) -> None:
    receipt = envelope["receipt"]
    assert isinstance(receipt, dict)
    receipt["result_sha256"] = existing_result_sha256(envelope["result"])


def _assert_safe_error(error: RenderContractError, secret: str) -> None:
    assert error.code == "render.contract_invalid"
    assert error.safe_message == "Render contract is invalid"
    assert error.retryable is False
    assert error.details == {}
    assert error.__context__ is None
    assert error.__cause__ is None
    assert secret not in str(error)
    assert secret not in repr(vars(error))
    assert secret not in repr(error.as_dict())


def _install_preflight_spies(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    from patent_analysis import chart_model

    reached: list[str] = []

    def unexpected_call(name: str) -> Any:
        def fail(*_args: object, **_kwargs: object) -> None:
            reached.append(name)
            raise AssertionError(f"preflight reached {name}")

        return fail

    for name in (
        "validate_analysis_result",
        "existing_result_sha256",
        "truncate_title_dimension",
    ):
        monkeypatch.setattr(chart_model, name, unexpected_call(name))
    return reached


def test_resolve_without_overlay_uses_existing_hash_and_identity_mapping() -> None:
    envelope = success_envelope()
    before = deepcopy(envelope)

    resolved = _resolve_chart_inputs(envelope, None)

    assert resolved.result == envelope["result"]
    assert resolved.result is not envelope["result"]
    assert resolved.analysis_result_sha256 == envelope["receipt"]["result_sha256"]
    assert resolved.overlay is None
    assert resolved.label_overlay_sha256 is None
    assert envelope == before


def test_complete_overlay_binds_same_text_rows_independently_and_returns_copies() -> None:
    envelope = success_envelope()
    overlay = label_overlay(envelope)
    envelope_before = deepcopy(envelope)
    overlay_before = deepcopy(overlay)

    resolved = _resolve_chart_inputs(envelope, overlay)

    assert [row["row_kind"] for row in resolved.overlay["rows"]] == [
        "dimension_value",
        "remainder",
    ]
    assert [row["source_label"] for row in resolved.overlay["rows"]] == [
        "その他",
        "その他",
    ]
    assert resolved.result is not envelope["result"]
    assert resolved.overlay is not overlay
    assert resolved.label_overlay_sha256 == sha256_bytes(canonical_json_bytes(overlay))
    resolved.result["rows"][0]["label"] = "changed"
    resolved.overlay["rows"][0]["display_label"] = "changed"
    assert envelope == envelope_before
    assert overlay == overlay_before


@pytest.mark.parametrize(
    ("case", "mutate"),
    [
        ("top_missing", lambda value: value.pop("ok")),
        ("top_unknown", lambda value: value.update(unexpected=True)),
        ("version", lambda value: value.update(analysis_contract_version="1.0.1")),
        ("ok_false", lambda value: value.update(ok=False)),
        ("receipt_missing", lambda value: value["receipt"].pop("input_sha256")),
        ("receipt_unknown", lambda value: value["receipt"].update(unexpected=True)),
        ("algorithm", lambda value: value["receipt"].update(algorithm_id="ranking.v2")),
        ("package", lambda value: value["receipt"].update(package_version="9.9.9")),
        ("input_hash", lambda value: value["receipt"].update(input_sha256="A" * 64)),
        ("spec_hash", lambda value: value["receipt"].update(spec_sha256="2" * 63)),
        ("result_hash_shape", lambda value: value["receipt"].update(result_sha256="g" * 64)),
        ("result_hash_binding", lambda value: value["receipt"].update(result_sha256="0" * 64)),
    ],
)
def test_envelope_validation_is_closed_exact_and_nonmutating(
    case: str,
    mutate: Any,
) -> None:
    del case
    envelope = success_envelope()
    mutate(envelope)
    before = deepcopy(envelope)

    with pytest.raises(RenderContractError):
        _resolve_chart_inputs(envelope, None)

    assert envelope == before


def _mutate_overlay_case(
    overlay: dict[str, object],
    envelope: dict[str, object],
    case: str,
) -> None:
    rows = overlay["rows"]
    assert isinstance(rows, list)
    if case == "result_hash":
        overlay["analysis_result_sha256"] = "0" * 64
    elif case == "dimension":
        overlay["dimension"]["source_label"] = "CPC"
    elif case == "missing_row":
        rows.pop()
    elif case == "extra_row":
        rows.append(deepcopy(rows[0]))
        rows[-1]["index"] = 2
    elif case == "reordered_rows":
        rows.reverse()
        rows[0]["index"] = 0
        rows[1]["index"] = 1
    elif case == "duplicate_rows":
        rows[1] = deepcopy(rows[0])
        rows[1]["index"] = 1
    elif case == "wrong_index":
        rows[0]["index"] = 1
    elif case == "wrong_kind":
        rows[0]["row_kind"] = "remainder"
    elif case == "wrong_source":
        rows[0]["source_label"] = "別分類"
    else:
        raise AssertionError(case)
    assert envelope["result"]


@pytest.mark.parametrize(
    "case",
    [
        "result_hash",
        "dimension",
        "missing_row",
        "extra_row",
        "reordered_rows",
        "duplicate_rows",
        "wrong_index",
        "wrong_kind",
        "wrong_source",
    ],
)
def test_overlay_binding_is_complete_exact_and_nonmutating(case: str) -> None:
    envelope = success_envelope()
    overlay = label_overlay(envelope)
    _mutate_overlay_case(overlay, envelope, case)
    envelope_before = deepcopy(envelope)
    overlay_before = deepcopy(overlay)

    with pytest.raises(RenderContractError):
        _resolve_chart_inputs(envelope, overlay)

    assert envelope == envelope_before
    assert overlay == overlay_before


@pytest.mark.parametrize(
    ("source_label", "overlay_label"),
    [
        ("1", "1.0"),
        ("é", "e\u0301"),
        ("e\u0301", "é"),
        ("Alpha", "alpha"),
        (" Alpha", "Alpha"),
        ("Alpha ", "Alpha"),
        ("１", "1"),
    ],
)
def test_binding_does_not_normalize_exact_source_labels(
    source_label: str,
    overlay_label: str,
) -> None:
    envelope = success_envelope()
    result = envelope["result"]
    assert isinstance(result, dict)
    rows = result["rows"]
    assert isinstance(rows, list)
    rows[0]["label"] = source_label
    _refresh_result_hash(envelope)
    overlay = label_overlay(envelope)
    overlay["rows"][0]["source_label"] = overlay_label

    with pytest.raises(RenderContractError):
        _resolve_chart_inputs(envelope, overlay)


def test_existing_result_negative_zero_hash_still_resolves() -> None:
    envelope = success_envelope()
    result = envelope["result"]
    assert isinstance(result, dict)
    result["rows"][0]["value"] = -0.0
    _refresh_result_hash(envelope)

    resolved = _resolve_chart_inputs(envelope, None)

    assert resolved.analysis_result_sha256 == existing_result_sha256(result)
    assert math.copysign(1.0, resolved.result["rows"][0]["value"]) == -1.0


def test_public_builder_rejects_102_rows_before_existing_expensive_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    envelope = success_envelope()
    result = envelope["result"]
    assert isinstance(result, dict)
    result["population"] = {"input_rows": 102, "analyzed_rows": 102}
    result["rows"] = [
        {
            "row_kind": "dimension_value",
            "label": f"分類{index}",
            "value": 1,
            "count": 1,
            "share": 1 / 102,
        }
        for index in range(102)
    ]
    reached = _install_preflight_spies(monkeypatch)

    with pytest.raises(RenderContractError):
        public_build_ranking_chart_model(envelope)

    assert reached == []


def test_public_builder_rejects_over_250000_node_payload_before_existing_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    envelope = success_envelope()
    result = envelope["result"]
    assert isinstance(result, dict)
    result["extra_payload"] = [None] * 250_001
    reached = _install_preflight_spies(monkeypatch)

    with pytest.raises(RenderContractError):
        public_build_ranking_chart_model(envelope)

    assert reached == []


def test_public_builder_rejects_over_2000000_code_point_payload_before_existing_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    envelope = success_envelope()
    result = envelope["result"]
    assert isinstance(result, dict)
    result["extra_payload"] = "x" * 2_000_001
    reached = _install_preflight_spies(monkeypatch)

    with pytest.raises(RenderContractError):
        public_build_ranking_chart_model(envelope)

    assert reached == []


@pytest.mark.parametrize(
    "case",
    ["depth", "cycle", "non_string_key", "unsupported_container", "nonfinite"],
)
def test_public_builder_rejects_non_json_or_unbounded_envelope_structure_early(
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    envelope = success_envelope()
    result = envelope["result"]
    assert isinstance(result, dict)
    if case == "depth":
        nested: object = None
        for _ in range(65):
            nested = [nested]
        result["extra_payload"] = nested
    elif case == "cycle":
        cycle: list[object] = []
        cycle.append(cycle)
        result["extra_payload"] = cycle
    elif case == "non_string_key":
        result[1] = None
    elif case == "unsupported_container":
        result["extra_payload"] = (None,)
    elif case == "nonfinite":
        result["extra_payload"] = float("nan")
    else:
        raise AssertionError(case)
    reached = _install_preflight_spies(monkeypatch)

    with pytest.raises(RenderContractError):
        public_build_ranking_chart_model(envelope)

    assert reached == []


@pytest.mark.parametrize(
    "case",
    [
        "dimension",
        "measure_column",
        "row_identity_source",
        "warning",
        "warning_count",
    ],
)
def test_public_builder_rejects_render_boundary_limits_before_existing_work(
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    envelope = success_envelope()
    result = envelope["result"]
    assert isinstance(result, dict)
    if case == "dimension":
        result["dimension"] = "x" * 4097
    elif case == "measure_column":
        result["measure"] = {"mode": "sum", "column": "x" * 4097}
    elif case == "row_identity_source":
        result["rows"][0]["label"] = "x" * 4097
    elif case == "warning":
        result["warnings"] = ["x" * 4097]
    elif case == "warning_count":
        result["warnings"] = [""] * 33
    else:
        raise AssertionError(case)
    reached = _install_preflight_spies(monkeypatch)

    with pytest.raises(RenderContractError):
        public_build_ranking_chart_model(envelope)

    assert reached == []


def test_all_binding_corpus_cases_execute_with_requirement_polarity() -> None:
    corpus = json.loads(
        files("patent_analysis")
        .joinpath("schemas", "render-contract-cases.json")
        .read_text(encoding="utf-8")
    )
    binding_cases = [
        case for case in corpus["cases"] if case["contract"] == "chart_input_binding"
    ]
    assert {case["name"] for case in binding_cases} == {
        "binding-result-complete-valid",
        "binding-result-hash-invalid",
        "binding-exact-string-valid",
        "binding-distinguishes-one-and-one-point-zero",
        "binding-nonsequential-overlay-index-invalid",
    }

    executed: dict[str, set[str]] = defaultdict(set)
    polarity: dict[str, set[bool]] = defaultdict(set)
    for case in binding_cases:
        requirement = case["requirements"][0]
        polarity[requirement].add(case["valid"])
        if case["valid"]:
            _resolve_chart_inputs(case["analyze_success_envelope"], case["overlay"])
        else:
            with pytest.raises(RenderContractError):
                _resolve_chart_inputs(case["analyze_success_envelope"], case["overlay"])
        executed[requirement].add(case["name"])

    assert set(executed) == {
        "binding-result-hash-dimension-complete-rows",
        "binding-no-normalization-1-vs-1point0",
    }
    assert all(polarity[requirement] == {False, True} for requirement in executed)
    assert sum(len(names) for names in executed.values()) == 5


@pytest.mark.parametrize(
    "lower_error",
    [
        AnalysisContractError("LOWER-SECRET"),
        CanonicalJsonError("LOWER-SECRET"),
        RenderTextError("LOWER-SECRET"),
        json.JSONDecodeError("LOWER-SECRET", "LOWER-SECRET", 0),
        ValidationError("LOWER-SECRET"),
        SchemaError("LOWER-SECRET"),
        TypeError("LOWER-SECRET"),
        ValueError("LOWER-SECRET"),
        RecursionError("LOWER-SECRET"),
    ],
    ids=lambda error: type(error).__name__,
)
def test_known_lower_exception_families_translate_to_detached_safe_error(
    lower_error: Exception,
) -> None:
    def fail() -> None:
        raise lower_error

    with pytest.raises(RenderContractError) as caught:
        _translate_contract_failure(fail)

    _assert_safe_error(caught.value, "LOWER-SECRET")


def test_translated_error_drops_operation_callable_from_translation_frame() -> None:
    secret = "CALLABLE-CLOSURE-SECRET"

    def fail() -> None:
        assert secret
        raise ValueError("LOWER-SECRET")

    with pytest.raises(RenderContractError) as caught:
        _translate_contract_failure(fail)

    traceback = caught.value.__traceback__
    translation_locals: dict[str, object] | None = None
    while traceback is not None:
        if traceback.tb_frame.f_code.co_name == "_translate_contract_failure":
            translation_locals = dict(traceback.tb_frame.f_locals)
            break
        traceback = traceback.tb_next
    assert translation_locals is not None
    assert "operation" not in translation_locals


@pytest.mark.parametrize("fatal_error", [MemoryError(), KeyboardInterrupt(), SystemExit()])
def test_fatal_base_exceptions_are_not_translated(fatal_error: BaseException) -> None:
    def fail() -> None:
        raise fatal_error

    with pytest.raises(type(fatal_error)) as caught:
        _translate_contract_failure(fail)

    assert caught.value is fatal_error


def test_existing_render_contract_error_is_reraised_unchanged() -> None:
    existing = RenderContractError()

    def fail() -> None:
        raise existing

    with pytest.raises(RenderContractError) as caught:
        _translate_contract_failure(fail)

    assert caught.value is existing


def test_builder_preserves_two_other_rows_and_applies_display_only_overlay() -> None:
    envelope = success_envelope()
    overlay = {
        "label_overlay_contract_version": "1.0.0",
        "analysis_result_sha256": envelope["receipt"]["result_sha256"],
        "dimension": {
            "source_label": "IPC",
            "display_label": "技術分類",
            "description": "分類コード別の件数",
        },
        "producer": {"id": "external-workflow", "version": "1.0.0"},
        "selection_policy_id": "reviewed-source-first.v1",
        "rows": [
            {
                "index": 0,
                "row_kind": "dimension_value",
                "source_label": "その他",
                "display_label": "データ中のその他",
                "description": None,
                "provenance_state": "manual",
                "review_state": "reviewed",
                "evidence_ids": [],
                "evidence_sha256": [],
            },
            {
                "index": 1,
                "row_kind": "remainder",
                "source_label": "その他",
                "display_label": "上位外",
                "description": None,
                "provenance_state": "derived",
                "review_state": "reviewed",
                "evidence_ids": [],
                "evidence_sha256": [],
            },
        ],
    }
    envelope_before = deepcopy(envelope)
    overlay_before = deepcopy(overlay)

    model, receipt = public_build_ranking_chart_model(envelope, overlay=overlay)

    assert set(model) == {
        "chart_model_contract_version",
        "chart_type",
        "analysis_result_sha256",
        "label_overlay_sha256",
        "title",
        "dimension",
        "measure",
        "population",
        "rows",
        "warnings",
    }
    assert model["dimension"] == {
        "source_label": "IPC",
        "display_label": "技術分類",
        "description": "分類コード別の件数",
    }
    assert [row["semantic_label"] for row in model["rows"]] == [
        "データ中の分類値",
        "上位表示外の合計",
    ]
    assert [row["display_label"] for row in model["rows"]] == [
        "データ中のその他",
        "上位外",
    ]
    assert [row["value"] for row in model["rows"]] == [2, 1]
    assert [row["row_kind"] for row in model["rows"]] == [
        "dimension_value",
        "remainder",
    ]
    decoded = strict_b64decode(receipt["chart_model_bytes"], max_decoded_bytes=2 * 1024 * 1024)
    assert receipt["analysis_result_sha256"] == (
        "a59e3f8c4ee4243655c91a9b70f2b7521856829447e4bc3df28ff411a2d5352c"
    )
    assert receipt["label_overlay_sha256"] == (
        "bc32fc5cbefc96ddf1b70740ce7def91fc2d7f9753369752e0b40ef9a2c01d3b"
    )
    assert receipt["chart_model_sha256"] == (
        "2ee0cf1b2320cfb53bd460aa401d667ded75d0e72a4366a44f62fe1538f1c67d"
    )
    assert receipt == {
        "chart_model_build_receipt_version": "1.0.0",
        "analysis_result_sha256": envelope["receipt"]["result_sha256"],
        "label_overlay_sha256": sha256_bytes(canonical_json_bytes(overlay)),
        "chart_model_sha256": sha256_bytes(decoded),
        "chart_model_bytes": strict_b64encode(canonical_json_bytes(model)),
        "row_count": 2,
        "builder_id": "patent-analysis.ranking-chart-model-builder",
        "builder_version": PACKAGE_VERSION,
    }
    assert decoded == canonical_json_bytes(model)
    assert validate_chart_model_build_receipt(receipt, chart_model=model) == receipt
    assert envelope == envelope_before
    assert overlay == overlay_before


@pytest.mark.parametrize(
    ("row_count", "height"),
    [(0, 675), (14, 675), (15, 700), (101, 3796)],
)
def test_render_spec_height_is_fixed(row_count: int, height: int) -> None:
    assert public_build_ranking_render_spec(row_count=row_count) == {
        "render_spec_contract_version": "1.0.0",
        "renderer_kind": "ranking.horizontal_bar.svg",
        "locale": "ja-JP",
        "timezone": "UTC",
        "width": 1200,
        "height": height,
        "font_family": "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif",
        "animation": False,
        "axis_label_max_graphemes": 28,
        "echarts_version": "6.1.0",
        "render_profile_id": "ranking-svg-ja-jp-node24-echarts6.v1",
    }


def test_builder_identity_mapping_preserves_values_types_warnings_and_inputs() -> None:
    envelope = success_envelope()
    result = envelope["result"]
    result["measure"] = {"mode": "sum", "column": "請求項数"}
    result["rows"][0].update({"value": 2.5, "count": 2, "share": 2 / 3})
    result["warnings"] = ["警告"]
    _refresh_result_hash(envelope)
    before = deepcopy(envelope)

    model, receipt = build_ranking_chart_model(envelope)

    assert model["dimension"] == {
        "source_label": "IPC",
        "display_label": "IPC",
        "description": None,
    }
    assert model["measure"] == {"mode": "sum", "column": "請求項数"}
    assert model["population"] == {"input_rows": 3, "analyzed_rows": 3}
    assert model["warnings"] == ["警告"]
    assert [row["index"] for row in model["rows"]] == [0, 1]
    assert [row["source_label"] for row in model["rows"]] == ["その他", "その他"]
    assert [row["display_label"] for row in model["rows"]] == ["その他", "その他"]
    assert type(model["rows"][0]["value"]) is float
    assert type(model["rows"][1]["value"]) is int
    assert type(model["rows"][0]["count"]) is int
    assert type(model["rows"][0]["share"]) is float
    assert model["rows"][0]["value"] == 2.5
    assert model["rows"][1]["value"] == 1
    assert receipt["label_overlay_sha256"] is None
    assert envelope == before


def test_builder_accepts_empty_rows_and_truncates_long_title_to_256_graphemes() -> None:
    envelope = success_envelope()
    result = envelope["result"]
    result["dimension"] = "あ" * 251
    result["population"] = {"input_rows": 0, "analyzed_rows": 0}
    result["rows"] = []
    _refresh_result_hash(envelope)

    model, receipt = build_ranking_chart_model(envelope)

    assert model["title"] == "あ" * 249 + "…のランキング"
    assert model["dimension"]["source_label"] == "あ" * 251
    assert model["dimension"]["display_label"] == "あ" * 251
    assert model["rows"] == []
    assert receipt["row_count"] == 0


def test_builder_preserves_complete_bounded_source_and_display_values() -> None:
    envelope = success_envelope()
    result = envelope["result"]
    result["dimension"] = "a" + "\u0301" * 3847 + "b" * 248
    result["rows"][0]["label"] = "c" + "\u0301" * 3847 + "d" * 248
    _refresh_result_hash(envelope)

    model, _receipt = build_ranking_chart_model(envelope)

    assert len(model["dimension"]["source_label"]) == 4096
    assert model["dimension"]["display_label"] == result["dimension"]
    assert len(model["rows"][0]["source_label"]) == 4096
    assert model["rows"][0]["display_label"] == result["rows"][0]["label"]


@pytest.mark.parametrize("invalid_label", ["unsafe\ntext", "あ" * 257])
def test_builder_rejects_unsafe_or_overlong_identity_labels(invalid_label: str) -> None:
    envelope = success_envelope()
    envelope["result"]["rows"][0]["label"] = invalid_label
    _refresh_result_hash(envelope)

    with pytest.raises(RenderContractError):
        build_ranking_chart_model(envelope)


def test_public_builder_rejects_existing_hash_negative_zero_at_chart_boundary() -> None:
    envelope = success_envelope()
    result = envelope["result"]
    result["rows"][0]["value"] = -0.0
    _refresh_result_hash(envelope)
    assert envelope["receipt"]["result_sha256"] == existing_result_sha256(result)

    with pytest.raises(RenderContractError) as caught:
        build_ranking_chart_model(envelope)

    assert caught.value.__context__ is None
    assert caught.value.__cause__ is None
    assert caught.value.as_dict() == {
        "code": "render.contract_invalid",
        "safe_message": "Render contract is invalid",
        "retryable": False,
        "details": {},
    }


def test_builder_serializes_chart_model_exactly_once(monkeypatch: pytest.MonkeyPatch) -> None:
    from patent_analysis import _render_canonical as canonical_module
    from patent_analysis import chart_model

    calls = {"builder_alias": 0, "canonical_module": 0}
    real_builder_serializer = chart_model.canonical_json_bytes
    real_canonical_serializer = canonical_module.canonical_json_bytes

    def counting_builder_serializer(value: object) -> bytes:
        calls["builder_alias"] += 1
        return real_builder_serializer(value)

    def counting_canonical_serializer(value: object) -> bytes:
        calls["canonical_module"] += 1
        return real_canonical_serializer(value)

    monkeypatch.setattr(chart_model, "canonical_json_bytes", counting_builder_serializer)
    monkeypatch.setattr(canonical_module, "canonical_json_bytes", counting_canonical_serializer)

    model, receipt = build_ranking_chart_model(success_envelope())

    assert calls == {"builder_alias": 1, "canonical_module": 0}
    assert sum(calls.values()) == 1
    assert len(strict_b64decode(receipt["chart_model_bytes"], 2 * 1024 * 1024)) < 2 * 1024 * 1024
    assert receipt["chart_model_bytes"] == strict_b64encode(real_builder_serializer(model))


def test_generated_receipt_passes_standalone_external_validation() -> None:
    model, receipt = build_ranking_chart_model(success_envelope())

    assert validate_chart_model_build_receipt(receipt, chart_model=model) == receipt


@pytest.mark.parametrize(
    ("attribute", "lower_error"),
    [
        ("canonical_json_bytes", CanonicalJsonError("LOWER-SECRET")),
        ("truncate_title_dimension", RenderTextError("LOWER-SECRET")),
    ],
)
def test_builder_translates_post_binding_failures_without_context(
    monkeypatch: pytest.MonkeyPatch,
    attribute: str,
    lower_error: Exception,
) -> None:
    from patent_analysis import chart_model

    def fail(*_args: object, **_kwargs: object) -> None:
        raise lower_error

    monkeypatch.setattr(chart_model, attribute, fail)
    with pytest.raises(RenderContractError) as caught:
        build_ranking_chart_model(success_envelope())

    _assert_safe_error(caught.value, "LOWER-SECRET")


@pytest.mark.parametrize("row_count", [True, False, -1, 102, 1.0, "1", None])
def test_render_spec_builder_rejects_invalid_row_count(row_count: object) -> None:
    with pytest.raises(RenderContractError):
        build_ranking_render_spec(row_count=row_count)  # type: ignore[arg-type]
