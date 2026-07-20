import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from weld_agent.contracts import validate_document


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "hypermesh" / "tcl" / "weld_agent_probe.tcl"


def _find_tclsh() -> Path | None:
    configured = os.environ.get("ALTAIR_TCLSH")
    if configured:
        return Path(configured)
    on_path = shutil.which("tclsh") or shutil.which("tclsh85")
    if on_path:
        return Path(on_path)
    candidates = sorted(
        Path("C:/Program Files/Altair").glob("*/hw/tcl/*/win64/bin/tclsh*.exe")
    )
    return candidates[0] if candidates else None


def test_probe_script_emits_contract_json_with_stubbed_hypermesh(tmp_path: Path) -> None:
    assert SCRIPT.is_file(), "HyperMesh Tcl adapter is missing"
    tclsh = _find_tclsh()
    if tclsh is None:
        pytest.skip("Altair Tcl runtime is not installed")

    output = tmp_path / "hm probe.json"
    source_path = SCRIPT.as_posix()
    output_path = output.as_posix()
    harness = f"""
proc *clearmark {{args}} {{}}
proc *createmarkpanel {{args}} {{}}
proc hm_getmark {{args}} {{ return {{9 12}} }}
proc hm_getvalue {{args}} {{
    if {{[lsearch -exact $args "id=9"] >= 0}} {{ return {{Part \"A\"}} }}
    return {{Part\\B}}
}}
proc *geomexport {{args}} {{}}
proc *geomoutputdata {{args}} {{}}
proc *CE_ConnectorCreate {{args}} {{}}
source {{{source_path}}}
puts [::weldagent::run_probe {{{output_path}}}]
"""
    completed = subprocess.run(
        [str(tclsh)],
        input=harness,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    validate_document("hypermesh-probe.schema.json", payload)
    assert [item["id"] for item in payload["selected_components"]] == [9, 12]
    assert payload["selected_components"][0]["name"] == 'Part "A"'
    assert all(payload["capabilities"].values())
