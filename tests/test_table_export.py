from __future__ import annotations

import csv
import json
import sys
from io import StringIO
from pathlib import Path

import pytest

from patent_analysis import AnalysisContractError, api, cli

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
CATALOG = json.loads((EXAMPLES / "analysis-catalog.json").read_bytes())["cases"]
FIRST_ROWS = {
    "inventor-tracking.v1": ("inventors", "inventor", "A", "count", "5"),
    "ranking.v1": ("rows", "label", "A", "value", "3"),
    "matrix.v1": ("cells", "x_label", "X", "value", "5"),
    "timeline.v1": ("series", "year", "2018", "value", "0"),
    "composition.v1": ("items", "label", "A", "value", "3"),
    "growth.v1": ("series", "label", "New", "growth_state", "new"),
    "concentration.v1": ("series", "label", "HHI", "classification", "concentrated"),
    "lifecycle.v1": ("points", "label", "A", "stage", "decline"),
    "growth-quadrant.v1": ("points", "label", "A", "long.rate_percent", "-50"),
    "entry-exit.v1": ("points", "label", "A", "first_year", "2020"),
    "citation.v1": ("points", "label", "A", "citation_value", "12"),
    "matrix-composition.v1": ("items", "label", "P", "share", "0.5"),
    "new-entrants.v1": ("applicants", "label", "B", "classification_memberships", "3"),
    "compara.v1": ("cells", "x", "X", "difference", "2"),
    "cooccurrence.v1": ("label_counts", "label", "P", "count", "5"),
    "collaboration-network.v1": ("nodes", "label", "A", "count", "1"),
    "uniqueness.v1": ("groups", "group", "A", "unique_items", "[]"),
    "shared-involvement.v1": ("groups", "group", "A", "shared_items", '["P","Q"]'),
}


@pytest.mark.parametrize("case", CATALOG, ids=lambda c: c["analysis_id"])
def test_all_analysis_csv_tables_use_saved_aggregate_values(case, monkeypatch, capsys):
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(EXAMPLES))
    assert cli.main([
        "analyze", case["csv"], "--spec", case["spec"], "--format", "csv",
    ]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == api.run_analysis_table(
        case["csv"], (EXAMPLES / case["spec"]).read_bytes(),
        allowed_root=EXAMPLES, table_format="csv",
    )
    rows = list(csv.DictReader(StringIO(captured.out)))
    first = rows[0]
    table, label, expected_label, metric, expected_metric = FIRST_ROWS[case["analysis_id"]]
    assert first["table"] == table
    assert first[label] == expected_label
    assert first[metric] == expected_metric
    if case["analysis_id"] == "growth.v1":
        assert first["growth_rate"] == ""  # Undefined rates are not converted to zero.
    assert all(row["analysis_id"] == case["analysis_id"] for row in rows)
    assert "sha256" not in captured.out and str(EXAMPLES) not in captured.out


def test_network_text_preserves_nodes_and_edges(monkeypatch, capsys):
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(EXAMPLES))
    assert cli.main([
        "analyze", "advanced/patents.csv", "--spec", "advanced/collaboration-network.json",
        "--format", "text",
    ]) == 0
    assert capsys.readouterr().out == (
        "collaboration-network.v1\n\n[nodes]\nlabel | count\nA | 1\nB | 1\n"
        "\n[edges]\nsource | target | count\nA | B | 1\n"
    )


