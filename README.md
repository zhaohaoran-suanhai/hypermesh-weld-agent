# HyperMesh Weld Agent

Human-reviewed spot-weld candidate workflow for HyperMesh 2017.

The current implementation stage builds contracts, runtime checks, and a deterministic test provider. It does not claim to identify real welds and does not create or realize HyperMesh connectors.

See [the approved design](docs/superpowers/specs/2026-07-20-hypermesh-weld-agent-design.md).

## Development

- [Local setup](docs/setup.md)
- [HyperMesh 2017 capability probe](docs/manual-tests/hm2017-capability-probe.md)

Run all local checks with:

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

## Current boundary

Stage 0 provides repository structure, versioned contracts, a PythonOCC runtime interface, a HyperMesh capability interface, and a deterministic test provider. Real geometry analysis, preview entities, Connector creation, and Agent orchestration remain later stages.
