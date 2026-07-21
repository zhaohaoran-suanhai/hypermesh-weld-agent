# Repository Knowledge Base Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Chinese-first, repository-owned knowledge base that lets a new Codex conversation or human developer operate the verified local HyperMesh 2017 + PythonOCC toolchain and extend the integration beyond weld-marker work without relying on chat history.

**Architecture:** `README.md` and `AGENTS.md` form the common entry point; `docs/current-state.md` is the sole maintained status source; stable architecture, domain, development, and integration documents each own one class of facts. ADRs record durable decisions, runbooks retain reproducible evidence, and historical specs/plans are explicitly separated from current truth. Lightweight pytest checks enforce structure, critical safety statements, maintained-document links, and the absence of private interpreter paths.

**Tech Stack:** Markdown, Python 3.11, pytest, PowerShell 5.1, HyperMesh/HyperWorks 2017 Tcl, PythonOCC/OpenCascade 7.9.0, JSON Schema Draft 2020-12.

## Global Constraints

- Work directly on `main`; do not create a worktree or couple this repository to `fluent-automation`.
- Use Chinese prose while retaining English file names, code symbols, commands, Schema fields, error codes, and product names.
- Do not modify Python production behavior, geometry algorithms, HyperMesh Tcl, CLI, Schema, customer data, or existing run results.
- Never commit customer CAD, `.hm`, STEP/IGES exports, temporary manifests, run artifacts, or a private `C:\Users\...\python.exe` path.
- Document the verified HyperWorks installation under `C:\Program Files\Altair\2017` and reference PythonOCC through `WELD_AGENT_PYTHONOCC_PYTHON` plus the repository-relative path `..\pythonocc\.m\envs\occ\python.exe`.
- Treat specs and plans as historical records; current facts come from code, fresh verification, and `docs/current-state.md`.
- Any formal Connector creation remains blocked until the user explicitly approves it.
- Run `scripts/verify.ps1` with `WELD_AGENT_PYTHONOCC_PYTHON` before claiming completion.

---

## File Map

- `README.md`: concise project overview and common human/Codex entry point.
- `AGENTS.md`: mandatory reading order, safety rules, truth precedence, documentation update matrix, and definition of done.
- `docs/index.md`: route questions to maintained knowledge, runbooks, decisions, or historical records.
- `docs/current-state.md`: sole current-state source for verified capabilities, evidence, limitations, and open questions.
- `docs/architecture.md`: actual module boundaries, contracts, and current data flows.
- `docs/domain-model.md`: distinguish HyperMesh entities, CAD marker geometry, engineering semantics, candidates, and Connectors.
- `docs/development.md`: common setup, test, commit, and data-handling workflow.
- `docs/integrations/local-environment.md`: verified local executables, versions, environment variables, and probes.
- `docs/integrations/hypermesh-2017.md`: GUI/Tcl/batch usage, verified commands, state protection, and extension rules.
- `docs/integrations/pythonocc.md`: external OCC runtime, adapters/protocols, headless tests, and debugging.
- `docs/integrations/hypermesh-occ-bridge.md`: reusable STEP + JSON process/file boundary and non-weld extension checklist.
- `docs/roadmap.md`: completed, approved, and merely proposed work kept explicitly separate.
- `docs/decisions/README.md`: ADR index and policy.
- `docs/decisions/0001-terminal-first-independent-repository.md`: repository and terminal-first decision.
- `docs/decisions/0002-pythonocc-headless-geometry-kernel.md`: headless OCC decision.
- `docs/decisions/0003-explicit-cad-markers-first.md`: explicit-marker-first decision.
- `docs/decisions/0004-user-approved-connectors.md`: Connector authorization decision.
- `docs/manual-tests/README.md`: current manual verification index.
- `docs/superpowers/README.md`: historical-record warning and index.
- `docs/superpowers/specs/README.md`: approved-design chronology and current-status warning.
- `docs/superpowers/plans/README.md`: implementation-plan chronology and current-status warning.
- `docs/setup.md`: compatibility redirect to maintained environment documents.
- `tests/test_documentation.py`: structural, safety, integration-fact, and relative-link tests.
- `tests/test_package.py`: package-version test only after documentation assertions move to the dedicated suite.

