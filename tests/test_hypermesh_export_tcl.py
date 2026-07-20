import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from weld_agent.contracts import validate_document


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "hypermesh" / "tcl" / "weld_agent_export.tcl"


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


HARNESS = r'''
array set ::marks {}
set ::visible {1 15 20}
set ::exported {}
set ::fail_on @FAIL_ON@
set ::selected @SELECTED@
set ::surface_ids @SURFACE_IDS@
set ::model_file {@MODEL_FILE@}

proc *clearmark {entity mark} { set ::marks($entity,$mark) {} }
proc *createmarkpanel {entity mark message} { set ::marks($entity,$mark) $::selected }
proc *createmark {entity mark args} {
    if {$entity eq "components" && [lindex $args 0] eq "displayed"} {
        set ::marks($entity,$mark) $::visible
        return
    }
    if {[lindex $args 0] eq "by comp id"} {
        set ::last_component [lindex $args 1]
        if {$entity eq "surfaces"} { set ::marks($entity,$mark) $::surface_ids }
        if {$entity eq "solids"} { set ::marks($entity,$mark) {} }
        if {$entity eq "elements"} { set ::marks($entity,$mark) {} }
        return
    }
    set ::marks($entity,$mark) $args
}
proc hm_getmark {entity mark} { return $::marks($entity,$mark) }
proc hm_marklength {entity mark} { return [llength $::marks($entity,$mark)] }
proc hm_getvalue {entity args} {
    if {[lsearch -exact $args "id=15"] >= 0} { return "6101081-DD01-A" }
    return "6101161-DD01-A"
}
proc hm_getboundingbox {entity mark args} {
    if {$::last_component == 15} { return {0 0 0 100 50 5} }
    return {20 10 1 80 40 6}
}
proc hm_info {args} {
    if {[lindex $args 0] eq "currentfile"} { return $::model_file }
    return "2017.2"
}
proc *displaycollectorwithfilter {entity state filter geometry elements} {
    if {$state eq "none"} { set ::visible {} }
}
proc *displaycollectorsbymark {entity mark state geometry elements} {
    set ::visible $::marks($entity,$mark)
}
proc *geomexport {cad_type step_path options} {
    set component_id [lindex $::visible 0]
    lappend ::exported $component_id
    set stream [open $step_path w]
    puts $stream "STEP-$component_id"
    close $stream
    if {$component_id == $::fail_on} { error "forced export failure" }
}

source {@SOURCE@}
set status [catch {
    set manifest [::weldagent::run_export_probe {@OUTPUT_ROOT@}]
    puts "MANIFEST=$manifest"
} message]
puts "STATUS=$status"
puts "MESSAGE=$message"
if {$status != 0} { puts "ERRORINFO=$::errorInfo" }
puts "VISIBLE=$::visible"
puts "EXPORTED=$::exported"
if {$status != 0} { exit 7 }
'''


def _run_harness(
    tmp_path: Path,
    fail_on: int,
    selected: str = "{15 20}",
    surface_ids: str = "{101 102}",
    model_file: str = "C:/models/FDOOR.hm",
) -> subprocess.CompletedProcess[str]:
    tclsh = _find_tclsh()
    if tclsh is None:
        pytest.skip("Altair Tcl runtime is not installed")
    source = HARNESS.replace("@SOURCE@", SCRIPT.as_posix())
    source = source.replace("@OUTPUT_ROOT@", tmp_path.as_posix())
    source = source.replace("@FAIL_ON@", str(fail_on))
    source = source.replace("@SELECTED@", selected)
    source = source.replace("@SURFACE_IDS@", surface_ids)
    source = source.replace("@MODEL_FILE@", model_file)
    return subprocess.run(
        [str(tclsh)],
        input=source,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )


def _line(stdout: str, prefix: str) -> str:
    return next(
        line.removeprefix(prefix)
        for line in stdout.splitlines()
        if line.startswith(prefix)
    )


def test_export_emits_two_steps_and_restores_display(tmp_path: Path) -> None:
    completed = _run_harness(tmp_path, fail_on=-1)
    assert completed.returncode == 0, completed.stderr
    manifest_path = Path(_line(completed.stdout, "MANIFEST="))
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_document("export-manifest.schema.json", payload)
    assert [item["id"] for item in payload["components"]] == [15, 20]
    assert [Path(item["step_path"]).name for item in payload["components"]] == [
        "component-15.step",
        "component-20.step",
    ]
    assert payload["export_options"]["units"] == "Millimeters"
    assert _line(completed.stdout, "EXPORTED=") == "15 20"
    assert _line(completed.stdout, "VISIBLE=") == "1 15 20"


def test_second_export_failure_cleans_steps_and_restores_display(
    tmp_path: Path,
) -> None:
    completed = _run_harness(tmp_path, fail_on=20)
    assert completed.returncode == 7
    assert _line(completed.stdout, "VISIBLE=") == "1 15 20"
    run_dirs = list(tmp_path.iterdir())
    assert len(run_dirs) == 1
    assert not (run_dirs[0] / "export-manifest.json").exists()
    assert list(run_dirs[0].glob("*.step")) == []


def test_duplicate_selection_stops_before_run_directory(tmp_path: Path) -> None:
    completed = _run_harness(tmp_path, fail_on=-1, selected="{15 15}")
    assert completed.returncode == 7
    assert "INVALID_SELECTION" in _line(completed.stdout, "MESSAGE=")
    assert list(tmp_path.iterdir()) == []


def test_empty_component_geometry_restores_display(tmp_path: Path) -> None:
    completed = _run_harness(tmp_path, fail_on=-1, surface_ids="{}")
    assert completed.returncode == 7
    assert "EMPTY_COMPONENT_GEOMETRY" in _line(completed.stdout, "MESSAGE=")
    assert _line(completed.stdout, "VISIBLE=") == "1 15 20"
    run_dir = next(tmp_path.iterdir())
    assert list(run_dir.iterdir()) == []


def test_unsaved_model_is_recorded_as_warning(tmp_path: Path) -> None:
    completed = _run_harness(tmp_path, fail_on=-1, model_file="")
    assert completed.returncode == 0
    manifest_path = Path(_line(completed.stdout, "MANIFEST="))
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["hypermesh"]["model_name"] == "Untitled"
    assert len(payload["warnings"]) == 1
