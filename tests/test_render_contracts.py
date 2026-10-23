from __future__ import annotations

import json
from collections import defaultdict
from copy import deepcopy
from importlib.resources import files

import pytest

from patent_analysis._render_canonical import (
    canonical_json_bytes,
    sha256_bytes,
    strict_b64encode,
)
from patent_analysis._render_contracts import (
    RenderContractError,
    get_chart_model_build_receipt_schema,
    get_chart_model_schema,
    get_label_overlay_pack_schema,
    get_render_spec_schema,
    validate_chart_model,
    validate_chart_model_build_receipt,
    validate_label_overlay_pack,
    validate_render_spec,
)

REQUIRED_REQUIREMENT_IDS = {
    "overlay.top.closed-required-version-hash",
    "overlay.dimension.source-display-description-limits",
    "overlay.producer-id-version-pattern",
    "overlay.selection-policy-pattern",
    "overlay.rows-count-index-kind",
    "overlay.row-source-display-description-limits",
    "overlay.provenance-review-enums-pattern",
    "overlay.evidence-count-item-limits",
    "overlay.evidence-arrays-independent",
    "chart.top.closed-required-version-type-hashes",
    "chart.title-256-257",
    "chart.dimension-limits-null",
    "chart.measure-count-null-noncount-column",
    "chart.population-independent-bounds",
    "chart.rows-0-101-index-order",
    "chart.row-count-1-500000-share-0-1",
    "chart.row-kind-semantic-label",
    "chart.remainder-unique-last-other",
    "chart.count-each-and-sum-lte-analyzed",
    "chart.count-sum-may-be-less-than-analyzed",
    "chart.analyzed-zero-iff-empty-rows",
    "chart.warning-count-and-item-limits",
    "chart.decoded-string-2000000",
    "chart.display-text-20000-graphemes",
    "chart.safe-text-forbidden-codepoints",
    "receipt.closed-required-version-builder",
    "receipt-strict-base64-2mib",
    "receipt-hash-model-row-count-binding",
    "spec.closed-required-fixed-values",
    "spec-height-row-count-formula",
    "spec-canonical-bytes-16kib-pixel-limit",
    "binding-result-hash-dimension-complete-rows",
    "binding-no-normalization-1-vs-1point0",
}

BINDING_REQUIREMENT_IDS = {
    "binding-result-hash-dimension-complete-rows",
    "binding-no-normalization-1-vs-1point0",
}

