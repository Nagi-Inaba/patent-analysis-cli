from __future__ import annotations

from copy import deepcopy

import pytest

from patent_analysis.analysis_contracts import StrictDraft202012Validator
from patent_analysis.chart_models._common import load_schema
from tests.test_task6_categorical_rendering import COMPOSITION_RESULT, TIMELINE_RESULT


def test_shared_measure_contract_rejects_irrelevant_count_role_and_noncanonical_rows() -> None:
    from patent_analysis.analyses._aggregation import row_values, validate_measure

    with pytest.raises(ValueError, match="not allowed"):
        validate_measure({"measure": "count", "measure_role": "score"})
    with pytest.raises(ValueError, match="canonically normalized"):
        row_values({"applicant": ["A社"]}, "applicant")  # type: ignore[arg-type]


def test_task6_parameter_schemas_reject_measure_role_for_count() -> None:
    for name in ("timeline", "composition"):
        schema = load_schema(f"{name}-parameters-v1.schema.json")
        parameters = schema["$defs"]["parameters"]
        validator = StrictDraft202012Validator(parameters)
        payload = {
            "measure": "count",
            "measure_role": "score",
        }
        if name == "timeline":
            payload.update({"date_role": "year", "series_role": "applicant"})
        else:
            payload.update({"role": "applicant"})
        assert list(validator.iter_errors(payload))


def test_series_chart_model_rejects_semantically_inconsistent_series() -> None:
    from patent_analysis.chart_models.series import build_series_chart_model

    duplicate = deepcopy(TIMELINE_RESULT)
    duplicate["data"]["series"].append(deepcopy(duplicate["data"]["series"][0]))
    with pytest.raises(ValueError, match="semantics"):
        build_series_chart_model(duplicate, mark="series-line-svg.v1")

    bad_population = deepcopy(TIMELINE_RESULT)
    bad_population["population"] = {"input_rows": 3, "analyzed_rows": 2, "excluded_rows": 0}
    with pytest.raises(ValueError):
        build_series_chart_model(bad_population, mark="series-line-svg.v1")


def test_composition_chart_model_rejects_bad_share_semantics() -> None:
    from patent_analysis.chart_models.composition import build_composition_chart_model

    wrong_share = deepcopy(COMPOSITION_RESULT)
    wrong_share["data"]["items"][0]["share"] = 0.5
    with pytest.raises(ValueError, match="shares"):
        build_composition_chart_model(wrong_share, mark="composition-pie-svg.v1")

    wrong_basis = deepcopy(COMPOSITION_RESULT)
    wrong_basis["data"]["items"][0]["share_basis"] = "value"
    with pytest.raises(ValueError, match="basis"):
        build_composition_chart_model(wrong_basis, mark="composition-pie-svg.v1")


def test_task6_registry_final_integration_allows_categorical_mcp_exposure() -> None:
    from patent_analysis.analysis_registry import get_analysis_definition

    assert get_analysis_definition("timeline.v1").mcp_public is True
    assert get_analysis_definition("composition.v1").mcp_public is True