---

### Task 1: Establish the Common Entry Point and Current Knowledge

**Files:**
- Create: `tests/test_documentation.py`
- Modify: `tests/test_package.py`
- Rewrite: `README.md`
- Rewrite: `AGENTS.md`
- Create: `docs/index.md`
- Create: `docs/current-state.md`
- Create: `docs/architecture.md`
- Create: `docs/domain-model.md`

**Interfaces:**
- Consumes: current source modules, schemas, existing runbooks, and the verified 122/83/39 car-door result.
- Produces: a common reading path and stable current-truth documents used by every later task.

- [ ] **Step 1: Write failing entry and current-state tests**

Create `tests/test_documentation.py` with:

```python
import re
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_common_entry_points_define_the_same_reading_path() -> None:
    for relative in ("README.md", "AGENTS.md", "docs/index.md"):
        text = read(relative)
        assert "docs/current-state.md" in text
        assert "docs/architecture.md" in text
        assert "docs/integrations/" in text


def test_current_state_separates_capability_evidence_and_limits() -> None:
    text = read("docs/current-state.md")
    for heading in ("## 已验证能力", "## 验证证据", "## 当前限制", "## 开放问题"):
        assert heading in text
    for fact in ("122", "83", "39", "unknown", "2T", "3T"):
        assert fact in text
    assert "默认开发任务" in text


def test_architecture_explains_actual_process_and_contract_boundaries() -> None:
    text = read("docs/architecture.md")
    for fact in (
        "HyperMesh Tcl",
        "STEP",
        "JSON",
        "PythonOCC",
        "src/weld_agent/geometry/",
        "schemas/",
        "JSON/CSV/log",
    ):
        assert fact in text


def test_domain_model_does_not_confuse_geometry_with_engineering_semantics() -> None:
    text = read("docs/domain-model.md")
    assert "cylinder" in text
    assert "triangular_prism" in text
    assert "几何事实" in text
    assert "工程语义" in text
    assert "不能单独证明" in text
    assert "Connector" in text
```

Modify `tests/test_package.py` so it contains only:

```python
from weld_agent import __version__


def test_package_version_is_explicit() -> None:
    assert __version__ == "0.1.0"
```

- [ ] **Step 2: Run the documentation tests and verify RED**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_documentation.py tests/test_package.py -v
```

Expected: FAIL because `docs/index.md`, `docs/current-state.md`, `docs/architecture.md`, and `docs/domain-model.md` do not exist and the old entry documents do not define the new reading path.

- [ ] **Step 3: Write the common entry documents**

Rewrite `README.md` with these exact top-level sections:

```markdown
# HyperMesh Weld Agent
## 从这里开始
## 当前能力摘要
## 本机快速验证
## 安全边界
## 文档地图
```

The opening must describe the repository as a reusable HyperMesh 2017 + geometry automation foundation whose first validated application is explicit weld-marker identification. Link `AGENTS.md`, `docs/current-state.md`, `docs/architecture.md`, `docs/integrations/`, and `docs/index.md`. Keep one short `verify.ps1` command using `WELD_AGENT_PYTHONOCC_PYTHON`; move detailed setup elsewhere.

Rewrite `AGENTS.md` with these exact sections:

```markdown
# Repository Rules
## 必读顺序
## 事实优先级
## 开发与安全边界
## 文档更新矩阵
## 完成定义
```

The reading order is README → AGENTS → current-state → architecture → relevant integration document. State that customer models and private interpreter paths are forbidden, current code/fresh verification outrank historical plans, HyperMesh model writes and Connector creation require explicit authority, and relevant knowledge documents must change with behavior.

Create `docs/index.md` with routes for: current status, HyperMesh/OCC integration, architecture/contracts, domain semantics, development/testing, manual verification, ADRs, and historical specs/plans.

- [ ] **Step 4: Write current state, architecture, and domain model**

Create `docs/current-state.md` using the headings asserted by the test. It must state:

- verified capabilities: HM2017 capability probe, isolated STEP export, external OCC reading, explicit Solid-marker classification, terminal artifacts;
- evidence: 5 selected Components, 122 total, 83 cylinder, 39 triangular prism, 0 unknown, linked to `manual-tests/terminal-weld-marker-identification.md`;
- limitations: no full-door discovery, no weld-face/2T/3T proof, no new marker generation, no Connector creation;
- open questions: examples only, explicitly saying they are not the default development task.

Create `docs/architecture.md` with:

```text
HyperMesh 2017 / Tcl
  -> STEP + JSON manifest in unique temporary run directory
  -> Schema validation
  -> PythonOCC adapter
  -> plain-Python domain workflow
  -> JSON/CSV/log
  -> human review / separately authorized HyperMesh write-back
