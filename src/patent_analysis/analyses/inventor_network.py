"""M01 public co-inventor graph over explicit inventor foundation inputs."""

from __future__ import annotations

from . import _inventor_common as c

ANALYSIS_ID = "inventor-network.v1"
VARIANT = "network"
required_roles = c.required_roles
validate_parameters = c.validate_parameters


def analyze_inventor_network_csv(source, spec, *, allowed_root):
    return c.run_csv(
        source, spec, allowed_root=allowed_root, analysis_id=ANALYSIS_ID, variant=VARIANT
    )
