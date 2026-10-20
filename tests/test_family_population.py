"""Representative selection occurs once before analysis eligibility checks."""

from __future__ import annotations

import csv
import io
import json
from copy import deepcopy
from pathlib import Path

import pytest

from patent_analysis import api, cli
from patent_analysis.analysis_contracts import AnalysisContractError
from patent_analysis.canonical_v2 import canonical_json_bytes
from patent_analysis.normalization import NormalizationReceipt, NormalizedDataset, NormalizedRow
from patent_analysis.population import apply_population
from patent_analysis.v2_contracts import validate_analysis_result_v2

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "advanced"
NATIVE_PARAMETERS = {
    "matrix.v1": {"x_role": "x", "y_role": "y"},
    "timeline.v1": {"date_role": "year", "series_role": "group"},
    "composition.v1": {"role": "group"},
    "growth.v1": {
        "date_role": "year",
        "series_role": "group",
        "start_year": 2020,
        "end_year": 2024,
    },
    "concentration.v1": {"date_role": "year", "category_role": "group"},
    "lifecycle.v1": {"date_role": "year", "category_role": "group"},
}
ADVANCED_IDS = (
    "growth-quadrant.v1",
    "entry-exit.v1",
    "citation.v1",
    "matrix-composition.v1",
    "new-entrants.v1",
    "compara.v1",
    "cooccurrence.v1",
    "collaboration-network.v1",
    "uniqueness.v1",
    "shared-involvement.v1",
)
RECORDS = {"filters": [], "selection_sets": [], "family_mode": "records"}
EARLIEST = {
    **RECORDS,
    "family_mode": "earliest",
    "family_role": "family_id",
    "date_role": "filing_date",
}


def _spec(analysis_id: str = "composition.v1") -> dict:
    if analysis_id in NATIVE_PARAMETERS:
        spec = {
            "analysis_contract_version": "2.0.0",
            "analysis_id": analysis_id,
            "resolution": {"bindings": {name: name for name in ("year", "group", "x", "y")}},
            "normalization": {"profiles": []},
            "population": deepcopy(RECORDS),
            "parameters": deepcopy(NATIVE_PARAMETERS[analysis_id]),
        }
    else:
        spec = json.loads((EXAMPLES / f"{analysis_id[:-3]}.json").read_text(encoding="utf-8"))
    spec["resolution"]["bindings"].update({"family_id": "family", "filing_date": "filed"})
    return spec


def _csv(rows: list[list[str]]) -> bytes:
    out = io.StringIO(newline="")
    csv.writer(out, lineterminator="\n").writerows(rows)
    return out.getvalue().encode("utf-8")


def _dataset(rows: tuple[tuple[str, str, str], ...]) -> NormalizedDataset:
    normalized = tuple(
        NormalizedRow(i, row, {"group": (row[2],) if row[2] else ()})
        for i, row in enumerate(rows, 1)
    )
    return NormalizedDataset(
        normalized,
        NormalizationReceipt(
            "1.0.0",
            "1" * 64,
            "2" * 64,
            ("group",),
            "all",
            {},
            len(rows),
            len(rows),
            len(rows),
            "3" * 64,
        ),
    )


def test_opaque_ids_dates_blanks_and_first_seen_family_order() -> None:
    dataset = _dataset(
        (
            (" F;1 ", "2020-12-31", "late"),
            ("F;1", "2020/01/01", "early"),
            ("", "2010-01-01", "blank-one"),
            (" ", "2010-01-01", "blank-two"),
            ("F", "2010-01-01", "different-id"),
            ("invalid", "2020-02-30", "invalid-first"),
            ("invalid", "2020-03-01", "valid-later"),
            ("tie", "2020-04-01", "tie-first"),
            ("tie", "2020/04/01", "tie-second"),
            ("unknown", "", "unknown-first"),
            ("unknown", "2020", "unknown-second"),
            ("blank-first", "", "blank-date-first"),
            ("blank-first", "2020-01-01", "valid-later"),
            ("invalid-later", "2020-01-01", "valid-first"),
            ("invalid-later", "not-a-date", "invalid-second"),
        )
    )
    before = dataset.to_dict()
    result = apply_population(
        dataset,
        {
            "filters": [],
            "family_mode": "earliest",
            "family_role": "family_id",
            "date_role": "filing_date",
        },
        source_role_ordinals={"family_id": 0, "filing_date": 1},
    )
    assert tuple(row.source_ordinal for row in result.rows) == (2, 3, 4, 5, 6, 8, 10, 12, 14)
    receipt = result.receipt.analysis_metadata()["family_selection"]
    assert receipt["matched_rows"] == 15
    assert receipt["representative_rows"] == 9 and receipt["collapsed_rows"] == 6
    assert receipt["unidentified_rows"] == 2
    assert dataset.to_dict() == before


