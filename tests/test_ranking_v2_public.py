import json
from copy import deepcopy

import pytest

from patent_analysis import api
from patent_analysis._render_contracts import RenderContractError
from patent_analysis.chart_model import build_ranking_chart_model


def test_ranking_v2_public_analysis_table_and_chart_bind_selected_population(tmp_path):
    spec = {
        "analysis_contract_version": "2.0.0", "analysis_id": "ranking.v2",
        "resolution": {"bindings": {"group": "group", "family": "family", "date": "date"}},
        "normalization": {"profiles": []},
        "population": {"filters": [], "selection_sets": [], "family_mode": "earliest",
                       "family_role": "family", "date_role": "date"},
        "parameters": {"role": "group"},
    }
    (tmp_path / "data.csv").write_text(
        "group,family,date\nA|B,F,2020-01-01\nC,F,2021-01-01\nA,G,2022-01-01\n",
        encoding="utf-8",
    )
    raw = json.dumps(spec).encode()
    document = api.run_analysis("data.csv", raw, allowed_root=tmp_path)
    assert document["population"] == {"input_rows": 3, "analyzed_rows": 2, "excluded_rows": 1}
    assert document["data"]["population"] == {"input_rows": 2, "analyzed_rows": 3}
    assert document["data"]["rows"][0]["value"] == 2
    table = api.run_analysis_table("data.csv", raw, allowed_root=tmp_path)
    assert "ranking.v2,rows,dimension_value,A,2,2," in table
    model, receipt = build_ranking_chart_model(document)
    assert model["rows"][0]["value"] == 2
    assert receipt["analysis_result_sha256"] == model["analysis_result_sha256"]
    different_source_count = deepcopy(document)
    different_source_count["population"].update(input_rows=4, excluded_rows=2)
    assert build_ranking_chart_model(different_source_count)[1] != receipt
    inconsistent = deepcopy(document)
    inconsistent["data"]["population"]["input_rows"] = 1
    with pytest.raises(RenderContractError):
        build_ranking_chart_model(inconsistent)
