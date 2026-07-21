# Terminal Weld Marker Identification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repository-owned, terminal-first PythonOCC workflow that classifies explicit Solid markers in a small, user-specified set of STEP Components as cylinders, triangular prisms, or unknowns and writes reproducible JSON, CSV, and log artifacts.

**Architecture:** A new manifest and result schema define the boundary. `occ_marker_reader.py` converts STEP/OCC objects into plain immutable observations; `marker_identification.py` classifies those observations without depending on OCC; the orchestration module validates inputs, reports four visible terminal stages, and atomically writes artifacts. The existing CLI receives one new subcommand, and a PowerShell wrapper selects the configured PythonOCC interpreter without opening a GUI.

**Tech Stack:** Python 3.11, PythonOCC/OpenCascade 7.9.0, JSON Schema Draft 2020-12, pytest, PowerShell 5.1, HyperMesh-produced AP214 STEP in millimetres.

## Global Constraints

- Work directly on `main`; do not create a worktree or couple this repository to `fluent-automation`.
- Analyze only the explicitly listed small candidate Components; do not scan all 34 door Components.
- Treat OCC as a background library; do not open an OCC GUI or create a second terminal window.
- Accept only `mm` and `global` coordinates in version 1.0.
- Do not commit customer STEP, `.hm`, temporary exports, run results, or a local PythonOCC absolute path.
- Do not infer 2T/3T, welding faces, new candidate welds, or Connector data in this plan.
- Do not modify or save the HyperMesh model.
- Every production behavior follows red-green-refactor; run `scripts/verify.ps1` with `WELD_AGENT_PYTHONOCC_PYTHON` before claiming completion.

---

## File Map

- `schemas/marker-input-manifest.schema.json`: one-or-more candidate Component input contract.
- `schemas/weld-markers.schema.json`: formal JSON result contract.
- `tests/fixtures/marker-input-manifest.valid.json`: valid contract fixture with absolute synthetic paths.
- `tests/test_marker_contracts.py`: schema and semantic identity tests.
- `src/weld_agent/geometry/marker_identification.py`: OCC-free observations, records, validation, and topology classifier.
- `tests/test_marker_identification.py`: fast classifier tests using plain Python values.
- `src/weld_agent/geometry/occ_marker_reader.py`: STEP reading and OCC-to-observation conversion.
- `tests/test_occ_marker_reader.py`: generated STEP integration tests for cylinder, triangular prism, and box.
- `src/weld_agent/marker_identification.py`: manifest orchestration, progress, deterministic ordering, atomic JSON/CSV/log output.
- `tests/test_marker_identification_workflow.py`: fake-reader workflow and artifact tests.
- `src/weld_agent/cli.py`: `identify-markers` command and classified error reporting.
- `tests/test_marker_identification_cli.py`: CLI dispatch, summary, and exit-code tests.
- `scripts/identify_weld_markers.ps1`: visible Windows entry point.
- `tests/test_identify_weld_markers_script.py`: wrapper failure-path test.
- `docs/manual-tests/terminal-weld-marker-identification.md`: current car-door runbook.
- `README.md`, `docs/setup.md`: supported command and current boundary.

---

### Task 1: Freeze Marker Input and Output Contracts

**Files:**
- Create: `schemas/marker-input-manifest.schema.json`
- Create: `schemas/weld-markers.schema.json`
- Create: `tests/fixtures/marker-input-manifest.valid.json`
- Create: `tests/test_marker_contracts.py`
- Modify: `src/weld_agent/contracts.py`

**Interfaces:**
- Consumes: `validate_document(schema_name: str, payload: Mapping[str, Any])`.
- Produces: validated `marker-input-manifest.schema.json` and `weld-markers.schema.json`; semantic uniqueness checks for Component IDs and absolute STEP paths.

- [ ] **Step 1: Write failing contract tests**

Create `tests/test_marker_contracts.py` with these behaviors:

