from __future__ import annotations

from pathlib import Path

import pytest

from patent_analysis.column_resolution import resolve_roles
from patent_analysis.dataset_v2 import read_dataset_v2


def _dataset(tmp_path: Path):
    source = tmp_path / "input.csv"
    source.write_text(
        "出願人,IPC,出願日,分類外\n"
        '"株式会社 ＡＢＣ Co., Ltd.","H01L 21/00,H01L 23/00",2024-03-02,"A,B;C"\n'
        'ABC株式会社,"H01L 21/00;G06F 3/00",2022/01/01,"C;D"\n'
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


def _catalog_dataset(tmp_path: Path):
    source = tmp_path / "catalog.csv"
    source.write_text(
        "出願日,Main IPC\n"
        '2024-03-02,"A01G 9/00,A01G 31/00"\n'
        "2022/01/01,G06F 3/00\n",
        encoding="utf-8",
    )
    dataset = read_dataset_v2(source.name, allowed_root=tmp_path)
    resolution = resolve_roles(
        dataset.manifest,
        {"profile": "column-alias.v2"},
        required_roles=("date", "main_ipc"),
    )
    assert resolution.mapping["date"].raw_header == "出願日"
    assert resolution.mapping["main_ipc"].raw_header == "Main IPC"
    return dataset, resolution


def test_pipeline_normalizes_without_source_product_mode(tmp_path: Path) -> None:
    from patent_analysis.normalization import NormalizationConfig, normalize_dataset

    dataset, resolution = _dataset(tmp_path)
    normalized = normalize_dataset(
        dataset,
        resolution,
        NormalizationConfig(
            roles=("applicant", "classification", "filing_date", "ordinary"),
            multi_value_policy="all",
            classification_levels={"classification": "subclass"},
        ),
    )
    first = normalized.rows[0]
    assert first.values("applicant") == ("ABC",)
    assert first.values("classification") == ("H01L",)
    assert first.values("filing_date") == ("2024",)
    assert first.values("ordinary") == ("A,B", "C")
    assert normalized.receipt.input_rows == 3
    assert normalized.receipt.output_rows == 3
    assert len(normalized.receipt.normalized_row_stream_sha256) == 64


def test_catalog_date_role_supports_year_population(tmp_path: Path) -> None:
    from patent_analysis.normalization import NormalizationConfig, normalize_dataset
    from patent_analysis.population import apply_population

    dataset, resolution = _catalog_dataset(tmp_path)
    normalized = normalize_dataset(
        dataset,
        resolution,
        NormalizationConfig(roles=("date",)),
    )

    assert normalized.rows[0].values("date") == ("2024",)
    selected = apply_population(
        normalized,
        {
            "filters": [
                {
                    "role": "date",
                    "match": "year_range",
                    "start": 2024,
                    "end": 2024,
                }
            ],
            "family_mode": "records",
        },
    )
    assert tuple(row.source_ordinal for row in selected.rows) == (1,)


def test_catalog_main_ipc_role_uses_classification_semantics(tmp_path: Path) -> None:
    from patent_analysis.normalization import NormalizationConfig, normalize_dataset

    dataset, resolution = _catalog_dataset(tmp_path)
    normalized = normalize_dataset(
        dataset,
        resolution,
        NormalizationConfig(roles=("main_ipc",)),
    )

    assert normalized.rows[0].values("main_ipc") == (
        "A01G 9/00",
        "A01G 31/00",
    )


def test_first_policy_and_stable_dedupe_are_deterministic(tmp_path: Path) -> None:
    from patent_analysis.normalization import NormalizationConfig, normalize_dataset

    dataset, resolution = _dataset(tmp_path)
    config = NormalizationConfig(
        roles=("classification",),
        multi_value_policy="first",
        classification_levels={"classification": "subclass"},
    )
    left = normalize_dataset(dataset, resolution, config)
    right = normalize_dataset(dataset, resolution, config)
    assert left.rows[0].values("classification") == ("H01L",)
    assert left.to_dict() == right.to_dict()
    assert (
        left.receipt.normalized_row_stream_sha256
        == right.receipt.normalized_row_stream_sha256
    )


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        ("full", "H01L 21/13"),
        ("class", "H01"),
        ("subclass", "H01L"),
        ("main_group", "H01L 21/00"),
        ("subgroup", "H01L 21/13"),
    ],
)
def test_classification_levels_are_generic(level: str, expected: str) -> None:
    from patent_analysis.normalization.classification import format_classification

    assert format_classification(" h01l21/13 ", level) == expected