def test_filters_precede_selection_and_blanks_are_not_replaced_by_later_members(tmp_path):
    # The earliest F member is outside the declared filter. The earliest G
    # member survives the filter but has a blank category, so G remains excluded.
    rows = [
        ["family", "filed", "group", "year", "x", "y"],
        ["F", "2018-01-01", "outside", "2018", "X", "Y"],
        ["F", "2020-09-01", "kept", "2020", "X", "Y"],
        ["G", "2020-10-01", "must-not-win", "2020", "X", "Y"],
        ["G", "2020-01-01", "", "2020", "X", "Y"],
    ]
    (tmp_path / "input.csv").write_bytes(_csv(rows))
    spec = _spec()
    spec["resolution"]["bindings"]["year"] = "filed"
    spec["population"] = {
        **EARLIEST,
        "date_role": "year",
        "filters": [
            {
                "role": "year",
                "effect": "include",
                "match": "year_range",
                "start_year": 2020,
                "end_year": 2020,
            }
        ],
    }
    result = api.run_analysis_csv("input.csv", canonical_json_bytes(spec), allowed_root=tmp_path)
    assert result["population"] == {"input_rows": 4, "analyzed_rows": 1, "excluded_rows": 3}
    assert result["family_selection"]["matched_rows"] == 3
    assert result["family_selection"]["representative_rows"] == 2
    assert "kept" in repr(result["data"]) and "must-not-win" not in repr(result["data"])


@pytest.mark.parametrize("analysis_id", (*NATIVE_PARAMETERS, *ADVANCED_IDS))
def test_native_analyses_equal_manual_representatives_without_changing_records(
    analysis_id, tmp_path
):
    original_rows = list(
        csv.reader(io.StringIO((EXAMPLES / "patents.csv").read_text(encoding="utf-8")))
    )
    header, *data = original_rows
    family = ["F1", "F1", "F2", "F2", "F3", "F3", "F4", "", "", ""]
    rows = [header + ["family", "filed"]] + [
        row + [family[i], "2020-01-01" if i % 2 else "2020-12-31"] for i, row in enumerate(data)
    ]
    chosen = [1, 3, 5, 6, 7, 8, 9]
    full = _csv(rows)
    (tmp_path / "input.csv").write_bytes(full)
    (tmp_path / "chosen.csv").write_bytes(_csv([rows[0], *(rows[i + 1] for i in chosen)]))
    spec = _spec(analysis_id)
    records_spec = deepcopy(spec)
    if analysis_id == "matrix.v1":
        records_spec["resolution"]["bindings"] = {"x": "x", "y": "y"}
        spec["resolution"]["bindings"] = {
            **records_spec["resolution"]["bindings"],
            "family_id": "family",
            "filing_date": "filed",
        }
    before = api.run_analysis_csv(
        "input.csv", canonical_json_bytes(records_spec), allowed_root=tmp_path
    )
    expected = api.run_analysis_csv(
        "chosen.csv", canonical_json_bytes(records_spec), allowed_root=tmp_path
    )
    selected_spec = {**spec, "population": deepcopy(EARLIEST)}
    selected = api.run_analysis_csv(
        "input.csv",
        canonical_json_bytes(selected_spec),
        allowed_root=tmp_path,
    )
    assert selected["data"] == expected["data"]
    assert selected["family_selection"] == {
        "algorithm_version": "1.0.0",
        "mode": "earliest",
        "family_role": "family_id",
        "date_role": "filing_date",
        "matched_rows": 10,
        "representative_rows": 7,
        "collapsed_rows": 3,
        "unidentified_rows": 3,
    }
    assert validate_analysis_result_v2(selected) == selected
    if analysis_id in ADVANCED_IDS:
        from patent_analysis.chart_models.advanced import build_advanced_chart_model

        model, _ = build_advanced_chart_model(selected, analysis_id=analysis_id)
        assert model["population"] == selected["population"]
    assert "family_selection" not in before
    after = api.run_analysis_csv(
        "input.csv", canonical_json_bytes(records_spec), allowed_root=tmp_path
    )
    assert canonical_json_bytes(after) == canonical_json_bytes(before)
    assert (tmp_path / "input.csv").read_bytes() == full


def test_missing_date_role_uses_first_member_and_empty_input_stays_empty(tmp_path):
    spec = _spec()
    spec["population"] = {k: v for k, v in EARLIEST.items() if k != "date_role"}
    rows = [
        ["family", "filed", "group", "year", "x", "y"],
        ["F", "2022-01-01", "first", "2022", "X", "Y"],
        ["F", "2020-01-01", "second", "2020", "X", "Y"],
    ]
    (tmp_path / "input.csv").write_bytes(_csv(rows))
    first = api.run_analysis_csv("input.csv", canonical_json_bytes(spec), allowed_root=tmp_path)
    assert "first" in repr(first["data"]) and "second" not in repr(first["data"])
    (tmp_path / "empty.csv").write_bytes(_csv(rows[:1]))
    empty = api.run_analysis_csv("empty.csv", canonical_json_bytes(spec), allowed_root=tmp_path)
    assert empty["family_selection"]["representative_rows"] == 0
    assert empty["family_selection"]["date_role"] is None