```python
import json
from pathlib import Path

import pytest

from weld_agent.contracts import ContractValidationError, load_document, validate_document


FIXTURES = Path(__file__).parent / "fixtures"


def payload() -> dict:
    return json.loads(
        (FIXTURES / "marker-input-manifest.valid.json").read_text(encoding="utf-8")
    )


def test_marker_manifest_accepts_one_or_more_unique_components() -> None:
    document = load_document(
        FIXTURES / "marker-input-manifest.valid.json",
        "marker-input-manifest.schema.json",
    )
    assert document["run_id"] == "marker-run-001"
    assert [item["id"] for item in document["components"]] == [5, 12]


def test_marker_manifest_rejects_duplicate_component_ids() -> None:
    document = payload()
    document["components"][1]["id"] = 5
    with pytest.raises(ContractValidationError, match="distinct component IDs"):
        validate_document("marker-input-manifest.schema.json", document)


def test_marker_manifest_rejects_relative_step_paths() -> None:
    document = payload()
    document["components"][0]["step_path"] = "component-5.step"
    with pytest.raises(ContractValidationError, match="absolute"):
        validate_document("marker-input-manifest.schema.json", document)


def test_marker_manifest_requires_millimetres() -> None:
    document = payload()
    document["hypermesh"]["units"] = "inch"
    with pytest.raises(ContractValidationError, match="mm"):
        validate_document("marker-input-manifest.schema.json", document)
```

The fixture contains two synthetic absolute paths, IDs 5 and 12, `units: "mm"`, `coordinate_system: "global"`, and valid geometry summaries using `selection.schema.json#/$defs/geometry_summary`.

- [ ] **Step 2: Run the contract tests and verify RED**

Run:

```powershell
& $env:WELD_AGENT_PYTHONOCC_PYTHON -m pytest tests/test_marker_contracts.py -v
```

Expected: FAIL because `marker-input-manifest.schema.json` does not exist.

- [ ] **Step 3: Add both schemas and semantic validation**

`marker-input-manifest.schema.json` must require this exact top-level structure:

```json
{
  "schema_version": "1.0",
  "run_id": "marker-run-001",
  "hypermesh": {
    "build": "HyperMesh 2017",
    "model_name": "synthetic-marker-model",
    "units": "mm",
    "coordinate_system": "global"
  },
  "components": [
    {
      "id": 5,
      "name": "MARKERS-A",
      "step_path": "C:/synthetic/component-5.step",
      "summary": {
        "surface_count": 7,
        "solid_count": 1,
        "element_count": 0,
        "bbox": [0, 0, 0, 10, 10, 10]
      }
    }
  ]
}
```

Use `additionalProperties: false`, `minItems: 1`, the existing geometry-summary `$ref`, and constants for schema version, units, and coordinate system. `weld-markers.schema.json` must require `status: "success"`, versions, manifest SHA-256, summaries, markers, warnings, and elapsed milliseconds. A marker permits `axis` to be either a three-number array or `null`, and restricts `marker_type` to `cylinder`, `triangular_prism`, or `unknown`.

Add this semantic branch to `validate_document`:

```python
if schema_name == "marker-input-manifest.schema.json":
    _validate_marker_component_identity(payload)
```

Implement `_validate_marker_component_identity` by requiring unique IDs, unique STEP paths, and `_is_absolute_any_platform` for every path. Do not reuse `_validate_two_component_identity`, because this contract allows one or more Components.

- [ ] **Step 4: Run contract tests and the existing contract suite**

Run:

```powershell
& $env:WELD_AGENT_PYTHONOCC_PYTHON -m pytest tests/test_marker_contracts.py tests/test_contracts.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit the contract boundary**

```powershell
git add schemas/marker-input-manifest.schema.json schemas/weld-markers.schema.json tests/fixtures/marker-input-manifest.valid.json tests/test_marker_contracts.py src/weld_agent/contracts.py
git commit -m "feat: add weld marker identification contracts"
```

---

### Task 2: Implement the OCC-Free Marker Classifier

**Files:**
- Create: `src/weld_agent/geometry/marker_identification.py`
- Create: `tests/test_marker_identification.py`

**Interfaces:**
- Produces: `FaceObservation`, `SolidObservation`, `MarkerRecord`, `InvalidMarkerGeometry`, and `classify_marker(component_id, component_name, solid_index, observation) -> MarkerRecord`.
- Consumed later by: `PythonOccMarkerReader` and `identify_weld_markers`.

- [ ] **Step 1: Write failing pure classification tests**

Tests construct observations without importing OCC:

```python
def test_split_cylinder_faces_are_classified_as_cylinder() -> None:
    observation = SolidObservation(
        center=(0.0, 0.0, 3.0),
        bbox=(-3.0, -3.0, 0.0, 3.0, 3.0, 6.0),
        volume=169.646,
        faces=(
            FaceObservation("cylinder", 4, None, (0.0, 0.0, 1.0)),
            FaceObservation("cylinder", 4, None, (0.0, 0.0, 1.0)),
            FaceObservation("plane", 2, (0.0, 0.0, 0.0), None),
            FaceObservation("plane", 2, (0.0, 0.0, 6.0), None),
        ),
    )
    result = classify_marker(5, "MARKERS", 1, observation)
    assert result.marker_type == "cylinder"
    assert result.axis == pytest.approx((0.0, 0.0, 1.0))


