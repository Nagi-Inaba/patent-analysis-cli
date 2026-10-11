"""M07 explicit snapshot citation observations and filing-field baselines."""

from collections.abc import Mapping

from patent_analysis.inventor_citations import _citations, citation_metrics
from patent_analysis.inventor_identity import text_ok
from patent_analysis.inventor_models import parse_observation_date

from . import _inventor_common as c

ANALYSIS_ID = "inventor-impact.v1"
VARIANT = "points"


def _snapshot(v):
    return (
        isinstance(v, str) and parse_observation_date(v, kind="citation_snapshot").start is not None
    )


def validate_parameters(value):
    p = c.validate_parameters(
        value,
        choices=(
            "unit",
            "person_weight",
            "date_kind",
            "classification_scheme",
            "classification_level",
        ),
        extras={
            "snapshot_date": (None, _snapshot),
            "citation_basis": (
                "record_counts",
                lambda v: v in ("record_counts", "unique_citing_ids", "representative_record"),
            ),
            "representative_records": (
                None,
                lambda v: (
                    v is None
                    or isinstance(v, Mapping)
                    and len(v) <= 5000
                    and all(text_ok(k) and text_ok(r) for k, r in v.items())
                ),
            ),
            "min_cohort_units": (5, lambda v: type(v) is int and 1 <= v <= 5000),
            "recent_start_year": (None, lambda v: v is None or type(v) is int and 1 <= v <= 9999),
        },
        required=("snapshot_date",),
    )
    if (
        (p["citation_basis"] == "representative_record")
        != (p["representative_records"] is not None)
        or p["citation_basis"] == "record_counts"
        and p["unit"] in ("application", "family")
    ):
        raise ValueError("invalid inventor parameters")
    return p


def required_roles(value):
    return c.unit_roles(validate_parameters(value), "date", "classification")


def _compute(units, observations, p, inputs):
    ids = {o.record_id for o in observations}
    full_citations = inputs.snapshot.tables["citations"] if inputs.snapshot else ()
    # Semantic citation conflict/date validation precedes population restriction.
    _citations(
        full_citations, {o.record_id: o for o in inputs.full_observations}, p["snapshot_date"]
    )
    citations = tuple(r for r in full_citations if r["record_id"] in ids)
    return citation_metrics(
        units,
        observations,
        citations,
        snapshot_date=p["snapshot_date"],
        citation_basis=p["citation_basis"],
        representative_records=p["representative_records"],
        person_weight=p["person_weight"],
        min_cohort_units=p["min_cohort_units"],
        recent_start_year=p["recent_start_year"],
    )


def _evidence(observations, p, inputs):
    # Retain per-record observation states outside unmodified numerical statistics.
    # An explicit unknown row differs from no matching snapshot entry and from zero.
    by_record = {}
    if inputs.snapshot:
        for row in inputs.snapshot.tables["citations"]:
            if row["snapshot_date"] == p["snapshot_date"]:
                by_record.setdefault(row["record_id"], []).append(row)
    rows = []
    for record_id in sorted({o.record_id for o in observations}):
        supplied = by_record.get(record_id, [])
        count = supplied[0]["count"] if supplied else None
        state = (
            "input_not_provided"
            if inputs.snapshot is None
            else "entry_not_provided"
            if not supplied
            else "unknown"
            if count is None
            else "known"
        )
        citing = supplied[0]["citing_ids"] if supplied else None
        rows.append(
            dict(
                record_id=record_id,
                snapshot_date=p["snapshot_date"],
                entry_state=state,
                citation_count=count,
                citing_ids=None if citing is None else list(citing),
                citation_ids=sorted(r["citation_id"] for r in supplied),
                source_ids=sorted({s for r in supplied for s in r["source_ids"]}),
            )
        )
    return {"citation_evidence": rows}


def analyze_inventor_impact_csv(source, spec, *, allowed_root):
    return c.run_csv(
        source,
        spec,
        allowed_root=allowed_root,
        analysis_id=ANALYSIS_ID,
        variant=VARIANT,
        validator=validate_parameters,
        compute=_compute,
        evidence=_evidence,
    )
