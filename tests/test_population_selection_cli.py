from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from patent_analysis import AnalysisContractError, api, cli

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
CSV = ("year,group,x,y,family,filed\n"
       "2020,A,X,U,F,2020-01-01\n"
       "2021,A,X,V,F,2021-01-01\n"
       "2021,B,Y,U,G,2021-01-01\n"
       ",A,Z,V,H,2021-01-01\n"
       "²²²²,A,X,U,I,2021-01-01\n"
       "2022,A;B,Y,V,J,2022-01-01\n"
       "2019,C,Z,U,K,2019-01-01\n").encode()


def _spec(name="composition"):
    spec = json.loads((EXAMPLES / "basic" / f"{name}.json").read_bytes())
    spec["resolution"]["bindings"].update(year="year", group="group")
    return spec


def _selection(mode="include"):
    return {"dimension_role": "group", "mode": mode, "values": ["A"],
            "source_date_role": "year", "start_year": 2021, "end_year": 2022}


@pytest.mark.parametrize("case,expected", [
    ("year", {"A": 1, "B": 1}),
    ("outside", {"A": 3, "B": 1, "C": 1}),
    ("outside-exclude", {"A": 2, "B": 1}),
    ("selection", {"A": 2, "B": 1}),
    ("selection-exclude", {"A": 3, "B": 1, "C": 1}),
    ("and-family", {"A": 1}),
])
def test_population_filters_api_and_cli_golden(case, expected, tmp_path, monkeypatch, capsys):
    source = tmp_path / "input.csv"
    source.write_bytes(CSV)
    spec = _spec()
    population = spec["population"]
    if case == "year":
        population["filters"] = [{"role": "year", "effect": "include",
                                  "match": "year", "value": 2021}]
    elif case.startswith("outside"):
        population["filters"] = [{"role": "year", "effect": "exclude" if
                                  case.endswith("exclude") else "include",
                                  "match": "outside_year_range",
                                  "start_year": 2020, "end_year": 2021}]
    else:
        population["selection_sets"] = [_selection("exclude" if
                                                   case.endswith("exclude") else "include")]
        if case == "and-family":
            population["selection_sets"].append(
                {"dimension_role": "y", "mode": "exclude", "values": ["U"]})
            population["filters"] = [{"role": "year", "effect": "exclude",
                                      "match": "year", "value": 2022}]
            population.update(family_mode="earliest", family_role="family", date_role="filed")
            spec["resolution"]["bindings"].update(y="y", family="family", filed="filed")
    raw = json.dumps(spec).encode()
    assert api.validate_analysis_spec_bytes(raw)["valid"]
    result = api.run_analysis_csv(source, raw, allowed_root=tmp_path)
    assert {item["label"]: item["value"] for item in result["data"]["items"]} == expected
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))
    monkeypatch.setattr(sys, "stdin", StringIO(raw.decode()))
    assert cli.main(["analyze", "input.csv", "--spec", "-", "--json"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out)["data"] == result["data"]
    assert source.read_bytes() == CSV


@pytest.mark.parametrize("case", ["missing-date-binding", "reversed", "too-many",
                                  "too-many-values", "padded-role", "too-many-roles"])
def test_invalid_selection_is_rejected_before_file_read(case, tmp_path):
    spec = _spec()
    selection = _selection()
    spec["population"]["selection_sets"] = [selection]
    if case == "missing-date-binding":
        del spec["resolution"]["bindings"]["year"]
    elif case == "reversed":
        selection["end_year"] = 2020
    elif case == "too-many":
        spec["population"]["filters"] = [
            {"role": "group", "effect": "include", "match": "exact", "value": "A"}
        ] * 64
    elif case == "too-many-values":
        selection["values"] = [str(i) for i in range(1001)]
    elif case == "too-many-roles":
        spec["population"]["selection_sets"] = [
            {"dimension_role": f"role{i}", "mode": "include", "values": ["A"]}
            for i in range(64)]
        spec["resolution"]["bindings"].update({f"role{i}": f"column{i}" for i in range(64)})
    else:
        selection["source_date_role"] = " year "
    raw = json.dumps(spec).encode()
    with pytest.raises(AnalysisContractError):
        api.validate_analysis_spec_bytes(raw)
    with pytest.raises(AnalysisContractError):
        api.run_analysis_csv("missing.csv", raw, allowed_root=tmp_path)
    if case == "too-many-roles":
        spec["population"]["selection_sets"].pop()
        raw = json.dumps(spec).encode()
        assert api.validate_analysis_spec_bytes(raw)["valid"]
        source = tmp_path / "limit.csv"
        source.write_text("group," + ",".join(f"column{i}" for i in range(63))
                          + "\n" + ",".join(["A"] * 64) + "\n", encoding="utf-8")
        result = api.run_analysis_csv(source, raw, allowed_root=tmp_path)
        assert result["data"]["items"][0]["value"] == 1


def test_selection_matrix_real_stdio_and_public_api(tmp_path):
    input_root = tmp_path / "inputs"
    output_root = tmp_path / "outputs"
    input_root.mkdir()
    output_root.mkdir()
    (input_root / "input.csv").write_bytes(CSV)
    spec = _spec("matrix")
    spec["population"]["selection_sets"] = [_selection()]
    raw = json.dumps(spec).encode()
    result = api.run_analysis_csv("input.csv", raw, allowed_root=input_root)
    assert {(cell["x_label"], cell["y_label"]): cell["value"]
            for cell in result["data"]["cells"]} == {("X", "V"): 1, ("Y", "V"): 1}
    params = StdioServerParameters(command=sys.executable,
        args=["-m", "patent_analysis_mcp.server", "--input-root", f"input={input_root}",
              "--output-root", f"output={output_root}"])

    async def scenario():
        with anyio.fail_after(60):
            async with stdio_client(params) as streams:
                async with ClientSession(*streams) as session:
                    await session.initialize()
                    validated = await session.call_tool(
                        "patent_analysis.validate_spec", {"spec": spec})
                    assert not validated.is_error
                    analyzed = await session.call_tool("patent_analysis.analyze",
                        {"input_root_id": "input", "path": "input.csv", "spec": spec})
                    assert not analyzed.is_error
                    content = analyzed.structured_content["content"]
                    assert content["data"] == result["data"]
                    assert str(tmp_path) not in repr(content)
    anyio.run(scenario)