@pytest.mark.parametrize("format_name", ["csv", "text"])
def test_tracking_table_cells_escape_unicode_controls_and_preserve_arrays(
    format_name, tmp_path, monkeypatch, capsys,
):
    inventor = '日本語 ｜ 区分\u202e方向\U0001d173譜\u2028改\u2029段\x1b"引用"\\'
    expected_inventor = inventor.replace("｜", "|")
    applicant = '出願人\u202e方向\U0001d173譜'
    source = tmp_path / "input.csv"
    with source.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["year", "inventor", "applicant"])
        writer.writerow([2020, inventor, applicant])
    before = source.read_bytes()
    raw = (EXAMPLES / "inventor-tracking/spec.json").read_bytes()
    (tmp_path / "spec.json").write_bytes(raw)
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))
    assert cli.main([
        "analyze", source.name, "--spec", "spec.json", "--format", format_name,
    ]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == api.run_analysis_table(
        source.name, raw, allowed_root=tmp_path, table_format=format_name,
    )
    assert not any(char in captured.out for char in ("\u202e", "\U0001d173", "\x1b"))
    assert "日本語" in captured.out and "出願人" in captured.out
    if format_name == "csv":
        rows = list(csv.DictReader(StringIO(captured.out)))
        members = next(row["members"] for row in rows if row["table"] == "clusters")
        applicants = next(row["applicants"] for row in rows if row["table"] == "observations")
    else:
        assert "\u2028" not in captured.out and "\u2029" not in captured.out

        def first_row(table):
            header, row = captured.out.split(f"[{table}]\n", 1)[1].splitlines()[:2]
            fields, cells = header.split(" | "), row.split(" | ")
            assert len(cells) == len(fields)
            return dict(zip(fields, cells, strict=True))

        members = first_row("clusters")["members"]
        applicants = first_row("observations")["applicants"]
        assert "|" not in members
    assert "\u2028" not in members and "\u2029" not in members
    assert json.loads(members) == [expected_inventor]
    assert json.loads(applicants) == [applicant]
    assert source.read_bytes() == before


def _ranking_spec():
    return (EXAMPLES / "basic/ranking.json").read_bytes()


def test_table_escaping_null_and_empty_population(tmp_path, monkeypatch, capsys):
    labels = ['=1+1', ' +SUM(A1)', '-2+3', '@test', '日本語,"引用"', 'line\nbreak', '\x1b[31m']
    source = tmp_path / "input.csv"
    with source.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["group"])
        writer.writerows([label] for label in labels)
    before = source.read_bytes()
    output = api.run_analysis_table(
        source.name, _ranking_spec(), allowed_root=tmp_path, table_format="csv",
    )
    exported = {row["label"] for row in csv.DictReader(StringIO(output))}
    assert "\x1b" not in output
    assert {"'=1+1", "'+SUM(A1)", "'-2+3", "'@test", '日本語,"引用"'} <= exported
    text = api.run_analysis_table(
        source.name, _ranking_spec(), allowed_root=tmp_path, table_format="text",
    )
    # The existing multi-value normalization splits embedded newlines before export.
    assert {"line", "break"} <= exported
    assert "\\u001b[31m" in text and "\x1b" not in text
    context_output = api.run_analysis_table(
        source.name, _ranking_spec(), allowed_root=tmp_path, include_context=True,
    )
    assert "\x1b" not in context_output
    values = [json.loads(row["context_value"])
              for row in csv.DictReader(StringIO(context_output)) if row["table"] == "context"]
    assert all(label in values for label in labels if "\n" not in label and label.strip() == label)
    assert source.read_bytes() == before
    source.write_bytes(b"group\n")
    assert api.run_analysis_table(
        source.name, _ranking_spec(), allowed_root=tmp_path, table_format="csv",
    ) == "analysis_id,table,row_kind,label,value,count,share\n"
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))
    monkeypatch.setattr(sys, "stdin", StringIO("{}"))
    assert cli.main(["analyze", "input.csv", "--spec", "-", "--format", "csv"]) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err


def test_table_format_refuses_unknown_and_json_combination(tmp_path, capsys):
    with pytest.raises(AnalysisContractError):
        api.run_analysis_table("missing.csv", b"{}", allowed_root=tmp_path, table_format="html")
    assert cli.main([
        "analyze", "input.csv", "--spec", "spec.json", "--json", "--format", "csv",
    ]) == 4
    assert json.loads(capsys.readouterr().out)["error"]["code"] == "usage.invalid"


def test_table_budget_rejects_without_partial_stdout(monkeypatch, capsys):
    import patent_analysis.analysis_tables as tables

    monkeypatch.setattr(tables, "MAX_TABLE_BYTES", 32)
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(EXAMPLES))
    assert cli.main([
        "analyze", "advanced/patents.csv", "--spec", "basic/ranking.json", "--format", "csv",
    ]) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and "published limits" in captured.err


