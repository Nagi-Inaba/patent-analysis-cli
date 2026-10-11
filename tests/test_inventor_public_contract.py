"""Real public counterexamples shared across all ten exact native IDs."""

import csv
import hashlib
import io
import json
from copy import deepcopy

import pytest
from jsonschema import Draft202012Validator
from test_inventor_foundation_sidecars import bundle, save
from test_inventor_public import spec, write_patents
from test_inventor_public_exposure import IDS
from test_inventor_public_impact import citation_bundle

from patent_analysis.analysis_contracts import AnalysisContractError
from patent_analysis.analysis_runner import run_analysis
from patent_analysis.api import get_public_schema, run_analysis_table
from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_sidecars import sidecar_schema


def request_for(aid, **extras):
    p = {"focus": ["id", "B"]} if aid == "inventor-ego-network.v1" else {}
    if aid == "inventor-impact.v1":
        p["snapshot_date"] = "2025-01-01"
    p.update(extras)
    return spec(aid, p)


def csv_bundle(root, document):
    schema = sidecar_schema()
    paths = {}
    for table, rows in document["tables"].items():
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, list(schema["$defs"][table]["items"]["properties"]))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    k: json.dumps(v, ensure_ascii=False)
                    if isinstance(v, list)
                    else ""
                    if v is None
                    else v
                    for k, v in row.items()
                }
            )
        paths[table] = table + ".csv"
        (root / paths[table]).write_bytes(stream.getvalue().encode("utf-8"))
    return dict(format="csv", version="1.0.0", tables=paths)


def execute(root, request):
    return run_analysis("patents.json", json.dumps(request).encode(), allowed_root=root)


@pytest.mark.parametrize("aid", IDS)
def test_json_csv_equivalent_statistics_and_exact_raw_hash_read_once(tmp_path, monkeypatch, aid):
    import patent_analysis.dataset_v2 as datasets
    import patent_analysis.inventor_sidecars as sidecars

    write_patents(tmp_path)
    d = citation_bundle()
    raw = save(tmp_path, d)
    calls = []
    side_read, patent_read = sidecars.read_verified_bytes, datasets.read_verified_bytes

    def side_spy(source, **kwargs):
        calls.append(str(source))
        return side_read(source, **kwargs)

    def patent_spy(source, **kwargs):
        calls.append(str(source))
        return patent_read(source, **kwargs)

    monkeypatch.setattr(sidecars, "read_verified_bytes", side_spy)
    monkeypatch.setattr(datasets, "read_verified_bytes", patent_spy)
    request = request_for(aid, auxiliary=dict(format="json", path="sidecar.json"))
    a = execute(tmp_path, request)
    assert calls == ["patents.json", "sidecar.json"]
    assert (
        a["data"]["provenance"]["patent_sha256"]
        == hashlib.sha256((tmp_path / "patents.json").read_bytes()).hexdigest()
    )
    assert a["data"]["provenance"]["sidecars"][0]["sha256"] == hashlib.sha256(raw).hexdigest()
    request["parameters"]["auxiliary"] = csv_bundle(tmp_path, d)
    calls.clear()
    b = execute(tmp_path, request)
    assert calls == ["patents.json", *request["parameters"]["auxiliary"]["tables"].values()]
    assert a["data"]["statistics"] == b["data"]["statistics"]
    assert a["data"]["input_coverage"] == b["data"]["input_coverage"]
    assert a["data"]["identity_evidence"] == b["data"]["identity_evidence"]
    if aid == "inventor-impact.v1":
        assert a["data"]["citation_evidence"] == b["data"]["citation_evidence"]
    assert len(b["data"]["provenance"]["sidecars"]) == 9
    assert str(tmp_path) not in json.dumps(b)


