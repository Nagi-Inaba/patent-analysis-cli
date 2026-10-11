"""M05 adjacent-calendar observed community membership flows."""

from patent_analysis.inventor_activity import cluster_flow

from . import _inventor_common as c

ANALYSIS_ID = "inventor-cluster-flow.v1"
VARIANT = "network"


def validate_parameters(value):
    return c.validate_parameters(
        value, choices=("unit", "pair_weight", "community_method", "date_kind")
    )


def required_roles(value):
    return c.unit_roles(validate_parameters(value), "date")


def _compute(units, observations, p, inputs):
    return cluster_flow(
        units, observations, pair_weight=p["pair_weight"], community_method=p["community_method"]
    )


def analyze_inventor_cluster_flow_csv(source, spec, *, allowed_root):
    return c.run_csv(
        source,
        spec,
        allowed_root=allowed_root,
        analysis_id=ANALYSIS_ID,
        variant=VARIANT,
        validator=validate_parameters,
        compute=_compute,
    )
