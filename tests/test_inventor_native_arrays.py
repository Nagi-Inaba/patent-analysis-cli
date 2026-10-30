import json
from copy import deepcopy
from pathlib import Path

import pytest

from patent_analysis.api import run_analysis, validate_analysis_spec_bytes
from patent_analysis.dataset_v2 import read_dataset_v2
from patent_analysis.errors import DatasetInputError

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "inventor-analysis"


def native_case(tmp_path):
    spec = json.loads((EXAMPLES / "inventor-network.v1.json").read_bytes())
    rows = json.loads((EXAMPLES / "patents.json").read_bytes())
    encoded = tmp_path / "encoded.json"
    encoded.write_text(json.dumps(rows), encoding="utf-8")
    bindings = spec["resolution"]["bindings"]
    for row in rows:
        for role in ("inventor_ids", "applicant_ids", "source_ids"):
            column = bindings.get(role)
            if column and row.get(column):
                row[column] = json.loads(row[column])
    native = tmp_path / "native.json"
    native.write_text(json.dumps(rows), encoding="utf-8")
    return spec, rows, native


@pytest.mark.parametrize("spec_name", [p.name for p in sorted(EXAMPLES.glob("inventor-*.v1.json"))])
def test_native_id_arrays_preserve_statistics_and_original_file(tmp_path, spec_name):
    spec, rows, native = native_case(tmp_path)
    spec = json.loads((EXAMPLES / spec_name).read_bytes())
    original = native.read_bytes()
    old = run_analysis("encoded.json", json.dumps(spec).encode(), allowed_root=tmp_path)
    spec["parameters"]["id_array_format"] = "native"
    raw = json.dumps(spec).encode()
    validate_analysis_spec_bytes(raw)
    new = run_analysis(native, raw, allowed_root=tmp_path)
    assert new["data"]["statistics"] == old["data"]["statistics"]
    assert new["population"] == old["population"]
    assert native.read_bytes() == original
    # The default generic dataset contract continues to join scalar arrays.
    dataset = read_dataset_v2(native, allowed_root=tmp_path)
    column = spec["resolution"]["bindings"]["inventor_ids"]
    assert dataset.rows[0].values[dataset.manifest.raw_header.index(column)] == "|".join(
        rows[0][column]
    )


def test_native_ids_are_not_split_or_trimmed(tmp_path):
    spec, rows, native = native_case(tmp_path)
    column = spec["resolution"]["bindings"]["inventor_ids"]
    for row in rows:
        row[column] = ["A|B", " A "]
    native.write_text(json.dumps(rows), encoding="utf-8")
    spec["parameters"]["id_array_format"] = "native"
    result = run_analysis(native, json.dumps(spec).encode(), allowed_root=tmp_path)
    assert {r["inventor_id"] for r in result["data"]["statistics"]["nodes"]} == {
        "A|B", " A "
    }


@pytest.mark.parametrize("value", [[1], [{"id": "secret"}], [["nested"]]])
def test_native_id_arrays_reject_non_strings_safely(tmp_path, value):
    spec, rows, native = native_case(tmp_path)
    rows[0][spec["resolution"]["bindings"]["inventor_ids"]] = value
    native.write_text(json.dumps(rows), encoding="utf-8")
    spec["parameters"]["id_array_format"] = "native"
    with pytest.raises(DatasetInputError) as error:
        run_analysis(native, json.dumps(spec).encode(), allowed_root=tmp_path)
    assert "secret" not in str(error.value)


def test_native_format_is_available_to_every_inventor_spec():
    for path in EXAMPLES.glob("inventor-*.v1.json"):
        spec = deepcopy(json.loads(path.read_bytes()))
        spec["parameters"]["id_array_format"] = "native"
        assert validate_analysis_spec_bytes(json.dumps(spec).encode())["valid"]