def test_five_plane_triangular_prism_is_classified() -> None:
    result = classify_marker(12, "MARKERS", 3, triangular_observation())
    assert result.marker_type == "triangular_prism"
    assert result.axis == pytest.approx((0.0, 0.0, 1.0))


def test_box_is_unknown_and_preserves_topology_evidence() -> None:
    result = classify_marker(12, "MARKERS", 4, box_observation())
    assert result.marker_type == "unknown"
    assert result.axis is None
    assert result.evidence["face_count"] == 6
    assert result.warnings == ("UNSUPPORTED_MARKER_TOPOLOGY",)


def test_non_finite_center_is_invalid_geometry() -> None:
    observation = replace(cylinder_observation(), center=(math.nan, 0.0, 0.0))
    with pytest.raises(InvalidMarkerGeometry, match="center"):
        classify_marker(5, "MARKERS", 1, observation)


def test_zero_length_triangle_axis_is_unknown() -> None:
    result = classify_marker(12, "MARKERS", 1, zero_axis_triangle())
    assert result.marker_type == "unknown"
    assert "ZERO_LENGTH_AXIS" in result.warnings
```

- [ ] **Step 2: Run and verify RED**

Run:

```powershell
& $env:WELD_AGENT_PYTHONOCC_PYTHON -m pytest tests/test_marker_identification.py -v
```

Expected: FAIL with `ModuleNotFoundError` for the new module.

- [ ] **Step 3: Implement immutable observations and deterministic rules**

Use frozen dataclasses and these field contracts:

```python
@dataclass(frozen=True)
class FaceObservation:
    surface_type: str
    edge_count: int
    centroid: Vector3 | None
    axis: Vector3 | None


@dataclass(frozen=True)
class SolidObservation:
    center: Vector3
    bbox: BBox
    volume: float
    faces: tuple[FaceObservation, ...]


@dataclass(frozen=True)
class MarkerRecord:
    marker_id: str
    component_id: int
    component_name: str
    solid_index: int
    marker_type: Literal["cylinder", "triangular_prism", "unknown"]
    center: Vector3
    axis: Vector3 | None
    bbox: BBox
    dimensions: Vector3
    volume: float
    evidence: dict[str, object]
    warnings: tuple[str, ...]
```

Classification order is cylinder, triangular prism, unknown. A cylinder requires at least one cylindrical Face with a finite non-zero axis and exactly two planar end Faces. A triangular prism requires five planar Faces, exactly two three-edge end Faces, and distinct end centroids. Normalize axis signs deterministically by making the largest-magnitude component positive. Generate IDs as `C{component_id:06d}-S{solid_index:06d}`. Reject non-finite center, bbox, volume, or reversed bbox with `InvalidMarkerGeometry`; unsupported but finite topology becomes `unknown`.

- [ ] **Step 4: Run classifier tests and refactor without changing behavior**

Run:

```powershell
& $env:WELD_AGENT_PYTHONOCC_PYTHON -m pytest tests/test_marker_identification.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit the classifier**

```powershell
git add src/weld_agent/geometry/marker_identification.py tests/test_marker_identification.py
git commit -m "feat: classify explicit weld marker solids"
```

---

### Task 3: Convert STEP Geometry into Marker Observations

**Files:**
- Create: `src/weld_agent/geometry/occ_marker_reader.py`
- Create: `tests/test_occ_marker_reader.py`

**Interfaces:**
- Consumes: `SolidObservation` and `FaceObservation` from Task 2.
- Produces: `MarkerStepReader` protocol and `PythonOccMarkerReader.read(path: Path) -> tuple[SolidObservation, ...]`.

- [ ] **Step 1: Write generated-geometry integration tests**

Use OCC to write temporary STEP files. Build the triangle with `BRepBuilderAPI_MakePolygon`, `BRepBuilderAPI_MakeFace`, and `BRepPrimAPI_MakePrism`. Assert:

