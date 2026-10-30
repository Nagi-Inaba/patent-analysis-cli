"""Opt-in, bounded renderer diagnostics with no path or process-output disclosure."""

from __future__ import annotations

import json
import platform
import re
import sys

from patent_analysis.advanced_renderer_resources import load_verified_advanced_renderer_resources
from patent_analysis.local_renderer import (
    launch_trusted_node,
    require_supported_platform,
    resolve_node_executable,
)
from patent_analysis.renderer_resources import (
    load_verified_categorical_renderer_resources,
    load_verified_matrix_renderer_resources,
    load_verified_points_renderer_resources,
    load_verified_renderer_resources,
)

_PROBE = (
    b"process.stdin.resume();process.stdin.on('end',()=>process.stdout.write("
    b"JSON.stringify({version:process.versions.node,arch:process.arch})));"
)
_VERSION = re.compile(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\Z")
_LOADERS = {
    "ranking": load_verified_renderer_resources,
    "matrix": load_verified_matrix_renderer_resources,
    "categorical": load_verified_categorical_renderer_resources,
    "points": load_verified_points_renderer_resources,
    "advanced": load_verified_advanced_renderer_resources,
}


def diagnose_renderer(*, node_executable=None):
    """Check the selected trusted Node and packaged resources, without rendering.

    This is neither an executable trust assessment nor a full native SVG test.
    The default Node is resolved exactly as it is for render, without searching
    for or installing alternate runtimes.
    """
    checks = []
    report = {"runtime_diagnostics_version": "1.0.0", "available": False,
              "required_node_version": "24.22.1", "detected_node_version": None,
              "checks": checks}

    def check(component, code):
        checks.append({"component": component, "ok": code == "ok", "code": code})

    try:
        require_supported_platform()
    except Exception:
        check("platform", "platform.unsupported")
    else:
        check("platform", "ok")
    for family, loader in _LOADERS.items():
        try:
            resources = loader()
            if resources.runtime.node_version != report["required_node_version"]:
                raise ValueError
        except Exception:
            check(f"resources.{family}", "resources.invalid")
        else:
            check(f"resources.{family}", "ok")
    if not checks[0]["ok"]:
        return report
    try:
        node = resolve_node_executable(node_executable)
    except Exception:
        check("node", "node.unavailable")
        return report
    try:
        result = launch_trusted_node(node, _PROBE, b"")
        if result.returncode != 0 or len(result.stdout) > 1024:
            raise ValueError
        probe = json.loads(result.stdout)
        version = probe["version"]
        architecture = probe["arch"]
        if (not isinstance(version, str) or not _VERSION.fullmatch(version)
                or architecture not in {"x64", "arm64", "ia32", "arm", "ppc64", "s390x"}):
            raise ValueError
    except Exception:
        check("node", "node.probe_failed")
        return report
    report["detected_node_version"] = version
    check("node.version", "ok" if version == report["required_node_version"]
          else "node.version_mismatch")
    expected = "arm64" if sys.platform == "darwin" and platform.machine() == "arm64" else "x64"
    check("node.architecture", "ok" if architecture == expected else "node.architecture_mismatch")
    report["available"] = all(item["ok"] for item in checks)
    return report