```

Add a module table for `hypermesh/tcl/`, `schemas/`, `src/weld_agent/geometry/`, workflow modules, `scripts/`, and `tests/`. Document both existing flows: two-Component export finalization and multi-Component marker identification.

Create `docs/domain-model.md` defining Model, Component, Surface/Face, Solid, explicit marker, cylinder, triangular prism, candidate, welding face, 2T/3T, Connector, and Realize. Put geometry facts and engineering semantics in separate columns and state that one cannot be inferred from the other without additional plate-intersection evidence.

- [ ] **Step 5: Run tests and commit the maintained core**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_documentation.py tests/test_package.py -v
git diff --check
```

Expected: all selected tests PASS and `git diff --check` exits 0.

Commit:

```powershell
git add README.md AGENTS.md docs/index.md docs/current-state.md docs/architecture.md docs/domain-model.md tests/test_documentation.py tests/test_package.py
git commit -m "docs: add common repository knowledge entry"
```

---

### Task 2: Document the Verified Local HyperMesh and PythonOCC Platform

**Files:**
- Modify: `tests/test_documentation.py`
- Create: `docs/development.md`
- Create: `docs/integrations/local-environment.md`
- Create: `docs/integrations/hypermesh-2017.md`
- Create: `docs/integrations/pythonocc.md`
- Create: `docs/integrations/hypermesh-occ-bridge.md`
- Rewrite: `docs/setup.md`

**Interfaces:**
- Consumes: `weld_agent_probe.tcl`, `weld_agent_export.tcl`, `StepInspector`, `MarkerStepReader`, `CandidateProvider`, CLI commands, wrapper scripts, and verified local executables.
- Produces: the reusable machine/tool interface handbook for weld and non-weld HyperMesh development.

- [ ] **Step 1: Add failing integration-document tests**

Append to `tests/test_documentation.py`:

```python
INTEGRATION_FACTS = {
    "docs/integrations/local-environment.md": (
        "C:\\Program Files\\Altair\\2017",
        "hmopengl.exe",
        "hmbatch.exe",
        "Python 3.11.15",
        "OCC 7.9.0",
        "WELD_AGENT_PYTHONOCC_PYTHON",
    ),
    "docs/integrations/hypermesh-2017.md": (
        "Tcl Console",
        "source",
        "::weldagent",
        "hm_getvalue",
        "hm_getboundingbox",
        "*geomexport",
        "状态恢复",
    ),
    "docs/integrations/pythonocc.md": (
        "StepInspector",
        "MarkerStepReader",
        "CandidateProvider",
        "OCC.Display",
        "pytest",
    ),
    "docs/integrations/hypermesh-occ-bridge.md": (
        "STEP + JSON",
        "Schema",
        "临时运行目录",
        "新增非焊点功能",
        "人工复核",
    ),
}


def test_integration_documents_record_verified_local_interfaces() -> None:
    for relative, facts in INTEGRATION_FACTS.items():
        text = read(relative)
        for fact in facts:
            assert fact in text, f"{relative} must contain {fact}"


def test_maintained_documents_do_not_embed_private_python_path() -> None:
    maintained = (
        "README.md",
        "AGENTS.md",
        "docs/current-state.md",
        "docs/architecture.md",
        "docs/development.md",
        *INTEGRATION_FACTS,
    )
    for relative in maintained:
        assert "C:\\Users\\" not in read(relative)
```

