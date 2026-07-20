import json
from pathlib import Path
from subprocess import CompletedProcess

from weld_agent.runtime import probe_pythonocc


def test_probe_reports_versions(monkeypatch) -> None:
    completed = CompletedProcess(
        args=[],
        returncode=0,
        stdout=json.dumps({"python": "3.11.15", "occ": "7.9.0"}),
        stderr="",
    )
    monkeypatch.setattr(
        "weld_agent.runtime.subprocess.run",
        lambda *args, **kwargs: completed,
    )
    result = probe_pythonocc(Path("C:/fake/python.exe"))
    assert result.available is True
    assert result.python_version == "3.11.15"
    assert result.occ_version == "7.9.0"


def test_probe_reports_process_failure(monkeypatch) -> None:
    completed = CompletedProcess(args=[], returncode=1, stdout="", stderr="import failed")
    monkeypatch.setattr(
        "weld_agent.runtime.subprocess.run",
        lambda *args, **kwargs: completed,
    )
    result = probe_pythonocc(Path("C:/fake/python.exe"))
    assert result.available is False
    assert result.error == "import failed"


def test_probe_reports_missing_executable(monkeypatch) -> None:
    def raise_missing(*args, **kwargs):
        raise FileNotFoundError("python.exe not found")

    monkeypatch.setattr("weld_agent.runtime.subprocess.run", raise_missing)
    result = probe_pythonocc(Path("C:/missing/python.exe"))
    assert result.available is False
    assert result.error is not None
    assert "not found" in result.error
