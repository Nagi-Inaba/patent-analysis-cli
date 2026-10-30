import json

from patent_analysis import cli
from patent_analysis import runtime_diagnostics as diagnostics
from patent_analysis.local_renderer import LocalProcessResult


def test_diagnostics_separates_version_mismatch_and_never_exposes_paths(monkeypatch):
    monkeypatch.setattr(diagnostics, "require_supported_platform", lambda: None)
    monkeypatch.setattr(diagnostics, "resolve_node_executable", lambda _: "SECRET_NODE_PATH")
    monkeypatch.setattr(diagnostics, "launch_trusted_node", lambda *_: LocalProcessResult(
        0, b'{"version":"24.19.0","arch":"x64"}', b"SECRET_STDERR"
    ))
    report = diagnostics.diagnose_renderer()
    assert report["available"] is False
    assert report["detected_node_version"] == "24.19.0"
    assert "node.version_mismatch" in [c["code"] for c in report["checks"]]
    assert "SECRET" not in json.dumps(report)


def test_diagnostics_ignores_untrusted_probe_output(monkeypatch):
    monkeypatch.setattr(diagnostics, "require_supported_platform", lambda: None)
    monkeypatch.setattr(diagnostics, "resolve_node_executable", lambda _: "secret")
    monkeypatch.setattr(diagnostics, "launch_trusted_node", lambda *_: LocalProcessResult(
        0, b'{"version":"SECRET_PATH","arch":"x64"}', b""
    ))
    report = diagnostics.diagnose_renderer()
    assert report["available"] is False
    assert report["detected_node_version"] is None
    assert "SECRET" not in json.dumps(report)


def test_cli_diagnostics_opt_in_does_not_change_capabilities(monkeypatch, capsys):
    monkeypatch.setattr(cli, "diagnose_renderer", lambda **_: {
        "available": False, "checks": [{"code": "node.version_mismatch"}]
    })
    assert cli.main(["capabilities", "--json"]) == 0
    assert "runtime" not in json.loads(capsys.readouterr().out)
    assert cli.main(["capabilities", "--check-runtime", "--json"]) == 5
    assert json.loads(capsys.readouterr().out)["runtime"]["available"] is False