EXPECTED_CORPUS_CASE_NAMES = {
    "binding-distinguishes-one-and-one-point-zero",
    "binding-exact-string-valid",
    "binding-nonsequential-overlay-index-invalid",
    "binding-result-complete-valid",
    "binding-result-hash-invalid",
    "chart-analysis-hash-pattern-invalid",
    "chart-count-sum-bound-invalid",
    "chart-count-sum-bound-valid",
    "chart-count-sum-less-invalid",
    "chart-count-sum-less-valid",
    "chart-decoded-string-budget-invalid",
    "chart-decoded-string-budget-valid",
    "chart-dimension-description-4097-invalid",
    "chart-dimension-description-type-invalid",
    "chart-dimension-display_label-4097-invalid",
    "chart-dimension-display_label-empty-invalid",
    "chart-dimension-display_label-null-invalid",
    "chart-dimension-display_label-type-invalid",
    "chart-dimension-limits-invalid",
    "chart-dimension-limits-valid",
    "chart-dimension-missing-description-invalid",
    "chart-dimension-missing-display_label-invalid",
    "chart-dimension-missing-source_label-invalid",
    "chart-dimension-source_label-4097-invalid",
    "chart-dimension-source_label-empty-invalid",
    "chart-dimension-source_label-null-invalid",
    "chart-dimension-source_label-type-invalid",
    "chart-dimension-unknown-sibling-invalid",
    "chart-display-text-budget-invalid",
    "chart-display-text-budget-valid",
    "chart-empty-population-invalid",
    "chart-empty-population-valid",
    "chart-measure-count-column-string-invalid",
    "chart-measure-count-null-invalid",
    "chart-measure-count-null-valid",
    "chart-measure-missing-column-invalid",
    "chart-measure-missing-mode-invalid",
    "chart-measure-mode-enum-invalid",
    "chart-measure-mode-null-invalid",
    "chart-measure-mode-type-invalid",
    "chart-measure-sum-column-4097-invalid",
    "chart-measure-sum-column-empty-invalid",
    "chart-measure-sum-column-valid",
    "chart-measure-unknown-sibling-invalid",
    "chart-overlay-hash-pattern-invalid",
    "chart-population-analyzed-500001-invalid",
    "chart-population-analyzed_rows-bool-invalid",
    "chart-population-analyzed_rows-minus-one-invalid",
    "chart-population-analyzed_rows-type-invalid",
    "chart-population-independent-invalid",
    "chart-population-independent-valid",
    "chart-population-input-100001-invalid",
    "chart-population-input-greater-valid",
    "chart-population-input_rows-bool-invalid",
    "chart-population-input_rows-minus-one-invalid",
    "chart-population-input_rows-type-invalid",
    "chart-population-missing-analyzed_rows-invalid",
    "chart-population-missing-input_rows-invalid",
    "chart-population-unknown-sibling-invalid",
    "chart-remainder-duplicate-invalid",
    "chart-remainder-last-other-invalid",
    "chart-remainder-last-other-valid",
    "chart-remainder-source-invalid",
    "chart-row-count-500001-invalid",
    "chart-row-count-bool-invalid",
    "chart-row-count-share-invalid",
    "chart-row-count-share-valid",
    "chart-row-index-101-invalid",
    "chart-row-index-bool-invalid",
    "chart-row-index-minus-one-invalid",
    "chart-row-index-order-invalid",
    "chart-row-index-order-valid",
    "chart-row-kind-enum-invalid",
    "chart-row-missing-count-invalid",
    "chart-row-missing-row_kind-invalid",
    "chart-row-missing-semantic_label-invalid",
    "chart-row-missing-share-invalid",
    "chart-row-missing-value-invalid",
    "chart-row-row_kind-null-invalid",
    "chart-row-row_kind-type-invalid",
    "chart-row-semantic-enum-invalid",
    "chart-row-semantic-invalid",
    "chart-row-semantic-valid",
    "chart-row-semantic_label-null-invalid",
    "chart-row-semantic_label-type-invalid",
    "chart-row-share-bool-invalid",
    "chart-row-share-minus-invalid",
    "chart-row-share-plus-invalid",
    "chart-row-value-bool-invalid",
    "chart-row-value-nonfinite-invalid",
    "chart-rows-101-valid",
    "chart-rows-102-invalid",
    "chart-rows-null-invalid",
    "chart-rows-type-invalid",
    "chart-safe-text-invalid",
    "chart-safe-text-valid",
    "chart-title-256-valid",
    "chart-title-257-invalid",
    "chart-title-empty-invalid",
    "chart-title-null-invalid",
    "chart-title-policy-invalid",
    "chart-title-policy-valid",
    "chart-title-type-invalid",
    "chart-top-contract-invalid",
    "chart-top-contract-valid",
    "chart-top-missing-analysis_result_sha256-invalid",
    "chart-top-missing-chart_model_contract_version-invalid",
    "chart-top-missing-chart_type-invalid",
    "chart-top-missing-dimension-invalid",
    "chart-top-missing-label_overlay_sha256-invalid",
    "chart-top-missing-measure-invalid",
    "chart-top-missing-population-invalid",
    "chart-top-missing-rows-invalid",
    "chart-top-missing-title-invalid",
    "chart-top-missing-warnings-invalid",
    "chart-top-unknown-sibling-invalid",
    "chart-type-const-invalid",
    "chart-warning-count-invalid",
    "chart-warning-count-valid",
    "chart-warning-item-4097-invalid",
    "chart-warning-item-type-invalid",
    "chart-warning-type-invalid",
    "overlay-dimension-256-graphemes-valid",
    "overlay-dimension-description-257-graphemes-invalid",
    "overlay-dimension-description-type-invalid",
    "overlay-dimension-display_label-257-graphemes-invalid",
    "overlay-dimension-display_label-empty-invalid",
    "overlay-dimension-display_label-null-invalid",
    "overlay-dimension-display_label-type-invalid",
    "overlay-dimension-limits-invalid",
    "overlay-dimension-limits-valid",
    "overlay-dimension-missing-description-invalid",
    "overlay-dimension-missing-display_label-invalid",
    "overlay-dimension-missing-source_label-invalid",
    "overlay-dimension-source_label-257-graphemes-invalid",
    "overlay-dimension-source_label-empty-invalid",
    "overlay-dimension-source_label-null-invalid",
    "overlay-dimension-source_label-type-invalid",
    "overlay-dimension-unknown-sibling-invalid",
    "overlay-evidence-16-valid",
    "overlay-evidence-arrays-independent-invalid",
    "overlay-evidence-arrays-independent-valid",
    "overlay-evidence-id-257-invalid",
    "overlay-evidence-id-empty-invalid",
    "overlay-evidence-id-null-invalid",
    "overlay-evidence-id-type-invalid",
    "overlay-evidence-limits-invalid",
    "overlay-evidence-limits-valid",
    "overlay-evidence-sha-17-invalid",
    "overlay-evidence-sha-null-invalid",
    "overlay-evidence-sha-pattern-invalid",
    "overlay-evidence-sha-type-invalid",
    "overlay-evidence_ids-null-invalid",
    "overlay-evidence_ids-type-invalid",
    "overlay-evidence_sha256-null-invalid",
    "overlay-evidence_sha256-type-invalid",
    "overlay-hash-null-invalid",
    "overlay-hash-pattern-invalid",
    "overlay-hash-type-invalid",
    "overlay-nonsequential-index-section7-invalid",
    "overlay-nonsequential-index-section7-valid",
    "overlay-producer-128-valid",
    "overlay-producer-id-129-invalid",
    "overlay-producer-id-null-invalid",
    "overlay-producer-id-pattern-invalid",
    "overlay-producer-id-type-invalid",
    "overlay-producer-missing-id-invalid",
    "overlay-producer-missing-version-invalid",
    "overlay-producer-pattern-invalid",
    "overlay-producer-pattern-valid",
    "overlay-producer-unknown-sibling-invalid",
    "overlay-producer-version-129-invalid",
    "overlay-producer-version-null-invalid",
    "overlay-producer-version-pattern-invalid",
    "overlay-producer-version-type-invalid",
    "overlay-provenance-review-invalid",
    "overlay-provenance-review-valid",
    "overlay-review-64-valid",
    "overlay-review-65-invalid",
    "overlay-review-pattern-invalid",
    "overlay-row-description-257-graphemes-invalid",
    "overlay-row-description-type-invalid",
    "overlay-row-display-257-graphemes-invalid",
    "overlay-row-display_label-empty-invalid",
    "overlay-row-display_label-null-invalid",
    "overlay-row-display_label-type-invalid",
    "overlay-row-index-100-valid",
    "overlay-row-index-101-invalid",
    "overlay-row-index-bool-invalid",
    "overlay-row-index-minus-one-invalid",
    "overlay-row-index-type-invalid",
    "overlay-row-index-zero-valid",
    "overlay-row-kind-enum-invalid",
    "overlay-row-kind-null-invalid",
    "overlay-row-kind-type-invalid",
    "overlay-row-missing-description-invalid",
    "overlay-row-missing-display_label-invalid",
    "overlay-row-missing-evidence_ids-invalid",
    "overlay-row-missing-evidence_sha256-invalid",
    "overlay-row-missing-index-invalid",
    "overlay-row-missing-provenance_state-invalid",
    "overlay-row-missing-review_state-invalid",
    "overlay-row-missing-row_kind-invalid",
    "overlay-row-missing-source_label-invalid",
    "overlay-row-provenance_state-null-invalid",
    "overlay-row-provenance_state-type-invalid",
    "overlay-row-review_state-null-invalid",
    "overlay-row-review_state-type-invalid",
    "overlay-row-source_label-empty-invalid",
    "overlay-row-source_label-null-invalid",
    "overlay-row-source_label-type-invalid",
    "overlay-row-text-limits-invalid",
    "overlay-row-text-limits-valid",
    "overlay-row-text-maximum-valid",
    "overlay-row-unknown-sibling-invalid",
    "overlay-rows-101-valid",
    "overlay-rows-102-invalid",
    "overlay-rows-missing-invalid",
    "overlay-rows-null-invalid",
    "overlay-rows-type-invalid",
    "overlay-selection-policy-128-valid",
    "overlay-selection-policy-129-invalid",
    "overlay-selection-policy-invalid",
    "overlay-selection-policy-leading-hyphen-invalid",
    "overlay-selection-policy-null-invalid",
    "overlay-selection-policy-type-invalid",
    "overlay-selection-policy-valid",
    "overlay-top-missing-analysis_result_sha256-invalid",
    "overlay-top-missing-dimension-invalid",
    "overlay-top-missing-label_overlay_contract_version-invalid",
    "overlay-top-missing-producer-invalid",
    "overlay-top-missing-selection_policy_id-invalid",
    "overlay-top-unknown-sibling-invalid",
    "overlay-top-version-hash-invalid",
    "overlay-top-version-hash-valid",
    "overlay-version-null-invalid",
    "overlay-version-type-invalid",
    "receipt-analysis-hash-binding-invalid",
    "receipt-base64-null-invalid",
    "receipt-base64-padding-invalid",
    "receipt-base64-type-invalid",
    "receipt-builder-id-invalid",
    "receipt-builder-version-65-invalid",
    "receipt-builder-version-null-invalid",
    "receipt-builder-version-pattern-invalid",
    "receipt-builder-version-type-invalid",
    "receipt-closed-builder-invalid",
    "receipt-closed-builder-valid",
    "receipt-missing-analysis_result_sha256-invalid",
    "receipt-missing-builder_id-invalid",
    "receipt-missing-builder_version-invalid",
    "receipt-missing-chart_model_build_receipt_version-invalid",
    "receipt-missing-chart_model_bytes-invalid",
    "receipt-missing-chart_model_sha256-invalid",
    "receipt-missing-label_overlay_sha256-invalid",
    "receipt-missing-row_count-invalid",
    "receipt-model-binding-invalid",
    "receipt-model-binding-valid",
    "receipt-overlay-hash-binding-invalid",
    "receipt-row-count-102-invalid",
    "receipt-row-count-binding-invalid",
    "receipt-row-count-bool-invalid",
    "receipt-row-count-minus-one-invalid",
    "receipt-strict-base64-invalid",
    "receipt-strict-base64-valid",
    "receipt-unknown-sibling-invalid",
    "spec-animation-const-invalid",
    "spec-axis_label_max_graphemes-const-invalid",
    "spec-canonical-bytes-over-16kib-invalid",
    "spec-echarts_version-const-invalid",
    "spec-fixed-values-invalid",
    "spec-fixed-values-valid",
    "spec-font_family-const-invalid",
    "spec-height-4097-invalid",
    "spec-height-674-invalid",
    "spec-height-675-valid",
    "spec-height-bool-invalid",
    "spec-height-formula-invalid",
    "spec-height-formula-valid",
    "spec-height-type-invalid",
    "spec-missing-animation-invalid",
    "spec-missing-axis_label_max_graphemes-invalid",
    "spec-missing-echarts_version-invalid",
    "spec-missing-font_family-invalid",
    "spec-missing-height-invalid",
    "spec-missing-locale-invalid",
    "spec-missing-render_profile_id-invalid",
    "spec-missing-render_spec_contract_version-invalid",
    "spec-missing-renderer_kind-invalid",
    "spec-missing-timezone-invalid",
    "spec-missing-width-invalid",
    "spec-pixel-limit-invalid",
    "spec-pixel-limit-valid",
    "spec-render_profile_id-const-invalid",
    "spec-renderer_kind-const-invalid",
    "spec-timezone-const-invalid",
    "spec-unknown-sibling-invalid",
    "spec-width-const-invalid",
    "chart-analysis-hash-null-invalid",
    "chart-analysis-hash-type-invalid",
    "chart-label-overlay-hash-string-valid",
    "chart-overlay-hash-type-invalid",
    "chart-row-description-257-invalid",
    "chart-row-description-4097-invalid",
    "chart-row-description-type-invalid",
    "chart-row-display-257-invalid",
    "chart-row-display-empty-invalid",
    "chart-row-display-null-invalid",
    "chart-row-display-type-invalid",
    "chart-row-missing-description-invalid",
    "chart-row-missing-display-label-invalid",
    "chart-row-missing-index-invalid",
    "chart-row-missing-source-label-invalid",
    "chart-row-source-4097-invalid",
    "chart-row-source-empty-invalid",
    "chart-row-source-null-invalid",
    "chart-row-source-type-invalid",
    "chart-row-unknown-sibling-invalid",
    "overlay-dimension-description-empty-valid",
    "overlay-evidence-id-256-valid",
    "receipt-analysis-hash-null-invalid",
    "receipt-analysis-hash-pattern-invalid",
    "receipt-analysis-hash-type-invalid",
    "receipt-builder-version-64-valid",
    "receipt-chart-hash-null-invalid",
    "receipt-chart-hash-pattern-invalid",
    "receipt-chart-hash-type-invalid",
    "receipt-label-overlay-hash-string-valid",
    "receipt-overlay-hash-type-invalid",
    "receipt-row-count-null-invalid",
    "receipt-row-count-type-invalid",
}