@pytest.mark.parametrize(
    "population",
    [
        {**RECORDS, "family_mode": "earliest"},
        {**EARLIEST, "family_role": ""},
        {**EARLIEST, "family_role": " family_id"},
        {**EARLIEST, "date_role": ""},
        {**EARLIEST, "date_role": "filing_date "},
        {**RECORDS, "family_role": "family_id"},
        {**EARLIEST, "infer_family": True},
    ],
)
def test_family_spec_is_closed_before_csv_access(population):
    spec = {**_spec(), "population": population}
    with pytest.raises(AnalysisContractError):
        api.run_analysis_csv("not-present.csv", canonical_json_bytes(spec), allowed_root=EXAMPLES)


def test_missing_family_column_is_rejected_instead_of_treating_every_row_as_unidentified(tmp_path):
    from patent_analysis import DatasetInputError

    (tmp_path / "input.csv").write_text(
        "group,year,x,y,filed\nA,2020,X,Y,2020-01-01\n", encoding="utf-8"
    )
    spec = {**_spec(), "population": deepcopy(EARLIEST)}
    with pytest.raises(DatasetInputError):
        api.run_analysis_csv("input.csv", canonical_json_bytes(spec), allowed_root=tmp_path)


def test_family_result_rejects_forged_selection_counts(tmp_path):
    (tmp_path / "input.csv").write_text(
        "group,year,x,y,family,filed\nA,2020,X,Y,F,2020-01-01\nB,2020,X,Y,F,2020-02-01\n",
        encoding="utf-8",
    )
    spec = {**_spec(), "population": deepcopy(EARLIEST)}
    result = api.run_analysis_csv("input.csv", canonical_json_bytes(spec), allowed_root=tmp_path)
    for changes in (
        {"matched_rows": 3},
        {"representative_rows": 0},
        {"collapsed_rows": 0},
        {"unidentified_rows": 2},
        {"representative_rows": 2, "collapsed_rows": 0},
        {"unidentified_rows": 1},
    ):
        invalid = deepcopy(result)
        invalid["family_selection"].update(changes)
        with pytest.raises(AnalysisContractError):
            validate_analysis_result_v2(invalid)


def test_family_selection_has_the_existing_literal_row_ceiling():
    from patent_analysis.normalization.family import select_family_population

    blank = _dataset((("", "", "A"),)).rows[0]
    rows = (blank,) * 100_000
    assert len(select_family_population(rows, family_column=0)) == 100_000
    with pytest.raises(ValueError):
        select_family_population((*rows, blank), family_column=0)


def test_family_json_cli_and_mcp_use_the_same_core(tmp_path, monkeypatch, capsys):
    import shutil
    import sys

    import anyio
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    input_root = tmp_path / "input"
    input_root.mkdir()
    source = b"year,group,item,family,filed\n2020,A,P,F,2020-02-01\n2020,B,Q,F,2020-01-01\n"
    (input_root / "input.csv").write_bytes(source)
    output = tmp_path / "output"
    output.mkdir()
    spec = {**_spec("uniqueness.v1"), "population": deepcopy(EARLIEST)}
    raw = canonical_json_bytes(spec)
    (input_root / "spec.json").write_bytes(raw)
    direct = api.run_analysis_csv("input.csv", raw, allowed_root=input_root)
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(input_root))
    assert cli.main(["analyze", "input.csv", "--spec", "spec.json", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == direct
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "patent_analysis_mcp.server",
            "--input-root",
            f"input={input_root}",
            "--output-root",
            f"output={output}",
        ],
        cwd=Path(__file__).resolve().parents[1],
    )

    async def scenario():
        with anyio.fail_after(30), (tmp_path / "server.log").open("w", encoding="utf-8") as log:
            async with stdio_client(parameters, errlog=log) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()
                    response = await session.call_tool(
                        "patent_analysis.analyze",
                        {
                            "input_root_id": "input",
                            "path": "input.csv",
                            "spec": spec,
                        },
                    )
                    assert not response.is_error, response
                    content = response.structured_content["content"]
                    assert content["data"] == direct["data"]
                    assert content["family_selection"] == direct["family_selection"]
                    assert str(tmp_path) not in repr(content)
                    # One real Windows family-result render, not another full
                    # analysis x adapter x mark cross product.
                    if sys.platform in {"win32", "darwin"}:
                        rendered = await session.call_tool(
                            "patent_analysis.render",
                            {
                                "output_root_id": "output",
                                "output_path": "family",
                                "analysis_handle": content["render_handle"],
                                "mark": "uniqueness-svg.v1",
                            },
                        )
                        assert not rendered.is_error, rendered
                        receipt = rendered.structured_content["content"]
                        direct_output = tmp_path / "direct"
                        direct_output.mkdir()
                        direct_receipt = api.render_analysis_svg(
                            canonical_json_bytes(direct),
                            mark="uniqueness-svg.v1",
                            output_directory=direct_output,
                            node_executable=shutil.which("node"),
                        )
                        assert (output / "family" / receipt["svg"]).read_bytes() == (
                            direct_output / direct_receipt["svg"]
                        ).read_bytes()

    anyio.run(scenario)
    assert (input_root / "input.csv").read_bytes() == source
    assert (input_root / "spec.json").read_bytes() == raw