@pytest.mark.parametrize("aid", IDS)
def test_derived_filters_selection_exact_exclude_and_day_preservation(tmp_path, aid):
    write_patents(tmp_path)
    request = request_for(aid)
    request["population"]["filters"] = [
        dict(role="year", effect="include", match="year", value=2023)
    ]
    request["population"]["selection_sets"] = [
        dict(
            dimension_role="inventor_id",
            mode="include",
            values=["B"],
            source_date_role="year",
            start_year=2023,
            end_year=2023,
        )
    ]
    result = execute(tmp_path, request)
    assert result["population"]["analyzed_rows"] == 1
    assert result["data"]["input_coverage"]["missing_date"] == 0
    request["population"]["filters"].append(
        dict(role="applicant_id", effect="exclude", match="exact", value="e2")
    )
    assert execute(tmp_path, request) == result
    assert (tmp_path / "patents.json").read_text(encoding="utf-8").find("2023-01-01") >= 0


@pytest.mark.parametrize("aid", IDS)
@pytest.mark.parametrize(
    "mutation", ["date", "id-array", "unknown-sidecar", "unknown-entity", "overpeople", "overrows"]
)
def test_malformed_unknown_overbudget_reject_privately(tmp_path, aid, mutation):
    write_patents(tmp_path)
    request = request_for(aid)
    rows = json.loads((tmp_path / "patents.json").read_text())
    if mutation == "date":
        rows[0]["day"] = "2023-02-29"
    if mutation == "id-array":
        rows[0]["people"] = "A;B"
    if mutation == "overpeople":
        rows = [dict(rows[0], record=f"r{i}", people=json.dumps([f"p{i}"])) for i in range(201)]
    if mutation == "overrows":
        rows = [dict(rows[0], record=f"r{i}") for i in range(5001)]
    if mutation in ("unknown-sidecar", "unknown-entity"):
        d = bundle()
        if mutation == "unknown-sidecar":
            d["tables"]["events"][0]["record_ids"] = ["SECRET-MISSING"]
        else:
            rows[0]["org"] = '["SECRET-ENTITY"]'
        save(tmp_path, d)
        request["parameters"]["auxiliary"] = dict(format="json", path="sidecar.json")
    (tmp_path / "patents.json").write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(DatasetInputError) as caught:
        execute(tmp_path, request)
    assert "SECRET" not in str(caught.value) and str(tmp_path) not in str(caught.value)


@pytest.mark.parametrize("aid", IDS)
@pytest.mark.parametrize(
    "path",
    [
        "../SECRET.json",
        "C:/SECRET/file.json",
        "//server/SECRET.json",
        "sidecar.json:stream",
        "//?/C:/SECRET",
    ],
)
def test_auxiliary_same_root_private_rejection(tmp_path, aid, path):
    write_patents(tmp_path)
    with pytest.raises(DatasetInputError) as caught:
        execute(tmp_path, request_for(aid, auxiliary=dict(format="json", path=path)))
    assert "SECRET" not in str(caught.value) and str(tmp_path) not in str(caught.value)


@pytest.mark.parametrize("aid", IDS)
@pytest.mark.parametrize(
    "change",
    ["family-mode", "both-identities", "unknown-binding", "unknown-filter", "extra-parameter"],
)
def test_nonexecutable_spec_rejected_before_input_read(tmp_path, monkeypatch, aid, change):
    import patent_analysis.inventor_prepare as prepare

    request = request_for(aid)
    if change == "family-mode":
        request["population"].update(family_mode="earliest", family_role="family_id")
    if change == "both-identities":
        request["resolution"]["bindings"]["inventor_names"] = "names"
    if change == "unknown-binding":
        request["resolution"]["bindings"]["unknown"] = "raw"
    if change == "unknown-filter":
        request["population"]["filters"] = [
            dict(role="unknown", effect="include", match="exact", value="x")
        ]
    if change == "extra-parameter":
        request["parameters"]["top_n"] = 1

    def forbidden(*args, **kwargs):
        raise AssertionError("input read before validation")

    monkeypatch.setattr(prepare, "read_dataset_v2", forbidden)
    with pytest.raises(AnalysisContractError):
        execute(tmp_path, request)