REQUIRED_ADDITIONAL_SCALAR_CASE_NAMES = {
    "binding-nonsequential-overlay-index-invalid",
    "chart-analysis-hash-null-invalid",
    "chart-analysis-hash-type-invalid",
    "chart-label-overlay-hash-string-valid",
    "chart-overlay-hash-type-invalid",
    "chart-row-description-257-invalid",
    "chart-row-description-4097-invalid",
    "chart-row-description-type-invalid",
    "chart-row-display-257-invalid",
    "chart-row-display-empty-invalid",
    "chart-row-display-null-invalid",
    "chart-row-display-type-invalid",
    "chart-row-missing-description-invalid",
    "chart-row-missing-display-label-invalid",
    "chart-row-missing-index-invalid",
    "chart-row-missing-source-label-invalid",
    "chart-row-source-4097-invalid",
    "chart-row-source-empty-invalid",
    "chart-row-source-null-invalid",
    "chart-row-source-type-invalid",
    "chart-row-unknown-sibling-invalid",
    "overlay-dimension-description-empty-valid",
    "overlay-evidence-id-256-valid",
    "receipt-analysis-hash-null-invalid",
    "receipt-analysis-hash-pattern-invalid",
    "receipt-analysis-hash-type-invalid",
    "receipt-builder-version-64-valid",
    "receipt-chart-hash-null-invalid",
    "receipt-chart-hash-pattern-invalid",
    "receipt-chart-hash-type-invalid",
    "receipt-label-overlay-hash-string-valid",
    "receipt-overlay-hash-type-invalid",
    "receipt-row-count-null-invalid",
    "receipt-row-count-type-invalid",
}