- [ ] **Step 2: Run the integration tests and verify RED**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_documentation.py -v
```

Expected: FAIL because the integration documents do not exist.

- [ ] **Step 3: Write the local environment and development guides**

Create `docs/integrations/local-environment.md` with:

- verified Windows/HyperWorks 2017 root and GUI/batch/HyperWorks executable table;
- repository-relative PythonOCC path and environment-variable setup;
- read-only PowerShell probes for executable existence, Python version, `OCC.VERSION`, and project `doctor`;
- a note distinguishing verified machine facts from portable repository requirements;
- troubleshooting for missing interpreter, missing license/start failure, wrong working directory, and stale `%TEMP%` run directories.

Create `docs/development.md` with setup, editable install, focused pytest, full verify, Git checks, synthetic OCC test strategy, HyperMesh manual-test strategy, and prohibited-data rules. The canonical full check is:

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

Rewrite `docs/setup.md` as a short compatibility page linking to `development.md`, `integrations/local-environment.md`, `integrations/hypermesh-2017.md`, and `integrations/pythonocc.md`; do not duplicate commands beyond the single environment-variable example.

- [ ] **Step 4: Write the HyperMesh, OCC, and bridge interface guides**

Create `docs/integrations/hypermesh-2017.md` with:

- GUI launch, Tcl Console workflow, and a `source {<repo>/hypermesh/tcl/...}` example using a placeholder rather than a private user path;
- `hmopengl.exe` versus `hmbatch.exe` usage and the rule that existing interactive scripts cannot be assumed batch-safe without a dedicated test;
- verified query/modify commands and current proc table for both Tcl files;
- mark IDs, component summary, display isolation, STEP AP214/mm export, unique run directory, error propagation, and `catch`/restore behavior;
- script conventions: `::weldagent` namespace, explicit proc arguments, classified errors, no hidden save, no unauthorized Connector creation;
- a safe extension checklist for a new HyperMesh operation.

Create `docs/integrations/pythonocc.md` with environment setup, `doctor`, imports, no-GUI rule, adapter/protocol table, synthetic-shape tests, STEP error vocabulary, and the boundary that OCC types stop at the geometry adapter.

Create `docs/integrations/hypermesh-occ-bridge.md` with the full process diagram from the approved spec, file ownership table, existing Schema map, unique-run-directory rule, failure/atomic-write behavior, and this extension sequence:

1. probe the HM2017 Tcl capability;
2. define a JSON Schema contract;
3. write a state-restoring namespaced Tcl adapter;
4. write an external Python/OCC adapter returning plain Python data;
5. implement the domain workflow;
6. test with synthetic geometry and fake adapters;
7. add a real HyperMesh runbook;
8. require explicit authorization for any model write-back.

- [ ] **Step 5: Run tests and commit the platform handbook**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_documentation.py -v
git diff --check
```

Expected: PASS.

Commit:

```powershell
git add docs/development.md docs/setup.md docs/integrations tests/test_documentation.py
git commit -m "docs: document local HyperMesh OCC integration"
```

---

### Task 3: Record Decisions and Separate Maintained Knowledge from History