@pytest.mark.parametrize("aid", IDS)
def test_empty_population_closed_schemas_and_table(tmp_path, aid):
    write_patents(tmp_path)
    request = request_for(aid)
    request["population"]["filters"] = [
        dict(role="record_id", effect="include", match="exact", value="missing")
    ]
    if aid == "inventor-ego-network.v1":
        with pytest.raises(DatasetInputError):
            execute(tmp_path, request)
        return
    document = execute(tmp_path, request)
    assert document["population"]["analyzed_rows"] == 0
    validator = Draft202012Validator(get_public_schema(aid[:-3] + "-result-v1.schema.json"))
    validator.validate(document["data"])
    mutated = deepcopy(document["data"])
    mutated["statistics"]["invented"] = {}
    assert list(validator.iter_errors(mutated))
    table = run_analysis_table(
        "patents.json", json.dumps(request).encode(), allowed_root=tmp_path, table_format="text"
    )
    assert "(no rows)" in table


@pytest.mark.parametrize("aid", IDS)
def test_curated_canonical_filter_before_selection_for_every_native_id(tmp_path, aid):
    write_patents(tmp_path)
    d = citation_bundle()
    d["tables"]["identities"][0]["raw_alias"] = "A"
    save(tmp_path, d)
    request = request_for(aid, auxiliary=dict(format="json", path="sidecar.json"))
    request["population"]["filters"] = [
        dict(role="inventor_id", effect="include", match="exact", value="p1")
    ]
    result = execute(tmp_path, request)
    assert result["population"]["analyzed_rows"] == 1
    people = result["data"]["identity_evidence"]
    curated = next(p for p in people if p["inventor_id"] == "p1")
    assert curated["identity_status"] == ["curated_mapping"] and curated["source_ids"] == ["s1"]
    assert all(p["inventor_id"] != "A" for p in people)


@pytest.mark.parametrize("aid", IDS)
def test_name_only_is_not_person_confirmation(tmp_path, aid):
    write_patents(tmp_path)
    rows = json.loads((tmp_path / "patents.json").read_text())
    for row in rows:
        row["people"] = ";".join(json.loads(row["people"]))
    (tmp_path / "patents.json").write_text(json.dumps(rows), encoding="utf-8")
    request = request_for(aid)
    request["resolution"]["bindings"].pop("inventor_ids")
    request["resolution"]["bindings"]["inventor_names"] = "people"
    if aid == "inventor-ego-network.v1":
        request["parameters"]["focus"] = ["name", "B"]
    result = execute(tmp_path, request)
    text = json.dumps(result["data"]["statistics"])
    assert "normalized_name_only" in text
    assert "curated_mapping" not in text
    if aid.startswith("inventor-mobility"):
        assert result["data"]["statistics"]["candidates"][0]["employment_status"] == "unknown"


@pytest.mark.parametrize("aid", IDS[:7])
def test_family_unit_retains_all_observations(tmp_path, aid):
    write_patents(tmp_path)
    rows = json.loads((tmp_path / "patents.json").read_text())
    for row in rows:
        row["family"] = " opaque family "
    (tmp_path / "patents.json").write_text(json.dumps(rows), encoding="utf-8")
    request = request_for(aid, unit="family")
    request["resolution"]["bindings"]["family_id"] = "family"
    if aid == "inventor-impact.v1":
        request["parameters"]["citation_basis"] = "unique_citing_ids"
    result = execute(tmp_path, request)
    assert result["population"]["analyzed_rows"] == 3
    assert result["data"]["family_basis"] == dict(family_mode="records", unit="family")
    if aid == "inventor-network.v1":
        assert all(
            e["unit_ids"] == [" opaque family "] for e in result["data"]["statistics"]["edges"]
        )
        assert len(result["data"]["statistics"]["edges"]) == 2