@pytest.fixture
def valid_overlay() -> dict[str, object]:
    return {
        "label_overlay_contract_version": "1.0.0",
        "analysis_result_sha256": "a" * 64,
        "dimension": {
            "source_label": "出願人",
            "display_label": "出願人",
            "description": None,
        },
        "producer": {"id": "external-workflow", "version": "1.0.0"},
        "selection_policy_id": "identity.v1",
        "rows": [],
    }


@pytest.fixture
def valid_chart_model() -> dict[str, object]:
    return {
        "chart_model_contract_version": "1.0.0",
        "chart_type": "ranking.horizontal_bar",
        "analysis_result_sha256": "a" * 64,
        "label_overlay_sha256": None,
        "title": "出願人のランキング",
        "dimension": {
            "source_label": "出願人",
            "display_label": "出願人",
            "description": None,
        },
        "measure": {"mode": "count", "column": None},
        "population": {"input_rows": 1, "analyzed_rows": 1},
        "rows": [
            {
                "index": 0,
                "row_kind": "dimension_value",
                "source_label": "A社",
                "display_label": "A社",
                "description": None,
                "semantic_label": "データ中の分類値",
                "value": 1,
                "count": 1,
                "share": 1,
            }
        ],
        "warnings": [],
    }


@pytest.fixture
def valid_render_spec() -> dict[str, object]:
    return {
        "render_spec_contract_version": "1.0.0",
        "renderer_kind": "ranking.horizontal_bar.svg",
        "locale": "ja-JP",
        "timezone": "UTC",
        "width": 1200,
        "height": 675,
        "font_family": "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif",
        "animation": False,
        "axis_label_max_graphemes": 28,
        "echarts_version": "6.1.0",
        "render_profile_id": "ranking-svg-ja-jp-node24-echarts6.v1",
    }


