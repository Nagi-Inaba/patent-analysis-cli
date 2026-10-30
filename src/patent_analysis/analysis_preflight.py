"""Bounded metadata-only checks; no aggregation, rendering, or source changes."""

from __future__ import annotations

from importlib import import_module

from patent_analysis.analyses._aggregation import row_number
from patent_analysis.analyses._inventor_registration import MODULE_BY_ID as INVENTOR_MODULES
from patent_analysis.analysis import _parse_numeric
from patent_analysis.analysis_dispatch import ValidatedV1Spec, dispatch_and_validate_spec_bytes
from patent_analysis.analysis_inputs import (
    _project_resolution_spec,
    records_population_spec,
    stable_roles,
)
from patent_analysis.column_resolution import ResolutionError, resolve_roles
from patent_analysis.data import read_csv_rows
from patent_analysis.dataset_v2 import read_dataset_v2
from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_inputs import string_array
from patent_analysis.inventor_models import parse_observation_date
from patent_analysis.inventor_prepare import prepare_execution, read_inventor_dataset
from patent_analysis.normalization import NormalizationConfig, normalize_dataset
from patent_analysis.normalization.family import _date_key
from patent_analysis.normalization.pipeline import _YEAR_ROLES, _role_key
from patent_analysis.normalization.year import extract_year
from patent_analysis.population import apply_population, family_roles


def _report(analysis_id):
    return {
        "preflight_contract_version": "1.0.0", "analysis_id": analysis_id,
        "checks_passed": True, "analysis_eligibility_checked": False,
        "roles": [], "population": None, "issues": [],
    }


def _issue(report, code, *, role=None):
    report["checks_passed"] = False
    report["issues"].append({"code": code, **({"role": role} if role is not None else {})})


def _counts(receipt):
    family = receipt.family_selection
    selected = receipt.included_rows
    matched = family.matched_rows if family else selected
    return {"input_rows": receipt.input_rows, "matched_rows": matched,
            "selected_rows": selected, "filtered_rows": receipt.input_rows - matched,
            "collapsed_rows": matched - selected}


def _role_counts(role, values, *, native=False, family_date=False, numeric=False):
    missing = invalid_date = invalid_ids = invalid_numeric = 0
    strict_date = native and role == "date"
    for value in values:
        if not (value if strict_date else value.strip()):
            missing += 1
        if native and role in {"inventor_ids", "applicant_ids", "source_ids"}:
            try:
                parsed = string_array(value)
                if not parsed and value.strip():
                    missing += 1
            except DatasetInputError:
                invalid_ids += 1
        if value.strip() or (strict_date and value):
            if strict_date:
                try:
                    parse_observation_date(value, kind="filing")
                except DatasetInputError:
                    invalid_date += 1
            elif family_date:
                invalid_date += int(_date_key(value, 0)[0])
            elif _role_key(role) in _YEAR_ROLES:
                invalid_date += int(not extract_year(value))
        if numeric and value.strip() and _parse_numeric(value) is None:
            invalid_numeric += 1
    return {"role": role, "bound": True, "missing_rows": missing,
            "invalid_date_rows": invalid_date, "invalid_id_array_rows": invalid_ids,
            "invalid_numeric_rows": invalid_numeric, "numeric_checked": numeric}


def _legacy_preflight(source, spec, *, allowed_root):
    from pathlib import Path

    report = _report("ranking.v1")
    if Path(source).suffix.casefold() == ".json":
        dataset = read_dataset_v2(source, allowed_root=allowed_root)
        columns = dataset.manifest.raw_header
        rows = [dict(zip(columns, r.values, strict=True)) for r in dataset.rows]
    else:
        rows, manifest = read_csv_rows(source, allowed_root=allowed_root)
        columns = manifest["columns"]
    bindings = {"dimension": spec["dimension"]}
    if spec["measure"]["mode"] != "count":
        bindings["measure"] = spec["measure"]["column"]
    for role, column in bindings.items():
        if column not in columns:
            report["roles"].append({"role": role, "bound": False})
            _issue(report, "resolution.missing", role=role)
        else:
            report["roles"].append(_role_counts(
                role, [r[column] for r in rows], numeric=role == "measure"
            ))
    if report["checks_passed"]:
        report["population"] = {"input_rows": len(rows), "matched_rows": len(rows),
                                "selected_rows": len(rows), "filtered_rows": 0,
                                "collapsed_rows": 0}
    return report


