"""Raw-ID inventor execution, independent of legacy earliest/year normalization."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict

from patent_analysis.canonical_v2 import canonical_json_bytes
from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_graph import co_inventor_graph, person_json
from patent_analysis.inventor_prepare import prepare_execution
from patent_analysis.inventor_units import _UNIT_FIELDS, form_units

MAX_RESULT_BYTES = 256 * 1024
MAX_STATISTICS_BYTES = 200 * 1024
CHOICES = {
    "unit": ("records", "publication", "application", "family"),
    "person_weight": ("full", "fractional"),
    "pair_weight": ("joint_unit_count", "unit_pair_fractional"),
    "community_method": ("connected_components", "greedy_modularity"),
    "date_kind": ("filing", "publication", "priority"),
    "classification_scheme": ("IPC", "CPC"),
    "classification_level": ("full", "class", "subclass", "main_group", "subgroup"),
}


GRAPH_CHOICES = tuple(CHOICES)
CHOICES["classification_weight"] = ("full", "fractional")
PROFILE_CHOICES = (
    "unit",
    "person_weight",
    "classification_weight",
    "classification_scheme",
    "classification_level",
)


def validate_parameters(value, *, choices=GRAPH_CHOICES, extras=None, required=()):
    extras = extras or {}
    if (
        not isinstance(value, Mapping)
        or set(value) - (set(choices) | extras.keys() | {"auxiliary"})
        or not set(required) <= value.keys()
    ):
        raise ValueError("invalid inventor parameters")
    result = {key: value.get(key, CHOICES[key][0]) for key in choices}
    if any(not isinstance(result[key], str) or result[key] not in CHOICES[key] for key in choices):
        raise ValueError("invalid inventor parameters")
    for key, (default, validator) in extras.items():
        item = value.get(key, default)
        if not validator(item):
            raise ValueError("invalid inventor parameters")
        result[key] = item
    if "auxiliary" in value:
        result["auxiliary"] = value["auxiliary"]
    return result


def required_roles(value):
    p = validate_parameters(value)
    return unit_roles(p)


def unit_roles(p, *extra):
    return tuple(dict.fromkeys(("record_id", _UNIT_FIELDS[p.get("unit", "records")], *extra)))


def executable_roles(spec, roles, filter_roles):
    from patent_analysis.inventor_inputs import _ROLES

    bindings = spec["resolution"].get("bindings", {})
    identities = set(bindings) & {"inventor_ids", "inventor_names"}
    if (
        len(identities) != 1
        or not set(bindings) <= _ROLES
        or spec["population"].get("family_mode") != "records"
    ):
        raise ValueError("invalid inventor bindings")
    identity = next(iter(identities))
    derived = {
        "inventor_id": identity,
        "inventor_name": identity,
        "year": "date",
        "applicant_id": "applicant_ids",
        "classification": "classification",
        "record_id": "record_id",
        "publication_id": "publication_id",
        "application_id": "application_id",
        "family_id": "family_id",
    }
    if not set(filter_roles) <= derived.keys():
        raise ValueError("invalid inventor filter roles")
    return tuple(dict.fromkeys((*roles, identity, *(derived[r] for r in filter_roles))))


def guard_budget(
    *,
    rows=0,
    people=0,
    pairs=0,
    edges=0,
    columns=0,
    years=0,
    sidecar_bytes=0,
    sidecar_rows=0,
    statistics_bytes=0,
    result_bytes=0,
):
    limits = (
        (rows, 5000),
        (people, 200),
        (pairs, 50000),
        (edges, 5000),
        (columns, 128),
        (years, 30),
        (sidecar_bytes, 1048576),
        (sidecar_rows, 5000),
        (statistics_bytes, MAX_STATISTICS_BYTES),
        (result_bytes, MAX_RESULT_BYTES),
    )
    if any(type(value) is not int or not 0 <= value <= limit for value, limit in limits):
        raise DatasetInputError("input is invalid")


def preflight_pair_size(value_count):
    if type(value_count) is not int or not 0 <= value_count <= 200:
        raise DatasetInputError("input is invalid")
    return value_count * (value_count - 1) // 2


def run_csv(
    source,
    spec,
    *,
    allowed_root,
    analysis_id,
    variant,
    validator=validate_parameters,
    compute=None,
    evidence=None,
):
    if not isinstance(spec, Mapping) or spec.get("analysis_id") != analysis_id:
        raise ValueError("analysis spec does not match inventor analysis")
    p = validator(spec.get("parameters"))
    inputs = prepare_execution(source, spec, p, allowed_root=allowed_root)
    prepared = inputs.prepared
    observations = prepared.observations
    guard_budget(
        rows=len(observations),
        people=len({person for row in observations for person in row.inventor_keys}),
    )
    codes = {code for row in observations for code in row.classifications}
    years = {row.observed_date.start.year for row in observations if row.observed_date.start}
    annual = analysis_id in {
        "inventor-activity.v1",
        "inventor-cluster-flow.v1",
        "inventor-mobility.v1",
        "inventor-mobility-flow.v1",
        "inventor-mobility-evidence.v1",
        "inventor-impact.v1",
    }
    guard_budget(columns=len(codes), years=max(years) - min(years) + 1 if annual and years else 0)
    units = form_units(observations, unit=p["unit"])
    statistics = (
        compute(units, observations, p, inputs)
        if compute
        else co_inventor_graph(
            units,
            observations,
            person_weight=p["person_weight"],
            pair_weight=p["pair_weight"],
            community_method=p["community_method"],
        )
    )
    guard_budget(statistics_bytes=len(canonical_json_bytes(statistics)))
    identities = {}
    for row in observations:
        for identity in row.inventors:
            identities.setdefault(identity.key, []).append(identity)
    data = {
        "schema_version": "1.0.0",
        "analysis_id": analysis_id,
        "algorithm_version": "1.0.0",
        "statistics": statistics,
        "input_coverage": dict(prepared.coverage),
        "identity_evidence": [person_json(key, identities) for key in sorted(identities)],
        "family_basis": {"family_mode": "records", "unit": p["unit"]},
        "provenance": {
            "patent_sha256": prepared.dataset.manifest.source_input_sha256,
            "sidecar_state": "provided" if inputs.snapshot is not None else "input_not_provided",
            "sidecars": [asdict(r) for r in inputs.snapshot.receipts] if inputs.snapshot else [],
        },
    }
    if evidence is not None:
        additional = evidence(observations, p, inputs)
        if set(additional) & data.keys():
            raise DatasetInputError("input is invalid")
        data.update(additional)
    guard_budget(result_bytes=len(canonical_json_bytes(data)))
    return {
        "analysis_id": analysis_id,
        "algorithm_version": "1.0.0",
        "result_variant": variant,
        "population": {
            "input_rows": prepared.dataset.manifest.input_rows,
            "analyzed_rows": len(observations),
            "excluded_rows": prepared.dataset.manifest.input_rows - len(observations),
        },
        "data": data,
        "warnings": ["Patent associations do not confirm employment or departments."],
    }


# Fixed native tables: no renderer, persisted result input, or dynamic column selection.
_GRAPH_TABLES = {
    "nodes": (
        "person_key inventor_id display_name identity_status caveats candidate_ids "
        "source_ids activity degree strength betweenness_unweighted "
        "betweenness_weighted pagerank community_id"
    ),
    "edges": (
        "source target weight unit_ids record_ids first_observation "
        "last_observation missing_date_records classifications"
    ),
    "unplottable": (
        "person_key inventor_id display_name identity_status caveats "
        "candidate_ids source_ids activity reason"
    ),
}
_CANDIDATE_COLUMNS = (
    "candidate_id person_key canonical_inventor_id identity_status from_ids to_ids "
    "removed_ids added_ids retained_ids preceding_episode_id following_episode_id "
    "preceding_observation_count following_observation_count preceding_dates following_dates "
    "period_start period_end possible_period_start possible_period_end missing_calendar_years "
    "gap_year_distance observed_status candidate_status employment_status corporate_status "
    "interpretations reason_codes supporting_signals corporate_matches evidence "
    "reviews conflicts corporate_conflicts record_ids source_ids default_flow_adoption"
)
_MOBILITY_TABLES = {
    "candidates": _CANDIDATE_COLUMNS,
    "associations": (
        "person_key record_id observed_date applicant_ids identity_status "
        "source_ids group_relations entity_aliases"
    ),
    "episodes": (
        "episode_id person_key start end record_ids applicant_ids "
        "unknown_applicants parallel_association observations"
    ),
    "unbound_reviews": (
        "review_id inventor_id claim status reason reviewed_date "
        "evidence_ids event_ids record_ids source_ids supersedes_review_id active"
    ),
    "corporate_changes": (
        "change_id person_key type entity_ids record_ids "
        "from_relations to_relations event_matches employment_confirmation"
    ),
}
_TABLES = {
    "inventor-network.v1": _GRAPH_TABLES,
    "inventor-ego-network.v1": {
        **_GRAPH_TABLES,
        "hop_membership": "person_token hop",
        "partners": (
            "person_token weight unit_ids record_ids first_observation "
            "last_observation missing_date_records classifications"
        ),
    },
    "inventor-technology.v1": {
        "profiles": (
            "person_key inventor_id display_name identity_status candidate_ids "
            "source_ids activity classification_total entropy hhi "
            "predominant_classification undefined_reason"
        ),
        "cells": "person_token classification count unit_count share relative_specialization",
        "classifications": "classification count reference_share",
    },
    "inventor-activity.v1": {
        "people": (
            "person_key inventor_id identity_status cumulative_unit_activity "
            "cumulative_unique_units annual_unit_presences missing_date_unit_ids"
        ),
        "calendar": "year observed record_count unit_count",
        "observations": (
            "person_token year observed unit_count unit_ids record_ids "
            "activity classifications partners added_partners "
            "continued_partners not_observed_partners community_id"
        ),
    },
    "inventor-cluster-flow.v1": {
        "nodes": "node_id year kind members size split merge",
        "links": "source target source_year target_year members width kind",
        "unplottable": "person_key inventor_id identity_status candidate_ids source_ids reasons",
    },
    "inventor-similarity.v1": {
        "features": "person_key inventor_id identity_status values undefined_reason",
        "similarities": "source target cosine undefined_reason shared_classifications",
        "co_inventor_edges": "source target weight",
    },
    "inventor-impact.v1": {
        "people": (
            "person_key inventor_id identity_status activity known_citation_activity "
            "raw_sum raw_mean adjusted_sum adjusted_mean recent_activity "
            "partial_citation_coverage unplottable_reasons"
        ),
        "units": "unit_id record_ids citation_count filing_year adjusted_value undefined_reasons",
        "cohorts": (
            "filing_year classification distinct_units reference_weight raw_mean undefined_reason"
        ),
    },
    "inventor-mobility.v1": _MOBILITY_TABLES,
    "inventor-mobility-flow.v1": {
        **_MOBILITY_TABLES,
        "flows": (
            "flow_id from_id to_id layer status employment_status corporate_status "
            "reason_codes unique_inventors transition_events inventor_ids candidate_ids "
            "axis mode allocation weight_basis flow_weight event_mass record_ids source_ids "
            "evidence_ids review_ids event_ids"
        ),
        "unallocated": (
            "candidate_id reason layer status axis mode allocation weight_basis "
            "employment_status corporate_status reason_codes event_mass "
            "from_legal_id to_legal_id from_id to_id"
        ),
    },
    "inventor-mobility-evidence.v1": _MOBILITY_TABLES,
}


def inventor_table(source, spec_bytes, *, allowed_root, table_format="csv", include_context=False):
    import csv
    import json

    from patent_analysis.analysis_contracts import AnalysisContractError
    from patent_analysis.analysis_runner import run_analysis
    from patent_analysis.analysis_tables import _Buffer, _cell, _context_rows, _escape_json_text

    if table_format not in ("csv", "text") or type(include_context) is not bool:
        raise AnalysisContractError("analysis table parameters are invalid")
    document = run_analysis(source, spec_bytes, allowed_root=allowed_root)
    analysis_id = document["analysis_id"]
    statistics = document["data"]["statistics"]
    tables = {table: columns.split() for table, columns in _TABLES[analysis_id].items()}
    tables["identity_evidence"] = (
        "person_key person_token inventor_id display_name identity_status "
        "caveats candidate_ids source_ids"
    ).split()
    if analysis_id == "inventor-impact.v1":
        tables["citation_evidence"] = (
            "record_id snapshot_date entry_state citation_count citing_ids citation_ids source_ids"
        ).split()
    columns = list(dict.fromkeys(c for fields in tables.values() for c in fields))
    output = _Buffer()
    if table_format == "csv":
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(
            [
                "analysis_id",
                "table",
                *columns,
                *(["context_path", "context_value"] if include_context else []),
            ]
        )
    else:
        output.write(analysis_id + "\n")
    for table, fields in tables.items():
        if table_format == "text":
            output.write("\n[" + table + "]\n" + " | ".join(fields) + "\n")
        rows = (
            document["data"][table]
            if table in ("identity_evidence", "citation_evidence")
            else statistics[table]
        )
        for row in rows:
            if table_format == "csv":
                writer.writerow(
                    [
                        analysis_id,
                        table,
                        *(_cell(row[c], csv_mode=True) if c in fields else "" for c in columns),
                        *(["", ""] if include_context else []),
                    ]
                )
            else:
                output.write(" | ".join(_cell(row[c], csv_mode=False) for c in fields) + "\n")
        if not rows and table_format == "text":
            output.write("(no rows)\n")
    if include_context:
        if table_format == "text":
            output.write("\n[context]\nJSON Pointer | JSON value\n")
        for path, value in _context_rows({"spec": json.loads(spec_bytes), "analysis": document}):
            encoded = json.dumps(
                value, ensure_ascii=table_format == "csv", allow_nan=False, separators=(",", ":")
            )
            if table_format == "csv":
                writer.writerow(
                    [
                        analysis_id,
                        "context",
                        *([""] * len(columns)),
                        json.dumps(path, ensure_ascii=True),
                        encoded,
                    ]
                )
            else:
                output.write(
                    _cell(path, csv_mode=False)
                    + " | "
                    + _escape_json_text(encoded, escape_separator=True)
                    + "\n"
                )
    return output.result()