```python
@pytest.mark.occ_integration
def test_reader_extracts_cylinder_observation(tmp_path: Path) -> None:
    path = write_step(tmp_path / "cylinder.step", BRepPrimAPI_MakeCylinder(3, 6).Shape())
    observations = PythonOccMarkerReader().read(path)
    assert len(observations) == 1
    assert any(face.surface_type == "cylinder" for face in observations[0].faces)
    assert classify_marker(5, "MARKERS", 1, observations[0]).marker_type == "cylinder"


@pytest.mark.occ_integration
def test_reader_extracts_triangular_prism_observation(tmp_path: Path) -> None:
    path = write_step(tmp_path / "triangle.step", make_triangular_prism())
    observation = PythonOccMarkerReader().read(path)[0]
    assert classify_marker(12, "MARKERS", 1, observation).marker_type == "triangular_prism"


@pytest.mark.occ_integration
def test_reader_keeps_box_as_unknown(tmp_path: Path) -> None:
    path = write_step(tmp_path / "box.step", BRepPrimAPI_MakeBox(6, 6, 6).Shape())
    observation = PythonOccMarkerReader().read(path)[0]
    assert classify_marker(12, "MARKERS", 1, observation).marker_type == "unknown"
```

Also test missing, invalid, and no-Solid STEP files with classified `MarkerStepReadError` codes `STEP_READ_FAILED` and `EMPTY_IMPORTED_SHAPE`.

- [ ] **Step 2: Run and verify RED**

Run:

```powershell
& $env:WELD_AGENT_PYTHONOCC_PYTHON -m pytest tests/test_occ_marker_reader.py -v
```

Expected: FAIL because `occ_marker_reader` is missing.

- [ ] **Step 3: Implement the reader**

Read with `STEPControl_Reader`, iterate `TopAbs_SOLID`, and for every Solid:

- calculate volume centroid with `brepgprop.VolumeProperties`;
- calculate an optimal finite bbox with `brepbndlib.AddOptimal`;
- iterate Faces and map `GeomAbs_Plane` to `plane`, `GeomAbs_Cylinder` to `cylinder`, and all other types to stable lowercase names;
- count unique topological edges with `TopExp_Explorer`;
- calculate planar Face centroids with `brepgprop.SurfaceProperties`;
- extract cylinder axes with `BRepAdaptor_Surface(face, True).Cylinder().Axis().Direction()`;
- preserve STEP explorer order and return a tuple.

Expose OCC version as a read-only `occ_version` property. Do not import PyQt5 or `OCC.Display`.

- [ ] **Step 4: Run integration and existing STEP tests**

Run:

```powershell
& $env:WELD_AGENT_PYTHONOCC_PYTHON -m pytest tests/test_occ_marker_reader.py tests/test_step_inspector.py -v
```

Expected: PASS without opening a window.

- [ ] **Step 5: Commit the OCC adapter**

```powershell
git add src/weld_agent/geometry/occ_marker_reader.py tests/test_occ_marker_reader.py
git commit -m "feat: read weld marker observations from STEP"
```

---

### Task 4: Orchestrate Identification and Write Auditable Artifacts

**Files:**
- Create: `src/weld_agent/marker_identification.py`
- Create: `tests/test_marker_identification_workflow.py`

**Interfaces:**
- Consumes: marker manifest contract, `MarkerStepReader`, `classify_marker`, and `validate_document`.
- Produces: `IdentificationArtifacts`, `MarkerIdentificationError`, and `identify_weld_markers(manifest_path, reader, emit) -> IdentificationArtifacts`.

- [ ] **Step 1: Write failing workflow tests using a fake reader**

Cover deterministic ordering, progress, JSON/CSV agreement, SHA-256, output conflict, missing STEP, and invalid geometry. The central success assertion is:

```python
artifacts = identify_weld_markers(manifest_path, FakeReader(observations), messages.append)
payload = json.loads(artifacts.json_path.read_text(encoding="utf-8"))
rows = list(csv.DictReader(artifacts.csv_path.open(encoding="utf-8", newline="")))

assert messages == [
    "[1/4] 检查 PythonOCC 运行环境",
    "[2/4] 读取焊点 Component STEP",
    "[3/4] 识别焊点标记",
    "[4/4] 写入识别结果",
]
assert [item["marker_id"] for item in payload["markers"]] == [
    "C000005-S000001",
    "C000012-S000001",
]
assert len(rows) == payload["summary"]["marker_count"] == 2
assert artifacts.json_path.parent.name == "marker-identification"
```