def preflight_analysis(source, spec_bytes, *, allowed_root):
    """Check bindings and population against one input snapshot, returning counts only.

    A passing report does not establish analysis-specific eligibility or budgets.
    Input access/parse and invalid Specs use the existing sanitized exceptions.
    """
    validated = dispatch_and_validate_spec_bytes(spec_bytes)
    spec = validated.spec
    if isinstance(validated, ValidatedV1Spec):
        return _legacy_preflight(source, spec, allowed_root=allowed_root)
    aid = spec["analysis_id"]
    report = _report(aid)
    population, filter_roles = records_population_spec(spec["population"])
    # Import only the module already fixed in the closed implementation registry.
    module = import_module(validated.definition.implementation.__module__)
    parameters = spec["parameters"]
    levels = {}
    native = aid in INVENTOR_MODULES
    if native:
        parameters = module.validate_parameters(parameters)
        roles = tuple(spec["resolution"]["bindings"])
        dataset = read_inventor_dataset(source, spec, parameters, allowed_root=allowed_root)
    else:
        if aid == "matrix.v1":
            matrix = module._validate_parameters(parameters)
            analysis_roles = tuple(matrix[k] for k in ("x_role", "y_role", "pie_role")
                                   if k in matrix)
            levels = dict(matrix["classification_levels"])
        else:
            analysis_roles = module.required_roles(parameters)
        roles = stable_roles((*analysis_roles, *filter_roles))
        dataset = read_dataset_v2(source, allowed_root=allowed_root)
    required = stable_roles((*roles, *family_roles(population)))
    for role in required:
        try:
            binding = resolve_roles(
                dataset.manifest, _project_resolution_spec(spec["resolution"], (role,)),
                required_roles=(role,),
            ).mapping[role]
        except ResolutionError as error:
            report["roles"].append({"role": role, "bound": False})
            _issue(report, error.code, role=role)
            continue
        counts = _role_counts(
            role, [r.values[binding.source_header_ordinal] for r in dataset.rows],
            native=native, family_date=role == population.get("date_role"),
        )
        report["roles"].append(counts)
        if native and (counts["invalid_id_array_rows"] or counts["invalid_date_rows"]):
            _issue(report, "inventor.invalid_cells", role=role)
        if native and role == "record_id" and counts["missing_rows"]:
            _issue(report, "inventor.missing_record_id", role=role)
    if not report["checks_passed"]:
        return report
    try:
        if native:
            inputs = prepare_execution(source, spec, parameters, allowed_root=allowed_root,
                                       dataset=dataset)
            report["population"] = _counts(inputs.prepared.population_receipt)
            report["input_coverage"] = dict(inputs.prepared.coverage)
        else:
            resolution = resolve_roles(
                dataset.manifest, _project_resolution_spec(spec["resolution"], required),
                required_roles=required,
            )
            normalized = normalize_dataset(dataset, resolution, NormalizationConfig(
                roles=roles, multi_value_policy="all", classification_levels=levels
            ))
            measure_role = parameters.get("measure_role")
            if isinstance(measure_role, str):
                measure_role = measure_role.strip()
                counts = next(item for item in report["roles"] if item["role"] == measure_role)
                ordinal = resolution.mapping[measure_role].source_header_ordinal
                counts["numeric_checked"] = True
                counts["invalid_numeric_rows"] = sum(
                    bool(raw.values[ordinal].strip()) and row_number(row, measure_role) is None
                    for raw, row in zip(dataset.rows, normalized.rows, strict=True)
                )
            selected = apply_population(normalized, population, source_role_ordinals={
                role: resolution.mapping[role].source_header_ordinal
                for role in family_roles(population)
            })
            report["population"] = _counts(selected.receipt)
    except (ValueError, DatasetInputError):
        _issue(report, "input.preparation_failed")
    return report