def _valid_receipt(model: dict[str, object]) -> dict[str, object]:
    raw = canonical_json_bytes(model)
    return {
        "chart_model_build_receipt_version": "1.0.0",
        "analysis_result_sha256": model["analysis_result_sha256"],
        "label_overlay_sha256": model["label_overlay_sha256"],
        "chart_model_sha256": sha256_bytes(raw),
        "chart_model_bytes": strict_b64encode(raw),
        "row_count": len(model["rows"]),
        "builder_id": "patent-analysis.ranking-chart-model-builder",
        "builder_version": "0.2.0",
    }


def test_render_schema_ids_and_closed_objects_are_exact() -> None:
    assert get_label_overlay_pack_schema()["$id"] == (
        "urn:patent-analysis:label-overlay-pack:1.0.0"
    )
    assert get_chart_model_schema()["$id"] == "urn:patent-analysis:chart-model:1.0.0"
    assert get_chart_model_build_receipt_schema()["$id"] == (
        "urn:patent-analysis:chart-model-build-receipt:1.0.0"
    )
    assert get_render_spec_schema()["$id"] == "urn:patent-analysis:render-spec:1.0.0"
    assert get_chart_model_schema()["additionalProperties"] is False
    assert get_chart_model_schema()["properties"]["dimension"]["additionalProperties"] is False
    assert get_chart_model_schema()["properties"]["rows"]["items"]["additionalProperties"] is False