Verify that a pre-existing `weld-markers.json` raises `MarkerIdentificationError("OUTPUT_CONFLICT", ...)`, a missing STEP raises `STEP_READ_FAILED`, non-mm input raises `UNIT_MISMATCH`, and no observations raises `EMPTY_IMPORTED_SHAPE`.

- [ ] **Step 2: Run and verify RED**

Run:

```powershell
& $env:WELD_AGENT_PYTHONOCC_PYTHON -m pytest tests/test_marker_identification_workflow.py -v
```

Expected: FAIL because the orchestration module is missing.

- [ ] **Step 3: Implement orchestration and atomic writers**

Use these public types:

```python
@dataclass(frozen=True)
class IdentificationArtifacts:
    json_path: Path
    csv_path: Path
    log_path: Path


class MarkerIdentificationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
```

Resolve and validate the manifest, require each STEP to exist, call the reader in manifest order, classify Solids with one-based indices, sort by `(component_id, solid_index)`, validate the final payload against `weld-markers.schema.json`, and write all three files into `manifest_path.resolve().parent / "marker-identification"`. Write JSON, CSV, and log to sibling `.tmp` files and call `os.replace` only after each stream closes successfully. The log contains the same four progress messages plus the final counts and paths. Use `time.perf_counter_ns()` for elapsed milliseconds and SHA-256 the manifest bytes.

Translate adapter and geometry exceptions into the exact error codes from the approved specification. Do not catch `KeyboardInterrupt` or `SystemExit`.

- [ ] **Step 4: Run workflow and contract tests**

Run:

```powershell
& $env:WELD_AGENT_PYTHONOCC_PYTHON -m pytest tests/test_marker_identification_workflow.py tests/test_marker_contracts.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit the auditable workflow**

```powershell
git add src/weld_agent/marker_identification.py tests/test_marker_identification_workflow.py
git commit -m "feat: write auditable weld marker results"
```

---

### Task 5: Add the Visible CLI and PowerShell Entry Point

**Files:**
- Modify: `src/weld_agent/cli.py`
- Create: `tests/test_marker_identification_cli.py`
- Create: `scripts/identify_weld_markers.ps1`
- Create: `tests/test_identify_weld_markers_script.py`

**Interfaces:**
- Consumes: `identify_weld_markers` and `PythonOccMarkerReader`.
- Produces: `python -m weld_agent.cli identify-markers --manifest PATH` and `.\scripts\identify_weld_markers.ps1 -InputManifest PATH`.

- [ ] **Step 1: Write failing CLI tests**

Test dispatch by monkeypatching the workflow and asserting that four stage messages plus a concise summary are printed. Test classified failure:

```python
def test_identify_markers_reports_classified_failure(monkeypatch, capsys, tmp_path) -> None:
    def fail(*args, **kwargs):
        raise MarkerIdentificationError("STEP_READ_FAILED", "missing component-5.step")

    monkeypatch.setattr("weld_agent.cli.identify_weld_markers", fail)
    code = main(["identify-markers", "--manifest", str(tmp_path / "input.json")])
    assert code == 2
    assert "error: STEP_READ_FAILED: missing component-5.step" in capsys.readouterr().err
```

Test the PowerShell wrapper with `-PythonOccPython C:\definitely-missing\python.exe` and assert a non-zero exit plus `PythonOCC interpreter not found`.

- [ ] **Step 2: Run and verify RED**

Run:

```powershell
& $env:WELD_AGENT_PYTHONOCC_PYTHON -m pytest tests/test_marker_identification_cli.py tests/test_identify_weld_markers_script.py -v
```

Expected: FAIL because the command and wrapper do not exist.

- [ ] **Step 3: Add the CLI subcommand and wrapper**

The parser receives:

```python
identify = subparsers.add_parser("identify-markers")
identify.add_argument("--manifest", type=Path, required=True)
```

Dispatch with `PythonOccMarkerReader()`, pass `print` as the progress emitter, and print only final counts and artifact paths after success. Catch `MarkerIdentificationError` and `MarkerStepReadError` alongside existing classified exceptions.

The PowerShell script uses this exact parameter boundary:

```powershell
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InputManifest,
    [string]$PythonOccPython = ""
)
```

It reads `WELD_AGENT_PYTHONOCC_PYTHON` only when `-PythonOccPython` is empty, validates both paths, resolves them, changes to the repository root with `Push-Location`, invokes:

```powershell
& $PythonOccPython -m weld_agent.cli identify-markers --manifest $InputManifest
```

and throws when `$LASTEXITCODE` is non-zero. It must not call `Start-Process`, redirect output, or launch a GUI.

- [ ] **Step 4: Run CLI and wrapper tests**

Run:

```powershell
& $env:WELD_AGENT_PYTHONOCC_PYTHON -m pytest tests/test_marker_identification_cli.py tests/test_identify_weld_markers_script.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit the user-visible entry point**

