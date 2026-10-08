from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from patent_analysis.column_resolution import resolve_roles
from patent_analysis.dataset_v2 import read_dataset_v2


def _dataset_and_resolution(tmp_path: Path):
    source = tmp_path / "input.csv"
    source.write_text(
        "出願人,IPC,出願日,分類外\n"
        '"PANASONIC IP MANAGEMENT CO., LTD.","A01G-009/00, A01G-031/00",2024-03-02,"A,B;C"\n'
        '株式会社花王,"A61K 8/00; A61K 8/34; A61Q 19/00",2022/01/01,"C;D"\n'
        ',G06F 3/00,不明,""\n',
        encoding="utf-8",
    )
    dataset = read_dataset_v2(source.name, allowed_root=tmp_path)
    resolution = resolve_roles(
        dataset.manifest,
        {
            "profile": None,
            "bindings": {
                "applicant": "出願人",
                "classification": "IPC",
                "filing_date": "出願日",
                "ordinary": "分類外",
            },
        },
        required_roles=(
            "applicant",
            "classification",
            "filing_date",
            "ordinary",
        ),
    )
    return dataset, resolution


def test_normalize_dataset_uses_the_public_config_and_immutable_row_contract(
    tmp_path: Path,
) -> None:
    from patent_analysis.normalization import (
        NormalizationConfig,
        NormalizedRow,
        normalize_dataset,
    )

    dataset, resolution = _dataset_and_resolution(tmp_path)
    config = NormalizationConfig(
        roles=("applicant", "classification", "filing_date", "ordinary"),
        multi_value_policy="all",
        classification_levels={"classification": "subclass"},
    )

    normalized = normalize_dataset(dataset, resolution, config)

    first = normalized.rows[0]
    assert isinstance(first, NormalizedRow)
    assert first.source_ordinal == 1
    assert first.source_fields == dataset.rows[0].values
    assert first.values_by_role == {
        "applicant": ("PANASONIC IP MANAGEMENT",),
        "classification": ("A01G",),
        "filing_date": ("2024",),
        "ordinary": ("A,B", "C"),
    }
    assert first.values("classification") == ("A01G",)
    with pytest.raises(TypeError):
        first.values_by_role["applicant"] = ("mutated",)  # type: ignore[index]
    assert normalized.receipt.requested_roles == config.roles
    assert len(normalized.receipt.normalized_row_stream_sha256) == 64


def test_patent_multi_value_semantics_preserve_applicant_commas() -> None:
    from patent_analysis.normalization import split_patent_values

    assert split_patent_values("A社,B社", role="applicant") == ("A社,B社",)
    assert split_patent_values("A社；B社|C社", role="applicant") == (
        "A社",
        "B社",
        "C社",
    )
    assert split_patent_values(
        "A01G-009/00, A01G-031/00, A01G-031/00",
        role="IPC",
    ) == ("A01G-009/00", "A01G-031/00")


def test_classification_projection_is_canonical_and_stably_deduplicated() -> None:
    from patent_analysis.normalization import derive_classification_values

    values = ("Ａ６１Ｋ８／００", "A61K 8/34", "A61Q 19/00", "A61K 8/00")
    assert derive_classification_values(values, level="class") == ("A61",)
    assert derive_classification_values(values, level="subclass") == (
        "A61K",
        "A61Q",
    )
    assert derive_classification_values(values, level="main_group") == (
        "A61K 8/00",
        "A61Q 19/00",
    )
    assert derive_classification_values(("A01G-031/00",), level="subgroup") == (
        "A01G 31/00",
    )


def test_applicant_and_year_normalization_port_pinned_source_expectations() -> None:
    from patent_analysis.normalization import extract_year, normalize_applicant

    assert normalize_applicant("株式会社花王") == "花王"
    assert normalize_applicant("花王（株）") == "花王"
    assert normalize_applicant("ＳＨＩＳＥＩＤＯ　ＣＯ．，　ＬＴＤ．") == "SHISEIDO"
    assert normalize_applicant("BASF SE") == "BASF"
    assert normalize_applicant("SE Research Inc.") == "SE Research"
    assert extract_year("2021-03-04") == "2021"
    assert extract_year("平成30年") == ""


def test_normalization_config_and_public_schema_are_closed() -> None:
    from patent_analysis.api import get_public_schema
    from patent_analysis.normalization import NormalizationConfig, NormalizationError

    schema = get_public_schema("normalization-v1.schema.json")
    assert schema["$id"] == "urn:patent-analysis:normalization:1.0.0"
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    valid = {
        "roles": ["applicant", "classification"],
        "multi_value_policy": "all",
        "classification_levels": {"classification": "subclass"},
    }
    assert not list(validator.iter_errors(valid))
    assert list(validator.iter_errors({**valid, "source_product_mode": "workbench"}))

    config = NormalizationConfig(
        roles=("applicant",),
        classification_levels={},
    )
    assert json.loads(json.dumps(config.to_dict())) == {
        "classification_levels": {},
        "multi_value_policy": "all",
        "roles": ["applicant"],
    }
    with pytest.raises(NormalizationError):
        NormalizationConfig(roles=("applicant", "applicant"))
    with pytest.raises(NormalizationError):
        NormalizationConfig(
            roles=("applicant",),
            classification_levels={"classification": "subclass"},
        )


def test_normalization_aggregates_reject_mutable_direct_inputs() -> None:
    from patent_analysis.normalization import (
        NormalizationError,
        NormalizationReceipt,
        NormalizedDataset,
        NormalizedRow,
    )

    row = NormalizedRow(
        source_ordinal=1,
        source_fields=("A社",),
        values_by_role={"applicant": ("A社",)},
    )
    receipt_arguments = {
        "normalization_contract_version": "1.0.0",
        "source_input_sha256": "1" * 64,
        "resolved_role_mapping_sha256": "2" * 64,
        "multi_value_policy": "all",
        "classification_levels": {},
        "input_rows": 1,
        "output_rows": 1,
        "normalized_contributions": 1,
        "normalized_row_stream_sha256": "3" * 64,
    }
    with pytest.raises(NormalizationError, match="receipt"):
        NormalizationReceipt(
            requested_roles=["applicant"],  # type: ignore[arg-type]
            **receipt_arguments,
        )

    receipt = NormalizationReceipt(
        requested_roles=("applicant",),
        **receipt_arguments,
    )
    with pytest.raises(NormalizationError, match="dataset"):
        NormalizedDataset(
            rows=[row],  # type: ignore[arg-type]
            receipt=receipt,
        )