@pytest.mark.parametrize("aid", IDS)
def test_ambiguous_alias_sources_and_reserved_coverage(tmp_path, aid):
    write_patents(tmp_path)
    d = bundle()
    d["tables"]["identities"][0].update(raw_alias="A", status="candidate")
    d["tables"]["identities"].append(
        dict(d["tables"]["identities"][0], alias_id="a2", inventor_id="p2", display_name="Other")
    )
    save(tmp_path, d)
    result = execute(tmp_path, request_for(aid, auxiliary=dict(format="json", path="sidecar.json")))
    text = json.dumps(result["data"]["identity_evidence"])
    assert "ambiguous_id" in text and "p1" in text and "p2" in text and "s1" in text
    stats = result["data"]["statistics"]
    if aid.startswith("inventor-mobility"):
        assert stats["coverage"]["ambiguous_associations"] == 1
    elif aid != "inventor-similarity.v1":
        assert stats["coverage"]["ambiguous_people"] == 1
    else:
        assert stats["features"][0]["undefined_reason"] == "ambiguous_identity"


@pytest.mark.parametrize("aid", IDS)
def test_opaque_id_preserved_without_nfkc_or_strip(tmp_path, aid):
    write_patents(tmp_path)
    rows = json.loads((tmp_path / "patents.json").read_text())
    rows[0]["people"] = json.dumps([" Ａ ", "B"], ensure_ascii=False)
    rows[0]["day"] = "2023-01"
    rows[1]["day"] = "2024"
    (tmp_path / "patents.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    result = execute(tmp_path, request_for(aid))
    text = json.dumps(result["data"]["statistics"], ensure_ascii=False)
    assert " Ａ " in text
    if aid.startswith("inventor-mobility"):
        dates = [r["observed_date"] for r in result["data"]["statistics"]["associations"]]
        assert any(d["raw"] == "2023-01" and d["precision"] == "month" for d in dates)
        assert any(d["raw"] == "2024" and d["precision"] == "year" for d in dates)
    elif aid in ("inventor-network.v1", "inventor-ego-network.v1"):
        assert result["data"]["statistics"]["edges"][0]["first_observation"]["raw"] == "2023-01"


@pytest.mark.parametrize(
    "aid", ("inventor-activity.v1", "inventor-cluster-flow.v1", "inventor-impact.v1", *IDS[7:])
)
def test_year_span_budget_actual_rejection(tmp_path, aid):
    write_patents(tmp_path)
    rows = json.loads((tmp_path / "patents.json").read_text())
    rows[0]["day"], rows[1]["day"] = "1990", "2020"
    (tmp_path / "patents.json").write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(DatasetInputError):
        execute(tmp_path, request_for(aid))


@pytest.mark.parametrize("aid", IDS)
def test_classification_columns_budget_rejects_before_kernel(tmp_path, aid):
    write_patents(tmp_path)
    rows = json.loads((tmp_path / "patents.json").read_text())
    rows[0]["ipc"] = ";".join(f"A01B {i}/00" for i in range(129))
    (tmp_path / "patents.json").write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(DatasetInputError):
        execute(tmp_path, request_for(aid))


@pytest.mark.parametrize("path", ["CON", "nul.json", "dir/AUX.csv", "COM1.txt", "dir/file.json."])
def test_reserved_sidecar_device_paths_rejected_before_verified_read(tmp_path, monkeypatch, path):
    import patent_analysis.inventor_sidecars as sidecars

    write_patents(tmp_path)

    def forbidden(*args, **kwargs):
        raise AssertionError("reserved sidecar path read attempted")

    monkeypatch.setattr(sidecars, "read_verified_bytes", forbidden)
    with pytest.raises(DatasetInputError):
        execute(
            tmp_path, request_for("inventor-network.v1", auxiliary=dict(format="json", path=path))
        )


def test_graph_edges_and_pair_expansion_budgets_precede_metrics(tmp_path, monkeypatch):
    import patent_analysis.inventor_graph as graph

    def forbidden(*args, **kwargs):
        raise AssertionError("expensive metrics reached")

    monkeypatch.setattr(graph, "_betweenness", forbidden)
    template = dict(day="2023", ipc="A01B 1/00", org="[]")
    groups = [
        list(range(64)),
        list(range(30, 94)),
        list(range(60, 124)),
        list(range(30)) + list(range(94, 124)),
    ]
    rows = [
        dict(template, record=f"r{i}", people=json.dumps([f"p{k}" for k in g]))
        for i, g in enumerate(groups)
    ]
    (tmp_path / "patents.json").write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(DatasetInputError):
        execute(tmp_path, request_for("inventor-network.v1"))
    rows = [
        dict(template, record=f"r{i}", people=json.dumps([f"p{k}" for k in range(64)]))
        for i in range(26)
    ]
    (tmp_path / "patents.json").write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(DatasetInputError):
        execute(tmp_path, request_for("inventor-network.v1"))


@pytest.mark.parametrize("aid", IDS)
@pytest.mark.parametrize("role", ["applicant_ids", "source_ids"])
def test_auxiliary_ids_are_string_arrays_not_delimiter_cells(tmp_path, aid, role):
    write_patents(tmp_path)
    rows = json.loads((tmp_path / "patents.json").read_text())
    request = request_for(aid)
    if role == "applicant_ids":
        rows[0]["org"] = "e1;e2"
    else:
        for row in rows:
            row["src"] = "[]"
        rows[0]["src"] = "s1;s2"
        request["resolution"]["bindings"]["source_ids"] = "src"
    (tmp_path / "patents.json").write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(DatasetInputError):
        execute(tmp_path, request)


@pytest.mark.parametrize("aid", IDS)
def test_sidecar_total_rows_budget_is_real(tmp_path, aid):
    write_patents(tmp_path)
    d = bundle()
    source = d["tables"]["sources"][0]
    d["tables"]["sources"] = [dict(source, source_id=f"s{i}") for i in range(4996)]
    save(tmp_path, d)
    with pytest.raises(DatasetInputError):
        execute(tmp_path, request_for(aid, auxiliary=dict(format="json", path="sidecar.json")))


@pytest.mark.parametrize("aid", IDS)
def test_sidecar_bytes_budget_is_real(tmp_path, aid):
    write_patents(tmp_path)
    (tmp_path / "sidecar.json").write_bytes(b" " * (1048576 + 1))
    with pytest.raises(DatasetInputError):
        execute(tmp_path, request_for(aid, auxiliary=dict(format="json", path="sidecar.json")))


@pytest.mark.parametrize("aid", IDS)
def test_schema_objects_are_deeply_closed_and_refs_local(aid):
    schema = get_public_schema(aid[:-3] + "-result-v1.schema.json")
    Draft202012Validator.check_schema(schema)
    pending = [schema]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if "$ref" in value:
                assert value["$ref"].startswith("#/$defs/")
            if value.get("type") == "object":
                assert value["additionalProperties"] is False
                assert set(value["required"]) == set(value["properties"])
            if value.get("type") == "array":
                assert "maxItems" in value
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)


def test_conflicting_excluded_record_is_not_hidden_by_filter(tmp_path):
    write_patents(tmp_path)
    rows = json.loads((tmp_path / "patents.json").read_text())
    rows.append(dict(rows[-1], people='["SECRET-CONFLICT"]'))
    (tmp_path / "patents.json").write_text(json.dumps(rows), encoding="utf-8")
    request = request_for("inventor-network.v1")
    request["population"]["filters"] = [
        dict(role="record_id", effect="include", match="exact", value="r1")
    ]
    with pytest.raises(DatasetInputError):
        execute(tmp_path, request)