def test_render_contract_error_never_echoes_secret_input() -> None:
    secret = "CLIENT-SECRET-LABEL"
    with pytest.raises(RenderContractError) as caught:
        validate_label_overlay_pack({"secret": secret})
    error = caught.value
    assert error.code == "render.contract_invalid"
    assert error.safe_message == "Render contract is invalid"
    assert error.retryable is False
    assert error.details == {}
    assert error.__cause__ is None
    assert error.__context__ is None
    assert error.__suppress_context__ is True
    assert secret not in str(error)
    assert secret not in repr(error.__dict__)
    assert secret not in repr(error.as_dict())


def test_render_contract_error_ignores_caller_fields() -> None:
    error = RenderContractError(
        message="SECRET", code="secret", retryable=True, details={"x": "SECRET"}
    )
    assert error.as_dict() == {
        "code": "render.contract_invalid",
        "safe_message": "Render contract is invalid",
        "retryable": False,
        "details": {},
    }


def test_copy_failure_is_translated_without_retaining_lower_exception(
    valid_overlay: dict[str, object],
) -> None:
    secret = "SECRET-DEEPCOPY-FAILURE"

    class FailingCopyDict(dict):
        def __deepcopy__(self, memo):
            del memo
            raise ValueError(secret)

    with pytest.raises(RenderContractError) as caught:
        validate_label_overlay_pack(FailingCopyDict(valid_overlay))
    assert caught.value.__context__ is None
    assert caught.value.__cause__ is None
    assert secret not in repr(caught.value.__dict__)


def test_validators_return_defensive_copies(
    valid_overlay: dict[str, object],
    valid_chart_model: dict[str, object],
    valid_render_spec: dict[str, object],
) -> None:
    for source, validated in (
        (valid_overlay, validate_label_overlay_pack(valid_overlay)),
        (valid_chart_model, validate_chart_model(valid_chart_model)),
        (valid_render_spec, validate_render_spec(valid_render_spec)),
    ):
        assert validated == source
        assert validated is not source
    receipt = _valid_receipt(valid_chart_model)
    validated_receipt = validate_chart_model_build_receipt(receipt, chart_model=valid_chart_model)
    assert validated_receipt == receipt
    assert validated_receipt is not receipt


@pytest.mark.parametrize(
    ("mutator"),
    [
        lambda value: value.pop("chart_type"),
        lambda value: value.__setitem__("unknown", True),
        lambda value: value.__setitem__("chart_model_contract_version", "2.0.0"),
        lambda value: value.__setitem__("label_overlay_sha256", "not-a-hash"),
        lambda value: value["population"].__setitem__("analyzed_rows", True),
        lambda value: value["rows"][0].__setitem__("value", float("nan")),
        lambda value: value["rows"][0].__setitem__("value", -0.0),
        lambda value: value["rows"][0].__setitem__("count", 0),
        lambda value: value["rows"][0].__setitem__("share", 1.01),
        lambda value: value["rows"][0].__setitem__("semantic_label", "wrong"),
        lambda value: value["rows"][0].__setitem__("display_label", "unsafe\ntext"),
        lambda value: value["rows"][0].__setitem__("display_label", "あ" * 257),
        lambda value: value.__setitem__("title", "wrong title"),
    ],
)
def test_chart_model_rejects_invalid_scalar_and_semantic_values_without_mutation(
    valid_chart_model: dict[str, object], mutator
) -> None:
    invalid = deepcopy(valid_chart_model)
    mutator(invalid)
    before = deepcopy(invalid)
    with pytest.raises(RenderContractError):
        validate_chart_model(invalid)
    assert invalid == before


def test_chart_model_remainder_and_count_rules(valid_chart_model: dict[str, object]) -> None:
    remainder = deepcopy(valid_chart_model["rows"][0])
    remainder.update(
        {
            "index": 1,
            "row_kind": "remainder",
            "source_label": "その他",
            "display_label": "その他",
            "semantic_label": "上位表示外の合計",
        }
    )
    valid_chart_model["population"]["analyzed_rows"] = 1
    valid_chart_model["rows"].append(remainder)
    with pytest.raises(RenderContractError):
        validate_chart_model(valid_chart_model)

    invalid_order = deepcopy(valid_chart_model)
    invalid_order["population"]["analyzed_rows"] = 2
    invalid_order["rows"].reverse()
    with pytest.raises(RenderContractError):
        validate_chart_model(invalid_order)


def test_chart_model_empty_population_and_independent_population_are_valid(
    valid_chart_model: dict[str, object],
) -> None:
    empty = deepcopy(valid_chart_model)
    empty["population"] = {"input_rows": 0, "analyzed_rows": 0}
    empty["rows"] = []
    assert validate_chart_model(empty) == empty

    fewer_input = deepcopy(valid_chart_model)
    fewer_input["population"] = {"input_rows": 1, "analyzed_rows": 2}
    assert validate_chart_model(fewer_input) == fewer_input

    more_input = deepcopy(valid_chart_model)
    more_input["population"] = {"input_rows": 2, "analyzed_rows": 1}
    assert validate_chart_model(more_input) == more_input