```powershell
git add src/weld_agent/cli.py tests/test_marker_identification_cli.py scripts/identify_weld_markers.ps1 tests/test_identify_weld_markers_script.py
git commit -m "feat: add terminal weld marker command"
```

---

### Task 6: Document and Reproduce the Current Car-Door Baseline

**Files:**
- Create: `docs/manual-tests/terminal-weld-marker-identification.md`
- Modify: `README.md`
- Modify: `docs/setup.md`
- Modify: `tests/test_package.py`

**Interfaces:**
- Consumes: the five existing local `(SW)` STEP exports and a local, untracked `marker-input-manifest.json`.
- Produces: a reproducible operator runbook and the verified 122/83/39 regression record without committing CAD.

- [ ] **Step 1: Write documentation assertions before documentation changes**

Add a lightweight test to `tests/test_package.py` that requires the README to contain `identify_weld_markers.ps1`, `marker-input-manifest.json`, and the statement that the command does not open OCC GUI. Run it and observe failure before editing the documents.

- [ ] **Step 2: Run and verify RED**

Run:

```powershell
& $env:WELD_AGENT_PYTHONOCC_PYTHON -m pytest tests/test_package.py -v
```

Expected: FAIL because the README does not yet describe the command.

- [ ] **Step 3: Add the operator runbook and verification hook**

Document:

1. how to set `WELD_AGENT_PYTHONOCC_PYTHON`;
2. how to provide the exact local manifest path;
3. the single PowerShell command;
4. the four progress stages;
5. JSON/CSV/log locations;
6. the fact that this stage only classifies explicit markers in five selected small Components;
7. how `OUTPUT_CONFLICT` is resolved by using a new run directory rather than overwriting results.

State explicitly that `scripts/verify.ps1` already discovers all new tests through its unfiltered `pytest` invocation. Do not add a customer-data test to automated CI.

- [ ] **Step 4: Run the complete automated verification**

Run:

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

Expected: every pytest test passes, runtime doctor reports Python 3.11 and OCC 7.9.0, contract validation passes, and `git diff --check` passes.

- [ ] **Step 5: Run the local car-door acceptance command**

Use a local, untracked manifest containing Components 5, 8, 12, 13, and 21 and pointing at the five previously exported STEP files. Obtain its exact path visibly in the terminal and run:

```powershell
$manifestPath = Read-Host 'Paste marker-input-manifest.json path'
.\scripts\identify_weld_markers.ps1 -InputManifest $manifestPath
```

Expected terminal summary:

```text
component_count       5
marker_count        122
cylinder_marker      83
triangular_marker    39
unknown_marker        0
```

Open the generated JSON and CSV with read-only commands, confirm every marker has Component and Solid identity, and record the run ID and counts in the manual-test document. Do not add the manifest, STEP, JSON, CSV, or log to Git.

- [ ] **Step 6: Commit documentation and the verified boundary**

```powershell
git add README.md docs/setup.md docs/manual-tests/terminal-weld-marker-identification.md tests/test_package.py
git commit -m "docs: add terminal weld marker runbook"
```

---

## Plan Self-Review Checklist

- Every approved specification requirement maps to a task above.
- The existing two-Component `export-manifest.json` contract remains unchanged.
- OCC types stop at `occ_marker_reader.py`; classifier and workflow tests remain GUI-free.
- Unknown topology remains visible and is never coerced into a known type.
- No task performs 2T/3T validation, welding-face recognition, full-door scanning, or Connector creation.
- No customer CAD or local interpreter path is added to a commit.
- Every production change has a preceding failing test and an explicit verification command.
