"""M09 exact shared mobility candidates, conservative directed legal/group flows."""

from patent_analysis.inventor_mobility import organization_flows

from . import _inventor_common as c
from . import inventor_mobility as mobility

ANALYSIS_ID = "inventor-mobility-flow.v1"
VARIANT = "network"
_AXES = ("legal_entity", "group")
_MODES = ("observations", "candidate_moves", "confirmed_moves")


def validate_parameters(value):
    if not isinstance(value, dict):
        raise ValueError("invalid inventor parameters")
    flow = {k: value[k] for k in ("axis", "mode", "allocation") if k in value}
    p = mobility.validate_parameters({k: v for k, v in value.items() if k not in flow})
    p["axis"] = flow.get("axis", "legal_entity")
    p["mode"] = flow.get("mode", "observations")
    p["allocation"] = flow.get("allocation", "unique_inventors")
    if (
        p["axis"] not in _AXES
        or p["mode"] not in _MODES
        or p["allocation"] not in ("unique_inventors", "fractional_flows")
    ):
        raise ValueError("invalid inventor parameters")
    return p


def required_roles(value):
    return c.unit_roles(validate_parameters(value), "date", "applicant_ids")


def _compute(units, observations, p, inputs):
    audit = mobility._compute(units, observations, p, inputs)
    return organization_flows(
        audit,
        observations,
        inputs.snapshot,
        axis=p["axis"],
        mode=p["mode"],
        allocation=p["allocation"],
    )


def analyze_inventor_mobility_flow_csv(source, spec, *, allowed_root):
    return c.run_csv(
        source,
        spec,
        allowed_root=allowed_root,
        analysis_id=ANALYSIS_ID,
        variant=VARIANT,
        validator=validate_parameters,
        compute=_compute,
    )
