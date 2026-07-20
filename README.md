# HyperMesh Weld Agent

Human-reviewed spot-weld candidate workflow for HyperMesh 2017.

The current implementation supports a verified two-Component STEP export input path for HyperMesh 2017, plus contracts, runtime checks, and a deterministic test provider. It does not claim to identify real welds and does not create or realize HyperMesh connectors.

See [the approved design](docs/superpowers/specs/2026-07-20-hypermesh-weld-agent-design.md).
The export boundary is specified in the [STEP export probe design](docs/superpowers/specs/2026-07-20-hypermesh-step-export-probe-design.md).

## Development

- [Local setup](docs/setup.md)
- [HyperMesh 2017 capability probe](docs/manual-tests/hm2017-capability-probe.md)
- [HyperMesh 2017 STEP export probe](docs/manual-tests/hm2017-step-export-probe.md)

Run all local checks with:

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

## Current boundary

The repository now provides versioned contracts, a PythonOCC STEP inspector, a non-destructive HyperMesh export adapter, export validation, and a deterministic test provider. Real weld geometry analysis, preview entities, Connector creation, and Agent orchestration remain later stages.