**Files:**
- Modify: `tests/test_documentation.py`
- Create: `docs/roadmap.md`
- Create: `docs/decisions/README.md`
- Create: `docs/decisions/0001-terminal-first-independent-repository.md`
- Create: `docs/decisions/0002-pythonocc-headless-geometry-kernel.md`
- Create: `docs/decisions/0003-explicit-cad-markers-first.md`
- Create: `docs/decisions/0004-user-approved-connectors.md`
- Create: `docs/manual-tests/README.md`
- Create: `docs/superpowers/README.md`
- Create: `docs/superpowers/specs/README.md`
- Create: `docs/superpowers/plans/README.md`

**Interfaces:**
- Consumes: approved designs, implemented commits, current runbooks, and repository safety rules.
- Produces: durable decision rationale and explicit history/current-truth separation.

- [ ] **Step 1: Add failing ADR, history-index, and link tests**

Append to `tests/test_documentation.py`:

```python
ADR_FILES = (
    "docs/decisions/0001-terminal-first-independent-repository.md",
    "docs/decisions/0002-pythonocc-headless-geometry-kernel.md",
    "docs/decisions/0003-explicit-cad-markers-first.md",
    "docs/decisions/0004-user-approved-connectors.md",
)


def test_adrs_have_required_structure_and_are_indexed() -> None:
    index = read("docs/decisions/README.md")
    for relative in ADR_FILES:
        text = read(relative)
        for heading in ("## Status", "## Context", "## Decision", "## Consequences"):
            assert heading in text
        assert Path(relative).name in index


def test_historical_directories_warn_that_they_are_not_current_truth() -> None:
    for relative in (
        "docs/superpowers/README.md",
        "docs/superpowers/specs/README.md",
        "docs/superpowers/plans/README.md",
    ):
        text = read(relative)
        assert "历史" in text
        assert "docs/current-state.md" in text


def maintained_markdown_files() -> list[Path]:
    files = [ROOT / "README.md", ROOT / "AGENTS.md"]
    files.extend(path for path in (ROOT / "docs").glob("*.md"))
    files.extend(path for path in (ROOT / "docs/integrations").glob("*.md"))
    files.extend(path for path in (ROOT / "docs/decisions").glob("*.md"))
    files.extend(path for path in (ROOT / "docs/manual-tests").glob("*.md"))
    files.extend(path for path in (ROOT / "docs/superpowers").glob("*.md"))
    files.extend(path for path in (ROOT / "docs/superpowers/specs").glob("README.md"))
    files.extend(path for path in (ROOT / "docs/superpowers/plans").glob("README.md"))
    return sorted(set(files))


def test_maintained_relative_markdown_links_exist() -> None:
    pattern = re.compile(r"\[[^]]+\]\(([^)]+)\)")
    failures: list[str] = []
    for document in maintained_markdown_files():
        for raw_target in pattern.findall(document.read_text(encoding="utf-8")):
            target = raw_target.strip("<>").split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            resolved = (document.parent / unquote(target)).resolve()
            if not resolved.exists():
                failures.append(f"{document.relative_to(ROOT)} -> {raw_target}")
    assert failures == []
```

