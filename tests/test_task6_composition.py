from __future__ import annotations

from types import MappingProxyType

import pytest

from patent_analysis.normalization import NormalizedRow
from patent_analysis.population import PopulationReceipt, PopulationResult


def _row(ordinal: int, **roles: tuple[str, ...]) -> NormalizedRow:
    return NormalizedRow(
        source_ordinal=ordinal,
        source_fields=tuple(value for values in roles.values() for value in values),
        values_by_role=MappingProxyType(dict(roles)),
    )


def _population(*rows: NormalizedRow) -> PopulationResult:
    return PopulationResult(
        rows=tuple(rows),
        receipt=PopulationReceipt(
            population_contract_version="1.0.0",
            normalization_row_stream_sha256="a" * 64,
            population_spec_sha256="b" * 64,
            family_mode="records",
            filter_count=0,
            input_rows=len(rows),
            included_rows=len(rows),
            filtered_rows=0,
        ),
    )


def test_composition_count_uses_value_share_and_recomputes_other_by_source_row() -> None:
    from patent_analysis.analyses.composition import analyze_composition

    population = _population(
        _row(1, applicant=("A社", "B社")),
        _row(2, applicant=("A社",)),
        _row(3, applicant=("C社", "D社")),
        _row(4, applicant=()),
    )

    result = analyze_composition(
        population,
        {
            "role": "applicant",
            "top_n": 1,
            "include_other": True,
            "measure": "count",
        },
    )

    assert result["items"] == [
        {
            "label": "A社",
            "value": 2,
            "row_count": 2,
            "share": pytest.approx(0.5),
            "share_basis": "value",
            "is_other": False,
        },
        {
            "label": "その他（上位外）",
            "value": 2,
            "row_count": 2,
            "share": pytest.approx(0.5),
            "share_basis": "value",
            "is_other": True,
        },
    ]
    assert result["population"] == {
        "input_rows": 4,
        "visible_rows": 3,
        "blank_role_rows": 1,
        "excluded_rows": 1,
    }
    assert result["contributions"] == 5


def test_composition_nonnegative_sum_uses_value_share() -> None:
    from patent_analysis.analyses.composition import analyze_composition

    result = analyze_composition(
        _population(
            _row(1, applicant=("A",), score=("10",)),
            _row(2, applicant=("B",), score=("30",)),
        ),
        {
            "role": "applicant",
            "top_n": 10,
            "include_other": False,
            "measure": "sum",
            "measure_role": "score",
        },
    )

    assert [item["label"] for item in result["items"]] == ["B", "A"]
    assert [item["share_basis"] for item in result["items"]] == ["value", "value"]
    assert [item["share"] for item in result["items"]] == [
        pytest.approx(0.75),
        pytest.approx(0.25),
    ]


def test_composition_negative_additive_value_falls_back_to_row_count_share() -> None:
    from patent_analysis.analyses.composition import analyze_composition

    result = analyze_composition(
        _population(
            _row(1, applicant=("A",), score=("10",)),
            _row(2, applicant=("B",), score=("-2",)),
            _row(3, applicant=("B",), score=("-3",)),
        ),
        {
            "role": "applicant",
            "top_n": 10,
            "include_other": False,
            "measure": "sum",
            "measure_role": "score",
        },
    )

    assert [item["label"] for item in result["items"]] == ["A", "B"]
    assert [item["value"] for item in result["items"]] == [10, -5]
    assert [item["share_basis"] for item in result["items"]] == [
        "row_count",
        "row_count",
    ]
    assert [item["share"] for item in result["items"]] == [
        pytest.approx(1 / 3),
        pytest.approx(2 / 3),
    ]


@pytest.mark.parametrize("mode", ["average", "max", "min"])
def test_composition_nonadditive_measures_use_row_count_share(mode: str) -> None:
    from patent_analysis.analyses.composition import analyze_composition

    result = analyze_composition(
        _population(
            _row(1, applicant=("A",), score=("10",)),
            _row(2, applicant=("B",), score=("20",)),
            _row(3, applicant=("B",), score=("30",)),
        ),
        {
            "role": "applicant",
            "top_n": 10,
            "include_other": False,
            "measure": mode,
            "measure_role": "score",
        },
    )

    assert all(item["share_basis"] == "row_count" for item in result["items"])
    shares = {item["label"]: item["share"] for item in result["items"]}
    assert shares == {"A": pytest.approx(1 / 3), "B": pytest.approx(2 / 3)}


def test_composition_all_zero_additive_weights_do_not_invent_equal_share() -> None:
    from patent_analysis.analyses.composition import analyze_composition

    result = analyze_composition(
        _population(
            _row(1, applicant=("A",), score=("0",)),
            _row(2, applicant=("B",), score=("0",)),
        ),
        {
            "role": "applicant",
            "top_n": 10,
            "include_other": False,
            "measure": "sum",
            "measure_role": "score",
        },
    )

    assert [item["share_basis"] for item in result["items"]] == ["value", "value"]
    assert [item["share"] for item in result["items"]] == [0.0, 0.0]


def test_composition_required_roles_are_analysis_owned() -> None:
    from patent_analysis.analyses.composition import required_roles

    assert required_roles({"role": "applicant", "measure": "count"}) == (
        "applicant",
    )
    assert required_roles(
        {"role": "applicant", "measure": "sum", "measure_role": "score"}
    ) == ("applicant", "score")


def test_composition_contribution_guard_fails_before_excess_increment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import patent_analysis.analyses.composition as composition

    monkeypatch.setattr(composition, "MAX_EXPANDED_CONTRIBUTIONS", 2)
    population = _population(
        _row(1, applicant=("A", "B")),
        _row(2, applicant=("C",)),
    )

    with pytest.raises(composition.CompositionBudgetError, match="contributions"):
        composition.analyze_composition(
            population,
            {
                "role": "applicant",
                "top_n": 10,
                "include_other": True,
                "measure": "count",
            },
        )
