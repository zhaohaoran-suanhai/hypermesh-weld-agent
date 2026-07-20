# Repository Rules

- Keep this repository independent from `fluent-automation`.
- Use Python 3.11 and keep geometry providers behind the `CandidateProvider` protocol.
- Never commit customer CAD, HyperMesh models, temporary exports, or local interpreter paths.
- Treat candidate generation as advisory; only explicit user actions may create formal connectors.
- Set `WELD_AGENT_PYTHONOCC_PYTHON` to the local OCC interpreter, then run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` before claiming completion.
