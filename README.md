# HyperMesh Weld Agent

Terminal-first, human-reviewed weld-marker workflow for HyperMesh 2017.

The current implementation can classify explicit marker solids from selected STEP Components as cylinders, triangular prisms, or unknown geometry. It also retains the verified two-Component STEP export path. It does not yet infer 2T/3T meaning, welding faces, or create HyperMesh Connectors.

See [the approved design](docs/superpowers/specs/2026-07-20-hypermesh-weld-agent-design.md).
The export boundary is specified in the [STEP export probe design](docs/superpowers/specs/2026-07-20-hypermesh-step-export-probe-design.md).

## Development

- [Local setup](docs/setup.md)
- [HyperMesh 2017 capability probe](docs/manual-tests/hm2017-capability-probe.md)
- [HyperMesh 2017 STEP export probe](docs/manual-tests/hm2017-step-export-probe.md)
- [Terminal weld-marker identification](docs/manual-tests/terminal-weld-marker-identification.md)

## Identify explicit weld markers

Prepare a local `marker-input-manifest.json` that lists the small STEP Components to inspect, then run from the repository root:

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
.\scripts\identify_weld_markers.ps1 -InputManifest 'C:\path\to\marker-input-manifest.json'
```

The command writes `weld-markers.json`, `weld-markers.csv`, and `identify-weld-markers.log` beside the manifest under `marker-identification`. OCC is used as a background geometry library: **不需要打开 OCC GUI**，也不会修改 HyperMesh 模型或创建 Connector。

Run all local checks with:

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

## Current boundary

This first marker-identification stage analyzes only explicitly listed small Components. Full-door discovery, 2T/3T validation, welding-face recognition, preview entities, Connector creation, and Agent orchestration remain later stages.
