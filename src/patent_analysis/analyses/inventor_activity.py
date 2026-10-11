"""M04 annual witnessed activity, without employment or inactivity inference."""

from patent_analysis.inventor_activity import annual_activity

from . import _inventor_common as c

ANALYSIS_ID = "inventor-activity.v1"
VARIANT = "network"


def validate_parameters(value):
    return c.validate_parameters(
        value, choices=(*c.PROFILE_CHOICES, "date_kind", "community_method")
    )


def required_roles(value):
    return c.unit_roles(validate_parameters(value), "date")


def _compute(units, observations, p, inputs):
    return annual_activity(
        units,
        observations,
        person_weight=p["person_weight"],
        classification_weight=p["classification_weight"],
        community_method=p["community_method"],
    )


def analyze_inventor_activity_csv(source, spec, *, allowed_root):
    return c.run_csv(
        source,
        spec,
        allowed_root=allowed_root,
        analysis_id=ANALYSIS_ID,
        variant=VARIANT,
        validator=validate_parameters,
        compute=_compute,
    )