@pytest.mark.parametrize("case", CATALOG, ids=lambda c: c["analysis_id"])
def test_context_csv_reconstructs_the_complete_spec_and_analysis(case, monkeypatch, capsys):
    raw = (EXAMPLES / case["spec"]).read_bytes()
    expected = {"spec": json.loads(raw), "analysis": api.run_analysis_csv(
        case["csv"], raw, allowed_root=EXAMPLES)}
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(EXAMPLES))
    assert cli.main(["analyze", case["csv"], "--spec", case["spec"],
                     "--format", "csv", "--include-context"]) == 0
    output = capsys.readouterr().out
    assert output == api.run_analysis_table(case["csv"], raw, allowed_root=EXAMPLES,
                                           include_context=True)
    restored = None
    for row in csv.DictReader(StringIO(output)):
        if row["table"] != "context":
            continue
        value = json.loads(row["context_value"])
        path = json.loads(row["context_path"])
        if path == "":
            restored = value
            continue
        parts = [part.replace("~1", "/").replace("~0", "~") for part in path[1:].split("/")]
        parent = restored
        for part in parts[:-1]:
            parent = parent[int(part)] if isinstance(parent, list) else parent[part]
        if isinstance(parent, list):
            assert len(parent) == int(parts[-1])
            parent.append(value)
        else:
            parent[parts[-1]] = value
    assert restored == expected


def test_context_text_and_usage_and_budget(monkeypatch, capsys):
    import patent_analysis.analysis_tables as tables

    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(EXAMPLES))
    args = ["analyze", "advanced/patents.csv", "--spec", "basic/composition.json"]
    assert cli.main([*args, "--include-context", "--json"]) == 4
    assert json.loads(capsys.readouterr().out)["error"]["code"] == "usage.invalid"
    assert cli.main([*args, "--include-context", "--format", "text"]) == 0
    output = capsys.readouterr().out
    assert "[context]" in output and "/spec/population/family_mode" in output
    assert "/analysis/warnings" in output
    raw = (EXAMPLES / "basic/composition.json").read_bytes()
    with pytest.raises(AnalysisContractError, match="include_context must be boolean"):
        api.run_analysis_table("advanced/patents.csv", raw, allowed_root=EXAMPLES,
                               include_context="true")
    ordinary = api.run_analysis_table("advanced/patents.csv", raw, allowed_root=EXAMPLES)
    monkeypatch.setattr(tables, "MAX_TABLE_BYTES", len(ordinary.encode()) + 20)
    assert cli.main([*args, "--include-context", "--format", "csv"]) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and "published limits" in captured.err


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_context_text_keeps_japanese_readable_and_json_values_safe(
    version, tmp_path, monkeypatch, capsys,
):
    header = '出願人 | 区分\u202e\U0001d173\u2028\u2029末'
    source = tmp_path / "input.csv"
    with source.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow([header])
        writer.writerow(['日本語 "引用" \\'])
    if version == "v1":
        spec = json.loads(_ranking_spec())
        spec["dimension"] = header
        binding_path, label_path = "/spec/dimension", "/analysis/result/rows/0/label"
    else:
        spec = json.loads((EXAMPLES / "basic/composition.json").read_bytes())
        spec["resolution"]["bindings"] = {"group": header, "未使用\u2028\u2029": header}
        binding_path = "/spec/resolution/bindings/group"
        label_path = "/analysis/data/items/0/label"
    raw = json.dumps(spec, ensure_ascii=False).encode()
    (tmp_path / "spec.json").write_bytes(raw)
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))
    assert cli.main(["analyze", "input.csv", "--spec", "spec.json", "--format", "text",
                     "--include-context"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == api.run_analysis_table(
        source.name, raw, allowed_root=tmp_path, table_format="text", include_context=True,
    )
    context = captured.out.split("[context]\nJSON Pointer | JSON value\n", 1)[1]
    assert "出願人" in context and "日本語" in context
    assert not any(char in context for char in ('\u202e', '\U0001d173', '\u2028', '\u2029'))
    values = {}
    for line in context.splitlines():
        assert line.count(" | ") == 1
        path, encoded = line.split(" | ")
        values[path] = json.loads(encoded)
    assert values[binding_path] == header
    assert values[label_path] == '日本語 "引用" \\'
    if version == "v2":
        assert values["/spec/resolution/bindings/未使用\\u2028\\u2029"] == header