- [ ] **Step 2: Run the decision/history tests and verify RED**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_documentation.py -v
```

Expected: FAIL because ADR and history-index files do not exist.

- [ ] **Step 3: Write ADRs and indexes**

Each ADR uses English headings `Status`, `Context`, `Decision`, `Consequences` and Chinese body text. Set Status to `Accepted`.

- ADR-0001: independent repository, terminal-visible versioned scripts, no coupling to `fluent-automation`.
- ADR-0002: external PythonOCC 7.9.0 as headless kernel; OCC types stay in adapters; GUI optional only for future debugging.
- ADR-0003: first validated application classifies explicit CAD marker Solids; it does not infer plate count or generate welds.
- ADR-0004: geometry results are advisory; preview/write-back/Connector creation require distinct interfaces and explicit user approval.

Create `docs/decisions/README.md` with the ADR policy and links. Create the three superpowers index files with a prominent warning that specs/plans are historical and `docs/current-state.md` is the status source. Create `docs/manual-tests/README.md` with links and a table describing capability probe, STEP export, and marker identification evidence.

- [ ] **Step 4: Write a non-directive roadmap**

Create `docs/roadmap.md` with three sections:

```markdown
## 已完成并验证
## 已批准但尚未实施
## 候选方向（未授权）
```

Put the current platform and marker classification under completed. If there is no approved unimplemented feature, state `当前没有已批准但尚未实施的功能阶段。` List plate-intersection/weld-face validation, generic HM batch execution, preview/write-back, and Agent orchestration only as candidate directions. State that repository handoff does not imply authorization to select one.

- [ ] **Step 5: Run tests and commit the decision/history layer**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_documentation.py -v
git diff --check
```

Expected: PASS with no broken maintained links.

Commit:

```powershell
git add docs/roadmap.md docs/decisions docs/manual-tests/README.md docs/superpowers/README.md docs/superpowers/specs/README.md docs/superpowers/plans/README.md tests/test_documentation.py
git commit -m "docs: record decisions and historical boundaries"
```

---

### Task 4: Verify the Knowledge Base as a Fresh Handoff

**Files:**
- Modify only if verification reveals an inconsistency: maintained Markdown files and `tests/test_documentation.py`.

**Interfaces:**
- Consumes: all knowledge documents from Tasks 1–3.
- Produces: fresh automated evidence that the repository is ready for a new Codex or human handoff.

- [ ] **Step 1: Run the dedicated knowledge tests**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_documentation.py -v
```

Expected: all documentation tests PASS.

- [ ] **Step 2: Perform the fresh-handoff content audit**

Read only `README.md`, `AGENTS.md`, `docs/current-state.md`, `docs/architecture.md`, and the four integration documents. Confirm those documents alone answer:

1. current reusable platform capability;
2. verified HyperMesh and OCC executables/versions;
3. GUI Tcl versus batch entry points;
4. STEP + JSON bridge and Schema responsibilities;
5. how to add a non-weld HyperMesh feature;
6. test and verification commands;
7. prohibited local/customer data;
8. why engineering semantics and Connector write-back require additional evidence/authority.

Record the audit in the final handoff; do not add a self-certification file that would immediately become stale.

- [ ] **Step 3: Run complete repository verification**

Run:

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

Expected: all pytest tests pass; runtime doctor reports Python 3.11.15 and OCC 7.9.0; Schema validation and `git diff --check` pass.

- [ ] **Step 4: Verify repository hygiene and commit any audit fixes**

Run:

```powershell
git status --short
git diff --check
git ls-files "*.hm" "*.step" "*.stp" "run-artifacts/*"
rg -n "C:\\\\Users\\\\.*python.exe" README.md AGENTS.md docs --glob "!docs/superpowers/**"
```

Expected: no customer geometry tracked, no private Python path in maintained docs, and no whitespace errors. If the audit required a documentation correction, commit only that correction with:

```powershell
git add README.md AGENTS.md docs tests/test_documentation.py
git commit -m "docs: complete knowledge base handoff audit"
```

If no audit fix was needed, do not create an empty commit.

---

## Plan Self-Review Checklist

- The common entry point serves both Codex and human developers.
- The plan documents HyperMesh GUI, Tcl, batch, external PythonOCC, and the file/process bridge independently of weld-marker work.
- `roadmap.md` does not select a default next feature.
- Current truth, durable decisions, runbook evidence, and historical design records have separate owners.
- Tests cover required structure, critical safety boundaries, maintained links, local integration facts, and private-path exclusion.
- No task changes algorithms, Tcl behavior, CLI behavior, schemas, customer data, or existing result artifacts.
- Every implementation task begins with a failing documentation test and ends with an independently reviewable commit.
