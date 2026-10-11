"""M10 full candidate evidence and review histories; analysis/table only."""

from patent_analysis.inventor_mobility import build_mobility_evidence

from . import _inventor_common as c
from .inventor_mobility import required_roles as required_roles
from .inventor_mobility import validate_parameters

ANALYSIS_ID = "inventor-mobility-evidence.v1"
VARIANT = "grouped-metrics"


def _compute(units, observations, p, inputs):
    return build_mobility_evidence(
        observations,
        inputs.snapshot,
        minimum_observations=p["minimum_observations"],
        maximum_gap_years=p["maximum_gap_years"],
        review_bindings=p["review_bindings"],
    )


def analyze_inventor_mobility_evidence_csv(source, spec, *, allowed_root):
    return c.run_csv(
        source,
        spec,
        allowed_root=allowed_root,
        analysis_id=ANALYSIS_ID,
        variant=VARIANT,
        validator=validate_parameters,
        compute=_compute,
    )