def test_chart_model_row_warning_and_title_boundaries(
    valid_chart_model: dict[str, object],
) -> None:
    row = valid_chart_model["rows"][0]
    valid_chart_model["rows"] = [
        {**deepcopy(row), "index": index, "source_label": str(index), "display_label": str(index)}
        for index in range(101)
    ]
    valid_chart_model["population"] = {"input_rows": 101, "analyzed_rows": 101}
    valid_chart_model["warnings"] = [""] * 32
    assert validate_chart_model(valid_chart_model) == valid_chart_model

    too_many_rows = deepcopy(valid_chart_model)
    too_many_rows["rows"].append({**deepcopy(row), "index": 101})
    with pytest.raises(RenderContractError):
        validate_chart_model(too_many_rows)

    too_many_warnings = deepcopy(valid_chart_model)
    too_many_warnings["warnings"].append("")
    with pytest.raises(RenderContractError):
        validate_chart_model(too_many_warnings)

    title_256 = deepcopy(valid_chart_model)
    title_256["dimension"]["display_label"] = "あ" * 250
    title_256["title"] = "あ" * 250 + "のランキング"
    assert validate_chart_model(title_256) == title_256

    truncated_title = deepcopy(valid_chart_model)
    truncated_title["dimension"]["display_label"] = "あ" * 251
    truncated_title["title"] = "あ" * 249 + "…のランキング"
    assert validate_chart_model(truncated_title) == truncated_title


def test_chart_title_keeps_full_bounded_dimension_code_points(
    valid_chart_model: dict[str, object],
) -> None:
    display_label = "a" + "\u0301" * 3847 + "b" * 248
    assert len(display_label) == 4096
    valid_chart_model["dimension"]["display_label"] = display_label
    valid_chart_model["title"] = display_label + "のランキング"
    assert validate_chart_model(valid_chart_model) == valid_chart_model


def test_chart_model_rejects_display_budget_above_20000_graphemes(
    valid_chart_model: dict[str, object],
) -> None:
    row = valid_chart_model["rows"][0]
    valid_chart_model["rows"] = [
        {
            **deepcopy(row),
            "index": index,
            "source_label": "s" * 100,
            "display_label": "d" * 100,
        }
        for index in range(101)
    ]
    valid_chart_model["population"] = {"input_rows": 101, "analyzed_rows": 101}
    with pytest.raises(RenderContractError):
        validate_chart_model(valid_chart_model)


def test_overlay_allows_nonsequential_index_section_7_controls_and_unequal_evidence(
    valid_overlay: dict[str, object],
) -> None:
    valid_overlay["rows"] = [
        {
            "index": 100,
            "row_kind": "dimension_value",
            "source_label": "source\nlabel",
            "display_label": "display\nlabel",
            "description": None,
            "provenance_state": "manual",
            "review_state": "reviewed",
            "evidence_ids": ["evidence\n1"],
            "evidence_sha256": [],
        }
    ]
    assert validate_label_overlay_pack(valid_overlay) == valid_overlay


def test_bounded_tree_rejects_cycle_depth_nonstring_keys_and_string_budget(
    valid_overlay: dict[str, object],
) -> None:
    cyclic = deepcopy(valid_overlay)
    cyclic["cycle"] = cyclic
    too_deep: object = "leaf"
    for _ in range(65):
        too_deep = [too_deep]

    for invalid in (cyclic, {1: "value"}, too_deep, {"value": "x" * 2_000_001}):
        with pytest.raises(RenderContractError):
            validate_label_overlay_pack(invalid)


def test_receipt_validates_strict_bytes_hash_model_and_row_count(
    valid_chart_model: dict[str, object],
) -> None:
    receipt = _valid_receipt(valid_chart_model)
    assert validate_chart_model_build_receipt(receipt, chart_model=valid_chart_model) == receipt

    for field, value in (
        ("chart_model_bytes", receipt["chart_model_bytes"] + "\n"),
        ("chart_model_sha256", "0" * 64),
        ("analysis_result_sha256", "0" * 64),
        ("row_count", 0),
    ):
        invalid = deepcopy(receipt)
        invalid[field] = value
        with pytest.raises(RenderContractError):
            validate_chart_model_build_receipt(invalid, chart_model=valid_chart_model)