def test_applicant_normalization_is_conservative_and_dictionary_free() -> None:
    from patent_analysis.normalization.applicant import normalize_applicant

    assert normalize_applicant("株式会社 ＡＢＣ Co., Ltd.") == "ABC"
    assert normalize_applicant("合同会社テスト") == "テスト"
    assert normalize_applicant("株式会社") == "株式会社"


def test_resolution_from_another_dataset_is_rejected(tmp_path: Path) -> None:
    from patent_analysis.normalization import (
        NormalizationConfig,
        NormalizationError,
        normalize_dataset,
    )

    dataset, resolution = _dataset(tmp_path)
    other_path = tmp_path / "other.csv"
    other_path.write_text(
        "出願人,IPC,出願日,分類外\nX,H01L,2020,Z\n",
        encoding="utf-8",
    )
    other = read_dataset_v2(other_path.name, allowed_root=tmp_path)
    with pytest.raises(NormalizationError, match="dataset binding"):
        normalize_dataset(
            other,
            resolution,
            NormalizationConfig(roles=("applicant",)),
        )
    assert dataset.manifest.source_input_sha256 != other.manifest.source_input_sha256


def test_normalization_limit_and_limit_plus_one_are_literal(tmp_path: Path) -> None:
    from patent_analysis.normalization import (
        MAX_NORMALIZED_VALUES_PER_CELL,
        NormalizationConfig,
        NormalizationError,
        normalize_dataset,
    )

    source = tmp_path / "limits.csv"
    at_limit = ";".join(f"V{i}" for i in range(MAX_NORMALIZED_VALUES_PER_CELL))
    source.write_text(f"項目\n{at_limit}\n", encoding="utf-8")
    dataset = read_dataset_v2(source.name, allowed_root=tmp_path)
    resolution = resolve_roles(
        dataset.manifest,
        {"profile": None, "bindings": {"value": "項目"}},
        required_roles=("value",),
    )
    config = NormalizationConfig(roles=("value",))
    result = normalize_dataset(dataset, resolution, config)
    assert len(result.rows[0].values("value")) == MAX_NORMALIZED_VALUES_PER_CELL

    over = tmp_path / "over.csv"
    over.write_text(f"項目\n{at_limit};overflow\n", encoding="utf-8")
    over_dataset = read_dataset_v2(over.name, allowed_root=tmp_path)
    over_resolution = resolve_roles(
        over_dataset.manifest,
        {"profile": None, "bindings": {"value": "項目"}},
        required_roles=("value",),
    )
    with pytest.raises(NormalizationError, match="value limit"):
        normalize_dataset(over_dataset, over_resolution, config)


def test_population_filters_are_anded_and_preserve_source_order(
    tmp_path: Path,
) -> None:
    from patent_analysis.normalization import NormalizationConfig, normalize_dataset
    from patent_analysis.population import apply_population

    dataset, resolution = _dataset(tmp_path)
    normalized = normalize_dataset(
        dataset,
        resolution,
        NormalizationConfig(
            roles=("applicant", "classification", "filing_date"),
            classification_levels={"classification": "subclass"},
        ),
    )
    selected = apply_population(
        normalized,
        {
            "filters": [
                {
                    "role": "classification",
                    "match": "one_of",
                    "values": ["H01L"],
                },
                {
                    "role": "filing_date",
                    "match": "year_range",
                    "start": 2023,
                    "end": 2025,
                },
            ],
            "family_mode": "records",
        },
    )
    assert [row.source_ordinal for row in selected.rows] == [1]
    assert selected.receipt.input_rows == 3
    assert selected.receipt.included_rows == 1
    assert selected.receipt.filtered_rows == 2


def test_population_exclude_and_unsupported_match_fail_closed(
    tmp_path: Path,
) -> None:
    from patent_analysis.normalization import NormalizationConfig, normalize_dataset
    from patent_analysis.population import PopulationError, apply_population

    dataset, resolution = _dataset(tmp_path)
    normalized = normalize_dataset(
        dataset,
        resolution,
        NormalizationConfig(roles=("applicant",)),
    )
    selected = apply_population(
        normalized,
        {
            "filters": [
                {
                    "role": "applicant",
                    "match": "exact",
                    "value": "ABC",
                    "exclude": True,
                }
            ],
            "family_mode": "records",
        },
    )
    assert [row.source_ordinal for row in selected.rows] == [3]
    with pytest.raises(PopulationError, match="unsupported filter"):
        apply_population(
            normalized,
            {
                "filters": [
                    {
                        "role": "applicant",
                        "match": "contains",
                        "value": "A",
                    }
                ],
                "family_mode": "records",
            },
        )
