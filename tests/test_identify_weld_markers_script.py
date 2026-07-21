import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "identify_weld_markers.ps1"


def test_wrapper_reports_missing_pythonocc_interpreter(tmp_path: Path) -> None:
    manifest = tmp_path / "marker-input-manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SCRIPT),
            "-InputManifest",
            str(manifest),
            "-PythonOccPython",
            r"C:\definitely-missing\python.exe",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "PythonOCC interpreter not found" in (
        completed.stdout + completed.stderr
    )


def test_wrapper_does_not_hide_terminal_or_open_gui() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "Start-Process" not in content
    assert "OCC.Display" not in content
    assert "-m weld_agent.cli identify-markers" in content