def test_receipt_rejects_semver_numeric_prerelease_with_leading_zero(
    valid_chart_model: dict[str, object],
) -> None:
    receipt = _valid_receipt(valid_chart_model)
    receipt["builder_version"] = "0.2.0-01"
    with pytest.raises(RenderContractError):
        validate_chart_model_build_receipt(receipt)


def test_receipt_rejects_decoded_bytes_above_two_mib(
    valid_chart_model: dict[str, object],
) -> None:
    receipt = _valid_receipt(valid_chart_model)
    receipt["chart_model_bytes"] = strict_b64encode(b"x" * (2 * 1024 * 1024 + 1))
    with pytest.raises(RenderContractError):
        validate_chart_model_build_receipt(receipt)


def test_receipt_model_binding_distinguishes_integer_and_float_values(
    valid_chart_model: dict[str, object],
) -> None:
    receipt = _valid_receipt(valid_chart_model)
    supplied_model = deepcopy(valid_chart_model)
    supplied_model["rows"][0]["value"] = 1.0
    assert receipt["chart_model_bytes"] != strict_b64encode(canonical_json_bytes(supplied_model))
    with pytest.raises(RenderContractError):
        validate_chart_model_build_receipt(receipt, chart_model=supplied_model)


@pytest.mark.parametrize(
    ("row_count", "height"),
    [(None, 675), (None, 700), (None, 3796), (0, 675), (14, 675), (15, 700), (101, 3796)],
)
def test_render_spec_accepts_standalone_and_bound_heights(
    valid_render_spec: dict[str, object], row_count: int | None, height: int
) -> None:
    valid_render_spec["height"] = height
    assert validate_render_spec(valid_render_spec, row_count=row_count) == valid_render_spec


@pytest.mark.parametrize(
    ("row_count", "height"),
    [(None, 676), (0, 700), (15, 675), (101, 3760), (True, 675), (-1, 675), (102, 675)],
)
def test_render_spec_rejects_invalid_height_or_explicit_row_count(
    valid_render_spec: dict[str, object], row_count: int | None, height: int
) -> None:
    valid_render_spec["height"] = height
    with pytest.raises(RenderContractError):
        validate_render_spec(valid_render_spec, row_count=row_count)


def test_contract_corpus_wrapper_requirements_and_standalone_dispatch() -> None:
    corpus = json.loads(
        files("patent_analysis")
        .joinpath("schemas", "render-contract-cases.json")
        .read_text(encoding="utf-8")
    )
    assert set(corpus) == {"corpus_version", "cases"}
    assert corpus["corpus_version"] == "1.0.0"
    assert {case["name"] for case in corpus["cases"]} == EXPECTED_CORPUS_CASE_NAMES
    assert len(corpus["cases"]) == len(EXPECTED_CORPUS_CASE_NAMES)
    assert REQUIRED_ADDITIONAL_SCALAR_CASE_NAMES <= EXPECTED_CORPUS_CASE_NAMES
    assert {requirement for case in corpus["cases"] for requirement in case["requirements"]} == (
        REQUIRED_REQUIREMENT_IDS
    )

    validators = {
        "label_overlay_pack": validate_label_overlay_pack,
        "chart_model": validate_chart_model,
        "chart_model_build_receipt": validate_chart_model_build_receipt,
        "render_spec": validate_render_spec,
    }
    dispatched_case_names: set[str] = set()
    requirement_polarity: dict[str, set[bool]] = defaultdict(set)
    executed_requirement_cases: dict[str, set[str]] = defaultdict(set)
    for case in corpus["cases"]:
        assert len(case["requirements"]) == 1
        requirement = case["requirements"][0]
        requirement_polarity[requirement].add(case["valid"])
        if case["contract"] == "chart_input_binding":
            assert set(case) == {
                "name",
                "contract",
                "valid",
                "analyze_success_envelope",
                "overlay",
                "requirements",
            }
            continue
        assert set(case) == {"name", "contract", "valid", "value", "requirements"}
        validator = validators[case["contract"]]
        if case["valid"]:
            validator(case["value"])
        else:
            with pytest.raises(RenderContractError):
                validator(case["value"])
        dispatched_case_names.add(case["name"])
        executed_requirement_cases[requirement].add(case["name"])

    expected_standalone_names = {
        case["name"] for case in corpus["cases"] if case["contract"] != "chart_input_binding"
    }
    assert dispatched_case_names == expected_standalone_names
    assert all(executed_requirement_cases[requirement] for requirement in (
        REQUIRED_REQUIREMENT_IDS - BINDING_REQUIREMENT_IDS
    ))
    assert all(requirement_polarity[requirement] == {False, True} for requirement in (
        REQUIRED_REQUIREMENT_IDS
    ))
