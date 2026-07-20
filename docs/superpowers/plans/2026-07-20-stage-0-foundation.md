# Stage 0 Repository Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立一个与 `fluent-automation` 解耦、可测试的 Python/Tcl 基础仓库，冻结 JSON 合同，跑通测试候选工作流，验证本机 PythonOCC，并从 HyperMesh 2017 采集选择与导出能力信息。

**Architecture:** Python 包负责合同校验、运行目录、工作流和可替换候选提供器；HyperMesh Tcl 在本阶段只采集两个 Component 和命令能力，不创建预览或 Connector。所有跨进程数据使用版本化 JSON，阶段 1 将复用这些接口实现 CAD 导出和 HyperMesh 回写。

**Tech Stack:** Windows 10/PowerShell、Python 3.11、pytest、jsonschema、HyperMesh 2017 Tcl、现有 PythonOCC 运行时。

## Global Constraints

- 仓库路径固定为 `C:\Users\25335\Documents\GitHub\hypermesh-weld-agent`。
- 远程固定为 `git@github.com:zhaohaoran-suanhai/hypermesh-weld-agent.git`，默认分支为 `main`。
- 不导入、复制或运行 `C:\Users\25335\Documents\GitHub\fluent-automation` 中的任何代码。
- Python 版本要求为 `>=3.11,<3.12`。
- 本机 OCC 解释器通过命令参数或未纳入 Git 的环境变量发现；当前 checkout 可使用相对路径 `..\pythonocc\.m\envs\occ\python.exe`，不得把用户绝对路径写入源码或配置。
- 几何算法在本计划中由明确标记为测试用途的提供器代替，不得把测试候选描述为真实焊点识别结果。
- Agent、CAD 自动导出、HyperMesh 预览、Connector 创建和 Realize 均不属于本计划。
- 所有文件修改使用 UTF-8；路径处理必须支持空格和中文。
- 每个任务先写失败测试，再做最小实现，并在通过后独立提交。

---

## Planned File Map

```text
.github/workflows/tests.yml                       # 不依赖 OCC/HM 的基础 CI
.gitignore                                        # Python、本地配置和临时模型排除规则
AGENTS.md                                         # 仓库级约束
README.md                                         # 项目入口和阶段声明
pyproject.toml                                    # Python 包与测试配置
schemas/selection.schema.json                     # 两 Component 分析输入合同
schemas/weld-candidates.schema.json               # 候选结果合同
schemas/hypermesh-probe.schema.json               # HM2017 能力探针合同
src/weld_agent/__init__.py                        # 包版本
src/weld_agent/cli.py                             # analyze/doctor/validate 命令
src/weld_agent/contracts.py                       # JSON Schema 加载与校验
src/weld_agent/run_workspace.py                   # 唯一运行目录与定向清理
src/weld_agent/runtime.py                         # PythonOCC 解释器探针
src/weld_agent/workflow.py                        # 阶段 0 确定性工作流
src/weld_agent/providers/__init__.py               # 提供器包
src/weld_agent/providers/base.py                  # CandidateProvider 协议
src/weld_agent/providers/fixture.py               # 测试候选提供器
hypermesh/tcl/weld_agent_probe.tcl                # HM2017 选择与命令能力采集
tests/fixtures/selection.valid.json               # 有效输入样例
tests/fixtures/hypermesh_probe.valid.json         # HM 探针样例
tests/test_package.py                             # 包安装测试
tests/test_contracts.py                           # 合同测试
tests/test_run_workspace.py                       # 运行目录安全测试
tests/test_fixture_provider.py                    # 测试提供器测试
tests/test_workflow_cli.py                        # CLI 往返测试
tests/test_runtime.py                             # OCC 探针单元测试
tests/test_hypermesh_probe_contract.py            # HM 探针合同测试
scripts/verify.ps1                                # 本机统一验证入口
docs/setup.md                                     # 安装与本地配置
docs/manual-tests/hm2017-capability-probe.md      # HyperMesh 手工探针步骤
```

---

### Task 1: Package Skeleton and Repository Guardrails

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `AGENTS.md`
- Create: `src/weld_agent/__init__.py`
- Create: `tests/test_package.py`
- Create: `.github/workflows/tests.yml`

**Interfaces:**
- Consumes: Python 3.11 interpreter.
- Produces: importable package `weld_agent`, constant `weld_agent.__version__`, pytest configuration, dependency declaration.

- [ ] **Step 1: Write the failing package test**

```python
# tests/test_package.py
from weld_agent import __version__


def test_package_version_is_explicit() -> None:
    assert __version__ == "0.1.0"
```

- [ ] **Step 2: Run the test and verify the package is absent**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_package.py -v
```

Expected: collection fails with `ModuleNotFoundError: No module named 'weld_agent'`.

- [ ] **Step 3: Create the package metadata and minimal module**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=75", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "hypermesh-weld-agent"
version = "0.1.0"
description = "Human-reviewed spot-weld candidate workflow for HyperMesh 2017"
readme = "README.md"
requires-python = ">=3.11,<3.12"
dependencies = [
  "jsonschema>=4.23,<5",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3,<9",
  "pytest-cov>=6,<7",
]

[project.scripts]
hypermesh-weld-agent = "weld_agent.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers"
```

```python
# src/weld_agent/__init__.py
__version__ = "0.1.0"
```

```gitignore
# .gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
htmlcov/
.venv/
*.egg-info/
build/
dist/
.env.local
config.local.json
*.hm
*.step
*.stp
*.iges
*.igs
run-artifacts/
```

```markdown
<!-- AGENTS.md -->
# Repository Rules

- Keep this repository independent from `fluent-automation`.
- Use Python 3.11 and keep geometry providers behind the `CandidateProvider` protocol.
- Never commit customer CAD, HyperMesh models, temporary exports, or local interpreter paths.
- Treat candidate generation as advisory; only explicit user actions may create formal connectors.
- Set `WELD_AGENT_PYTHONOCC_PYTHON` to the local OCC interpreter, then run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` before claiming completion.
```

- [ ] **Step 4: Add a minimal README required by package metadata**

```markdown
# HyperMesh Weld Agent

Human-reviewed spot-weld candidate workflow for HyperMesh 2017.

The current implementation stage builds contracts, runtime checks, and a deterministic test provider. It does not claim to identify real welds and does not create or realize HyperMesh connectors.

See [the approved design](docs/superpowers/specs/2026-07-20-hypermesh-weld-agent-design.md).
```

- [ ] **Step 5: Install the package in the existing OCC interpreter**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pip install -e '.[dev]'
```

Expected: exit code 0 and an editable installation of `hypermesh-weld-agent==0.1.0`.

- [ ] **Step 6: Run the package test**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_package.py -v
```

Expected: `1 passed`.

- [ ] **Step 7: Add dependency-light CI**

```yaml
# .github/workflows/tests.yml
name: tests

on:
  push:
  pull_request:

jobs:
  unit:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install -e ".[dev]"
      - run: python -m pytest
```

- [ ] **Step 8: Commit the package skeleton**

```powershell
git add pyproject.toml .gitignore AGENTS.md README.md src/weld_agent/__init__.py tests/test_package.py .github/workflows/tests.yml
git commit -m "build: initialize standalone Python package"
```

---

### Task 2: Versioned JSON Contracts

**Files:**
- Create: `schemas/selection.schema.json`
- Create: `schemas/weld-candidates.schema.json`
- Create: `schemas/hypermesh-probe.schema.json`
- Create: `src/weld_agent/contracts.py`
- Create: `tests/fixtures/selection.valid.json`
- Create: `tests/fixtures/hypermesh_probe.valid.json`
- Create: `tests/test_contracts.py`
- Create: `tests/test_hypermesh_probe_contract.py`

**Interfaces:**
- Consumes: JSON-compatible `Mapping[str, Any]`.
- Produces: `validate_document(schema_name: str, payload: Mapping[str, Any]) -> None`, `load_document(path: Path, schema_name: str) -> dict[str, Any]`, `ContractValidationError`.

- [ ] **Step 1: Write failing contract tests**

```python
# tests/test_contracts.py
import json
from pathlib import Path

import pytest

from weld_agent.contracts import ContractValidationError, load_document, validate_document


FIXTURES = Path(__file__).parent / "fixtures"


def test_valid_selection_fixture_passes() -> None:
    payload = load_document(FIXTURES / "selection.valid.json", "selection.schema.json")
    assert payload["run_id"] == "run-001"
    assert [item["id"] for item in payload["components"]] == [9, 12]


def test_duplicate_component_ids_are_rejected() -> None:
    payload = json.loads((FIXTURES / "selection.valid.json").read_text(encoding="utf-8"))
    payload["components"][1]["id"] = payload["components"][0]["id"]
    with pytest.raises(ContractValidationError, match="distinct component IDs"):
        validate_document("selection.schema.json", payload)


def test_missing_units_are_rejected() -> None:
    payload = json.loads((FIXTURES / "selection.valid.json").read_text(encoding="utf-8"))
    del payload["hypermesh"]["units"]
    with pytest.raises(ContractValidationError, match="units"):
        validate_document("selection.schema.json", payload)
```

```python
# tests/test_hypermesh_probe_contract.py
from pathlib import Path

from weld_agent.contracts import load_document


def test_hypermesh_probe_fixture_passes() -> None:
    path = Path(__file__).parent / "fixtures" / "hypermesh_probe.valid.json"
    payload = load_document(path, "hypermesh-probe.schema.json")
    assert len(payload["selected_components"]) == 2
    assert isinstance(payload["capabilities"]["geomexport"], bool)
```

- [ ] **Step 2: Run tests and verify contract module is absent**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_contracts.py tests/test_hypermesh_probe_contract.py -v
```

Expected: collection fails because `weld_agent.contracts` does not exist.

- [ ] **Step 3: Create the selection schema**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://zhaohaoran-suanhai.github.io/hypermesh-weld-agent/selection.schema.json",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "run_id", "hypermesh", "components", "parameters"],
  "properties": {
    "schema_version": {"const": "1.0"},
    "run_id": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"},
    "hypermesh": {
      "type": "object",
      "additionalProperties": false,
      "required": ["build", "model_name", "units", "coordinate_system"],
      "properties": {
        "build": {"type": "string", "minLength": 1},
        "model_name": {"type": "string", "minLength": 1},
        "units": {"enum": ["mm", "m", "inch"]},
        "coordinate_system": {"type": "string", "minLength": 1}
      }
    },
    "components": {
      "type": "array",
      "minItems": 2,
      "maxItems": 2,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "name", "geometry", "summary"],
        "properties": {
          "id": {"type": "integer", "minimum": 1},
          "name": {"type": "string", "minLength": 1},
          "geometry": {
            "type": "object",
            "additionalProperties": false,
            "required": ["path", "format", "sha256"],
            "properties": {
              "path": {"type": "string", "minLength": 1},
              "format": {"enum": ["STEP", "IGES"]},
              "sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"}
            }
          },
          "summary": {
            "type": "object",
            "additionalProperties": false,
            "required": ["surface_count", "solid_count", "element_count", "bbox"],
            "properties": {
              "surface_count": {"type": "integer", "minimum": 0},
              "solid_count": {"type": "integer", "minimum": 0},
              "element_count": {"type": "integer", "minimum": 0},
              "bbox": {
                "type": "array",
                "minItems": 6,
                "maxItems": 6,
                "prefixItems": [
                  {"type": "number"}, {"type": "number"}, {"type": "number"},
                  {"type": "number"}, {"type": "number"}, {"type": "number"}
                ],
                "items": false
              }
            }
          }
        }
      }
    },
    "parameters": {
      "type": "object",
      "additionalProperties": false,
      "required": ["search_distance", "max_gap", "pitch", "end_offset", "edge_clearance", "rule_profile_version"],
      "properties": {
        "search_distance": {"type": "number", "exclusiveMinimum": 0},
        "max_gap": {"type": "number", "minimum": 0},
        "pitch": {"type": "number", "exclusiveMinimum": 0},
        "end_offset": {"type": "number", "minimum": 0},
        "edge_clearance": {"type": "number", "minimum": 0},
        "rule_profile_version": {"type": "string", "minLength": 1}
      }
    }
  }
}
```

- [ ] **Step 4: Create the candidate and probe schemas**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://zhaohaoran-suanhai.github.io/hypermesh-weld-agent/weld-candidates.schema.json",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "run_id", "status", "has_candidate_regions", "provider", "algorithm_version", "component_refs", "parameters", "elapsed_ms", "regions", "warnings", "errors"],
  "properties": {
    "schema_version": {"const": "1.0"},
    "run_id": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"},
    "status": {"enum": ["success", "failure"]},
    "has_candidate_regions": {"type": "boolean"},
    "provider": {"type": "string", "minLength": 1},
    "algorithm_version": {"type": "string", "minLength": 1},
    "component_refs": {
      "type": "array",
      "minItems": 2,
      "maxItems": 2,
      "items": {"type": "integer", "minimum": 1}
    },
    "parameters": {
      "type": "object",
      "additionalProperties": false,
      "required": ["search_distance", "max_gap", "pitch", "end_offset", "edge_clearance", "rule_profile_version"],
      "properties": {
        "search_distance": {"type": "number", "exclusiveMinimum": 0},
        "max_gap": {"type": "number", "minimum": 0},
        "pitch": {"type": "number", "exclusiveMinimum": 0},
        "end_offset": {"type": "number", "minimum": 0},
        "edge_clearance": {"type": "number", "minimum": 0},
        "rule_profile_version": {"type": "string", "minLength": 1}
      }
    },
    "elapsed_ms": {"type": "integer", "minimum": 0},
    "regions": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "risk_flags", "candidates"],
        "properties": {
          "id": {"type": "string", "minLength": 1},
          "risk_flags": {"type": "array", "items": {"type": "string"}, "uniqueItems": true},
          "candidates": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": ["id", "position", "direction", "component_refs", "confidence", "evidence", "status"],
              "properties": {
                "id": {"type": "string", "minLength": 1},
                "position": {"type": "array", "minItems": 3, "maxItems": 3, "prefixItems": [{"type": "number"}, {"type": "number"}, {"type": "number"}], "items": false},
                "direction": {"type": "array", "minItems": 3, "maxItems": 3, "prefixItems": [{"type": "number"}, {"type": "number"}, {"type": "number"}], "items": false},
                "component_refs": {"type": "array", "minItems": 2, "maxItems": 2, "items": {"type": "integer", "minimum": 1}},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "evidence": {"type": "object"},
                "status": {"const": "pending_review"}
              }
            }
          }
        }
      }
    },
    "warnings": {"type": "array", "items": {"type": "string", "minLength": 1}, "uniqueItems": true},
    "errors": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["code", "message"],
        "properties": {
          "code": {"enum": ["NO_PROXIMITY", "NO_VALID_OVERLAP", "INVALID_GEOMETRY", "UNSUPPORTED_GEOMETRY", "AMBIGUOUS_RESULT", "EXPORT_MISMATCH"]},
          "message": {"type": "string", "minLength": 1}
        }
      }
    }
  },
  "allOf": [
    {
      "if": {"properties": {"status": {"const": "success"}}},
      "then": {"properties": {"has_candidate_regions": {"const": true}, "regions": {"minItems": 1}, "errors": {"maxItems": 0}}}
    },
    {
      "if": {"properties": {"status": {"const": "failure"}}},
      "then": {"properties": {"has_candidate_regions": {"const": false}, "regions": {"maxItems": 0}, "errors": {"minItems": 1}}}
    }
  ]
}
```

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://zhaohaoran-suanhai.github.io/hypermesh-weld-agent/hypermesh-probe.schema.json",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "selected_components", "capabilities"],
  "properties": {
    "schema_version": {"const": "1.0"},
    "selected_components": {
      "type": "array",
      "minItems": 2,
      "maxItems": 2,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "name"],
        "properties": {
          "id": {"type": "integer", "minimum": 1},
          "name": {"type": "string", "minLength": 1}
        }
      }
    },
    "capabilities": {
      "type": "object",
      "additionalProperties": false,
      "required": ["geomexport", "legacy_geomoutputdata", "connector_create"],
      "properties": {
        "geomexport": {"type": "boolean"},
        "legacy_geomoutputdata": {"type": "boolean"},
        "connector_create": {"type": "boolean"}
      }
    }
  }
}
```

- [ ] **Step 5: Create valid fixtures**

```json
{
  "schema_version": "1.0",
  "run_id": "run-001",
  "hypermesh": {"build": "2017", "model_name": "FDOOR", "units": "mm", "coordinate_system": "global"},
  "components": [
    {
      "id": 9,
      "name": "6101041-DDA1",
      "geometry": {"path": "C:/Temp/run-001/component-9.step", "format": "STEP", "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
      "summary": {"surface_count": 20, "solid_count": 1, "element_count": 0, "bbox": [0, 0, 0, 100, 50, 5]}
    },
    {
      "id": 12,
      "name": "6101035-DDA1(SW)",
      "geometry": {"path": "C:/Temp/run-001/component-12.step", "format": "STEP", "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},
      "summary": {"surface_count": 16, "solid_count": 1, "element_count": 0, "bbox": [20, 10, 1, 80, 40, 6]}
    }
  ],
  "parameters": {"search_distance": 5, "max_gap": 2, "pitch": 40, "end_offset": 20, "edge_clearance": 10, "rule_profile_version": "review-only-1"}
}
```

```json
{
  "schema_version": "1.0",
  "selected_components": [
    {"id": 9, "name": "6101041-DDA1"},
    {"id": 12, "name": "6101035-DDA1(SW)"}
  ],
  "capabilities": {"geomexport": true, "legacy_geomoutputdata": true, "connector_create": true}
}
```

- [ ] **Step 6: Implement schema loading and validation**

```python
# src/weld_agent/contracts.py
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class ContractValidationError(ValueError):
    pass


SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"


def _schema_path(schema_name: str) -> Path:
    if Path(schema_name).name != schema_name:
        raise ContractValidationError(f"invalid schema name: {schema_name}")
    path = SCHEMA_DIR / schema_name
    if not path.is_file():
        raise ContractValidationError(f"schema not found: {schema_name}")
    return path


def validate_document(schema_name: str, payload: Mapping[str, Any]) -> None:
    schema = json.loads(_schema_path(schema_name).read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda item: list(item.path))
    if errors:
        first = errors[0]
        location = "$" + "".join(f"[{value!r}]" for value in first.path)
        raise ContractValidationError(f"{location}: {first.message}")
    if schema_name == "selection.schema.json":
        ids = [component["id"] for component in payload["components"]]
        if len(set(ids)) != 2:
            raise ContractValidationError("selection requires two distinct component IDs")


def load_document(path: Path, schema_name: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractValidationError(f"cannot read JSON document {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ContractValidationError("document root must be an object")
    validate_document(schema_name, payload)
    return payload
```

- [ ] **Step 7: Run contract tests**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_contracts.py tests/test_hypermesh_probe_contract.py -v
```

Expected: all tests pass.

- [ ] **Step 8: Commit the contracts**

```powershell
git add schemas src/weld_agent/contracts.py tests/fixtures tests/test_contracts.py tests/test_hypermesh_probe_contract.py
git commit -m "feat: add versioned workflow contracts"
```

---

### Task 3: Safe Per-Run Workspace

**Files:**
- Create: `src/weld_agent/run_workspace.py`
- Create: `tests/test_run_workspace.py`

**Interfaces:**
- Consumes: validated `run_id`, optional root `Path`.
- Produces: `RunWorkspace.create(run_id, root=None)`, `write_json(name, payload)`, `read_json(name)`, `append_event(event, details)`, `cleanup_geometry()`.

- [ ] **Step 1: Write failing workspace tests**

```python
# tests/test_run_workspace.py
import json
from pathlib import Path

import pytest

from weld_agent.run_workspace import RunWorkspace


def test_workspace_writes_json_atomically(tmp_path: Path) -> None:
    workspace = RunWorkspace.create("run-001", root=tmp_path)
    target = workspace.write_json("selection.json", {"run_id": "run-001"})
    assert workspace.read_json("selection.json") == {"run_id": "run-001"}
    assert target.parent == tmp_path / "run-001"
    assert not list(target.parent.glob("*.tmp"))


def test_workspace_rejects_path_traversal(tmp_path: Path) -> None:
    workspace = RunWorkspace.create("run-001", root=tmp_path)
    with pytest.raises(ValueError, match="simple file name"):
        workspace.write_json("../outside.json", {})


def test_cleanup_removes_only_cad_exports(tmp_path: Path) -> None:
    workspace = RunWorkspace.create("run-001", root=tmp_path)
    (workspace.path / "part.step").write_text("cad", encoding="utf-8")
    (workspace.path / "result.json").write_text("{}", encoding="utf-8")
    workspace.cleanup_geometry()
    assert not (workspace.path / "part.step").exists()
    assert (workspace.path / "result.json").exists()


def test_workspace_appends_structured_event_log(tmp_path: Path) -> None:
    workspace = RunWorkspace.create("run-001", root=tmp_path)
    target = workspace.append_event("analysis_completed", {"status": "success"})
    record = json.loads(target.read_text(encoding="utf-8").splitlines()[0])
    assert record["event"] == "analysis_completed"
    assert record["details"] == {"status": "success"}
    assert record["timestamp_utc"].endswith("+00:00")
```

- [ ] **Step 2: Run tests and verify the module is absent**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_run_workspace.py -v
```

Expected: collection fails because `weld_agent.run_workspace` does not exist.

- [ ] **Step 3: Implement the safe workspace**

```python
# src/weld_agent/run_workspace.py
from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
CAD_SUFFIXES = {".step", ".stp", ".iges", ".igs"}


@dataclass(frozen=True)
class RunWorkspace:
    path: Path

    @classmethod
    def create(cls, run_id: str, root: Path | None = None) -> "RunWorkspace":
        if RUN_ID.fullmatch(run_id) is None:
            raise ValueError("invalid run_id")
        base = root or Path(tempfile.gettempdir()) / "hypermesh-weld-agent"
        path = (base / run_id).resolve()
        base_resolved = base.resolve()
        if path.parent != base_resolved:
            raise ValueError("run directory escapes workspace root")
        path.mkdir(parents=True, exist_ok=True)
        return cls(path=path)

    def _child(self, name: str) -> Path:
        if Path(name).name != name:
            raise ValueError("artifact name must be a simple file name")
        return self.path / name

    def write_json(self, name: str, payload: dict[str, Any]) -> Path:
        target = self._child(name)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, target)
        return target

    def read_json(self, name: str) -> dict[str, Any]:
        payload = json.loads(self._child(name).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("artifact root must be an object")
        return payload

    def append_event(self, event: str, details: dict[str, Any]) -> Path:
        if not event or any(character.isspace() for character in event):
            raise ValueError("event must be a non-empty token")
        target = self._child("events.jsonl")
        record = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "details": details,
        }
        with target.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        return target

    def cleanup_geometry(self) -> None:
        for path in self.path.iterdir():
            if path.is_file() and path.suffix.lower() in CAD_SUFFIXES:
                path.unlink()
```

- [ ] **Step 4: Run workspace tests**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_run_workspace.py -v
```

Expected: `4 passed`.

- [ ] **Step 5: Commit the workspace**

```powershell
git add src/weld_agent/run_workspace.py tests/test_run_workspace.py
git commit -m "feat: add safe per-run workspace"
```

---

### Task 4: Replaceable Fixture Candidate Provider

**Files:**
- Create: `src/weld_agent/providers/__init__.py`
- Create: `src/weld_agent/providers/base.py`
- Create: `src/weld_agent/providers/fixture.py`
- Create: `tests/test_fixture_provider.py`

**Interfaces:**
- Consumes: validated selection `Mapping[str, Any]`.
- Produces: protocol `CandidateProvider.analyze(selection) -> dict[str, Any]`, class `FixtureCandidateProvider`.

- [ ] **Step 1: Write failing provider tests**

```python
# tests/test_fixture_provider.py
import json
from pathlib import Path

from weld_agent.contracts import validate_document
from weld_agent.providers.fixture import FixtureCandidateProvider


FIXTURE = Path(__file__).parent / "fixtures" / "selection.valid.json"


def test_fixture_provider_marks_output_as_test_only() -> None:
    selection = json.loads(FIXTURE.read_text(encoding="utf-8"))
    result = FixtureCandidateProvider().analyze(selection)
    validate_document("weld-candidates.schema.json", result)
    assert result["provider"] == "fixture-test-only"
    assert result["parameters"] == selection["parameters"]
    assert result["elapsed_ms"] == 0
    assert result["has_candidate_regions"] is True
    assert result["regions"][0]["risk_flags"] == ["TEST_PROVIDER_ONLY"]
    assert result["regions"][0]["candidates"][0]["status"] == "pending_review"


def test_fixture_provider_reports_non_overlapping_bounding_boxes() -> None:
    selection = json.loads(FIXTURE.read_text(encoding="utf-8"))
    selection["components"][1]["summary"]["bbox"] = [200, 200, 200, 210, 210, 210]
    result = FixtureCandidateProvider().analyze(selection)
    assert result["status"] == "failure"
    assert result["has_candidate_regions"] is False
    assert result["errors"][0]["code"] == "NO_PROXIMITY"
```

- [ ] **Step 2: Run tests and verify provider modules are absent**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_fixture_provider.py -v
```

Expected: collection fails because `weld_agent.providers.fixture` does not exist.

- [ ] **Step 3: Define the provider protocol**

```python
# src/weld_agent/providers/base.py
from collections.abc import Mapping
from typing import Any, Protocol


class CandidateProvider(Protocol):
    def analyze(self, selection: Mapping[str, Any]) -> dict[str, Any]: ...
```

```python
# src/weld_agent/providers/__init__.py
from .base import CandidateProvider
from .fixture import FixtureCandidateProvider

__all__ = ["CandidateProvider", "FixtureCandidateProvider"]
```

- [ ] **Step 4: Implement the explicitly test-only provider**

```python
# src/weld_agent/providers/fixture.py
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _intersection_center(first: list[float], second: list[float]) -> list[float] | None:
    lower = [max(first[index], second[index]) for index in range(3)]
    upper = [min(first[index + 3], second[index + 3]) for index in range(3)]
    if any(low > high for low, high in zip(lower, upper, strict=True)):
        return None
    return [(low + high) / 2.0 for low, high in zip(lower, upper, strict=True)]


class FixtureCandidateProvider:
    def analyze(self, selection: Mapping[str, Any]) -> dict[str, Any]:
        component_ids = [item["id"] for item in selection["components"]]
        center = _intersection_center(
            selection["components"][0]["summary"]["bbox"],
            selection["components"][1]["summary"]["bbox"],
        )
        base = {
            "schema_version": "1.0",
            "run_id": selection["run_id"],
            "provider": "fixture-test-only",
            "algorithm_version": "fixture-1",
            "component_refs": component_ids,
            "parameters": dict(selection["parameters"]),
            "elapsed_ms": 0,
        }
        if center is None:
            return {
                **base,
                "status": "failure",
                "has_candidate_regions": False,
                "regions": [],
                "warnings": [],
                "errors": [{"code": "NO_PROXIMITY", "message": "fixture bounding boxes do not overlap"}],
            }
        return {
            **base,
            "status": "success",
            "has_candidate_regions": True,
            "regions": [
                {
                    "id": "fixture-region-1",
                    "risk_flags": ["TEST_PROVIDER_ONLY"],
                    "candidates": [
                        {
                            "id": "fixture-candidate-1",
                            "position": center,
                            "direction": [0.0, 0.0, 1.0],
                            "component_refs": component_ids,
                            "confidence": 0.0,
                            "evidence": {"source": "bounding-box-intersection-center"},
                            "status": "pending_review",
                        }
                    ],
                }
            ],
            "warnings": ["TEST_PROVIDER_ONLY: result is not a real weld analysis"],
            "errors": [],
        }
```

- [ ] **Step 5: Run provider tests**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_fixture_provider.py -v
```

Expected: `2 passed`.

- [ ] **Step 6: Commit the provider boundary**

```powershell
git add src/weld_agent/providers tests/test_fixture_provider.py
git commit -m "feat: add replaceable fixture candidate provider"
```

---

### Task 5: Deterministic Workflow and CLI Round Trip

**Files:**
- Create: `src/weld_agent/workflow.py`
- Create: `src/weld_agent/cli.py`
- Create: `tests/test_workflow_cli.py`

**Interfaces:**
- Consumes: `selection.json`, output root, `CandidateProvider`.
- Produces: `run_analysis(selection_path, output_root, provider) -> Path`; CLI `analyze` and `validate` subcommands.

- [ ] **Step 1: Write failing CLI tests**

```python
# tests/test_workflow_cli.py
import json
from pathlib import Path

from weld_agent.cli import main


FIXTURE = Path(__file__).parent / "fixtures" / "selection.valid.json"


def test_analyze_command_writes_valid_candidate_file(tmp_path: Path) -> None:
    exit_code = main([
        "analyze",
        "--selection", str(FIXTURE),
        "--output-root", str(tmp_path),
        "--provider", "fixture",
    ])
    assert exit_code == 0
    output = tmp_path / "run-001" / "weld_candidates.json"
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["provider"] == "fixture-test-only"
    events = (output.parent / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(events[-1])["event"] == "analysis_completed"


def test_validate_command_rejects_wrong_schema(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{}", encoding="utf-8")
    assert main(["validate", "--schema", "selection.schema.json", "--input", str(invalid)]) == 2
```

- [ ] **Step 2: Run tests and verify workflow modules are absent**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_workflow_cli.py -v
```

Expected: collection fails because `weld_agent.cli` does not exist.

- [ ] **Step 3: Implement the deterministic workflow**

```python
# src/weld_agent/workflow.py
from pathlib import Path

from weld_agent.contracts import load_document, validate_document
from weld_agent.providers.base import CandidateProvider
from weld_agent.run_workspace import RunWorkspace


def run_analysis(selection_path: Path, output_root: Path, provider: CandidateProvider) -> Path:
    selection = load_document(selection_path, "selection.schema.json")
    workspace = RunWorkspace.create(selection["run_id"], root=output_root)
    result = provider.analyze(selection)
    validate_document("weld-candidates.schema.json", result)
    output = workspace.write_json("weld_candidates.json", result)
    workspace.append_event(
        "analysis_completed",
        {"status": result["status"], "provider": result["provider"], "output": output.name},
    )
    return output
```

- [ ] **Step 4: Implement analyze and validate commands**

```python
# src/weld_agent/cli.py
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from weld_agent.contracts import ContractValidationError, load_document
from weld_agent.providers.fixture import FixtureCandidateProvider
from weld_agent.workflow import run_analysis


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hypermesh-weld-agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--selection", type=Path, required=True)
    analyze.add_argument("--output-root", type=Path, required=True)
    analyze.add_argument("--provider", choices=["fixture"], required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--schema", required=True)
    validate.add_argument("--input", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            load_document(args.input, args.schema)
            return 0
        output = run_analysis(args.selection, args.output_root, FixtureCandidateProvider())
        print(output)
        return 0
    except (ContractValidationError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run CLI tests**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_workflow_cli.py -v
```

Expected: `2 passed`.

- [ ] **Step 6: Run an actual CLI round trip**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m weld_agent.cli analyze --selection tests/fixtures/selection.valid.json --output-root run-artifacts --provider fixture
```

Expected: prints a path ending in `run-artifacts\run-001\weld_candidates.json`; the JSON contains `"provider": "fixture-test-only"`.

- [ ] **Step 7: Commit the workflow**

```powershell
git add src/weld_agent/workflow.py src/weld_agent/cli.py tests/test_workflow_cli.py
git commit -m "feat: add deterministic contract workflow"
```

---

### Task 6: PythonOCC Runtime Doctor

**Files:**
- Create: `src/weld_agent/runtime.py`
- Modify: `src/weld_agent/cli.py`
- Create: `tests/test_runtime.py`

**Interfaces:**
- Consumes: explicit Python interpreter `Path`.
- Produces: `probe_pythonocc(executable: Path) -> RuntimeProbe`; CLI `doctor --pythonocc-python PATH`.

- [ ] **Step 1: Write failing runtime tests**

```python
# tests/test_runtime.py
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
    monkeypatch.setattr("weld_agent.runtime.subprocess.run", lambda *args, **kwargs: completed)
    result = probe_pythonocc(Path("C:/fake/python.exe"))
    assert result.available is True
    assert result.python_version == "3.11.15"
    assert result.occ_version == "7.9.0"


def test_probe_reports_process_failure(monkeypatch) -> None:
    completed = CompletedProcess(args=[], returncode=1, stdout="", stderr="import failed")
    monkeypatch.setattr("weld_agent.runtime.subprocess.run", lambda *args, **kwargs: completed)
    result = probe_pythonocc(Path("C:/fake/python.exe"))
    assert result.available is False
    assert result.error == "import failed"


def test_probe_reports_missing_executable(monkeypatch) -> None:
    def raise_missing(*args, **kwargs):
        raise FileNotFoundError("python.exe not found")

    monkeypatch.setattr("weld_agent.runtime.subprocess.run", raise_missing)
    result = probe_pythonocc(Path("C:/missing/python.exe"))
    assert result.available is False
    assert "not found" in result.error
```

- [ ] **Step 2: Run tests and verify runtime module is absent**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_runtime.py -v
```

Expected: collection fails because `weld_agent.runtime` does not exist.

- [ ] **Step 3: Implement the non-shelling runtime probe**

```python
# src/weld_agent/runtime.py
from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


PROBE_CODE = """
import json
import platform
import OCC
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
print(json.dumps({"python": platform.python_version(), "occ": OCC.VERSION}))
""".strip()


@dataclass(frozen=True)
class RuntimeProbe:
    available: bool
    executable: str
    python_version: str | None = None
    occ_version: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def probe_pythonocc(executable: Path) -> RuntimeProbe:
    try:
        completed = subprocess.run(
            [str(executable), "-c", PROBE_CODE],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return RuntimeProbe(False, str(executable), error=str(exc))
    if completed.returncode != 0:
        return RuntimeProbe(False, str(executable), error=completed.stderr.strip() or "probe failed")
    try:
        payload = json.loads(completed.stdout)
        return RuntimeProbe(True, str(executable), payload["python"], payload["occ"])
    except (json.JSONDecodeError, KeyError) as exc:
        return RuntimeProbe(False, str(executable), error=f"invalid probe output: {exc}")
```

- [ ] **Step 4: Add the doctor command**

Extend `_parser()` in `src/weld_agent/cli.py`:

```python
    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("--pythonocc-python", type=Path, required=True)
```

Add imports:

```python
import json
from weld_agent.runtime import probe_pythonocc
```

Insert this branch before `validate` handling in `main()`:

```python
        if args.command == "doctor":
            result = probe_pythonocc(args.pythonocc_python)
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
            return 0 if result.available else 2
```

- [ ] **Step 5: Run unit tests**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_runtime.py tests/test_workflow_cli.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Probe the installed OCC runtime**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m weld_agent.cli doctor --pythonocc-python '..\pythonocc\.m\envs\occ\python.exe'
```

Expected: exit code 0 with JSON containing `"available": true`, Python `3.11.15`, and an OCC version.

- [ ] **Step 7: Commit the runtime doctor**

```powershell
git add src/weld_agent/runtime.py src/weld_agent/cli.py tests/test_runtime.py
git commit -m "feat: add PythonOCC runtime doctor"
```

---

### Task 7: HyperMesh 2017 Selection and Capability Probe

**Files:**
- Create: `hypermesh/tcl/weld_agent_probe.tcl`
- Create: `docs/manual-tests/hm2017-capability-probe.md`

**Interfaces:**
- Consumes: interactive selection of exactly two HyperMesh Components and an explicit output path.
- Produces: JSON matching `hypermesh-probe.schema.json`; no geometry export and no model mutation beyond a temporary selection mark.

- [ ] **Step 1: Create the Tcl probe with strict two-Component selection**

```tcl
# hypermesh/tcl/weld_agent_probe.tcl
namespace eval ::weldagent {}

proc ::weldagent::json_escape {value} {
    return [string map [list "\\" "\\\\" "\"" "\\\"" "\n" "\\n" "\r" "\\r" "\t" "\\t"] $value]
}

proc ::weldagent::command_available {name} {
    return [expr {[llength [info commands $name]] > 0 ? "true" : "false"}]
}

proc ::weldagent::run_probe {output_path} {
    *clearmark components 1
    *createmarkpanel components 1 "Select exactly two Components for Weld Agent"
    set component_ids [hm_getmark components 1]
    if {[llength $component_ids] != 2} {
        error "Weld Agent requires exactly two Components; selected [llength $component_ids]"
    }

    set component_json {}
    foreach component_id $component_ids {
        set component_name [hm_getvalue components id=$component_id dataname=name]
        lappend component_json [format {    {"id": %d, "name": "%s"}} $component_id [::weldagent::json_escape $component_name]]
    }

    set normalized_output [file normalize $output_path]
    file mkdir [file dirname $normalized_output]
    set stream [open $normalized_output w]
    fconfigure $stream -encoding utf-8 -translation lf
    puts $stream "{"
    puts $stream {  "schema_version": "1.0",}
    puts $stream {  "selected_components": [}
    puts $stream [join $component_json ",\n"]
    puts $stream {  ],}
    puts $stream "  \"capabilities\": {"
    puts $stream [format {    "geomexport": %s,} [::weldagent::command_available *geomexport]]
    puts $stream [format {    "legacy_geomoutputdata": %s,} [::weldagent::command_available *geomoutputdata]]
    puts $stream [format {    "connector_create": %s} [::weldagent::command_available *CE_ConnectorCreate]]
    puts $stream "  }"
    puts $stream "}"
    close $stream
    return $normalized_output
}
```

- [ ] **Step 2: Validate a probe document with the existing command**

No Python change is required beyond the existing `validate` command. Verify with the committed fixture:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m weld_agent.cli validate --schema hypermesh-probe.schema.json --input tests/fixtures/hypermesh_probe.valid.json
```

Expected: exit code 0 and no error output.

- [ ] **Step 3: Write the exact manual probe procedure**

````markdown
# HyperMesh 2017 Capability Probe

1. Open the car-door model in HyperMesh 2017.
2. Open `View -> Command Window`.
3. Run:

   ```tcl
   source {C:/Users/25335/Documents/GitHub/hypermesh-weld-agent/hypermesh/tcl/weld_agent_probe.tcl}
   ::weldagent::run_probe {C:/Users/25335/AppData/Local/Temp/hypermesh-weld-agent/hm2017-probe.json}
   ```

4. Select exactly two Components when HyperMesh displays the selection panel.
5. Confirm the returned path is `hm2017-probe.json` and the model has no new geometry, nodes, elements, or connectors.
6. Validate the file from PowerShell:

   ```powershell
   & '..\pythonocc\.m\envs\occ\python.exe' -m weld_agent.cli validate --schema hypermesh-probe.schema.json --input "$env:TEMP\hypermesh-weld-agent\hm2017-probe.json"
   ```

7. Record the three boolean capability values in the Stage 1 implementation plan. The probe itself does not export geometry or change the model.
````

- [ ] **Step 4: Run the HyperMesh manual probe**

Expected:

- exactly two selected Component IDs and names appear in the JSON;
- `geomexport`, `legacy_geomoutputdata`, and `connector_create` are booleans;
- Python validation exits 0;
- entity counts in the HyperMesh model are unchanged.

- [ ] **Step 5: Commit the capability probe**

```powershell
git add hypermesh/tcl/weld_agent_probe.tcl docs/manual-tests/hm2017-capability-probe.md
git commit -m "feat: add HyperMesh 2017 capability probe"
```

---

### Task 8: Setup Documentation and Unified Verification

**Files:**
- Create: `docs/setup.md`
- Create: `scripts/verify.ps1`
- Modify: `README.md`

**Interfaces:**
- Consumes: repository checkout and explicit local OCC interpreter path.
- Produces: one verification command with deterministic exit code; documented Stage 0 usage.

- [ ] **Step 1: Create the verification script**

```powershell
# scripts/verify.ps1
[CmdletBinding()]
param(
    [string]$PythonOccPython = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

if ([string]::IsNullOrWhiteSpace($PythonOccPython)) {
    $PythonOccPython = $env:WELD_AGENT_PYTHONOCC_PYTHON
}

if ([string]::IsNullOrWhiteSpace($PythonOccPython)) {
    throw "Set WELD_AGENT_PYTHONOCC_PYTHON or pass -PythonOccPython"
}

if (-not (Test-Path -LiteralPath $PythonOccPython -PathType Leaf)) {
    throw "PythonOCC interpreter not found: $PythonOccPython"
}

Push-Location $repoRoot
try {
    & $PythonOccPython -m pytest
    if ($LASTEXITCODE -ne 0) { throw "pytest failed with exit code $LASTEXITCODE" }

    & $PythonOccPython -m weld_agent.cli doctor --pythonocc-python $PythonOccPython
    if ($LASTEXITCODE -ne 0) { throw "runtime doctor failed with exit code $LASTEXITCODE" }

    git diff --check
    if ($LASTEXITCODE -ne 0) { throw "git diff --check failed" }
}
finally {
    Pop-Location
}
```

- [ ] **Step 2: Document setup without committing a local absolute path**

````markdown
# Setup

## Supported Environment

- Windows 10
- Python 3.11
- HyperMesh 2017
- PythonOCC capable of importing `BRepExtrema_DistShapeShape` and `BRepMesh_IncrementalMesh`

## Install for Development

From the repository root:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pip install -e '.[dev]'
```

The sibling `pythonocc` directory is a local runtime convenience, not a source-code dependency. Do not commit its absolute path or contents.

## Verify

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

To use a different interpreter:

```powershell
$otherPython = (Resolve-Path '..\another-occ-env\python.exe').Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -PythonOccPython $otherPython
```

## Stage 0 Analysis Smoke Test

```powershell
hypermesh-weld-agent analyze --selection tests\fixtures\selection.valid.json --output-root run-artifacts --provider fixture
```

The produced point is explicitly test-only and must not be treated as a real weld candidate.
````

- [ ] **Step 3: Link setup and manual test documentation from README**

Append:

````markdown
## Development

- [Local setup](docs/setup.md)
- [HyperMesh 2017 capability probe](docs/manual-tests/hm2017-capability-probe.md)

Run all local checks with:

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```
````

- [ ] **Step 4: Run the complete verification command**

Run:

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

Expected:

- pytest reports all tests passed;
- runtime doctor reports `"available": true`;
- `git diff --check` produces no output;
- command exits 0.

- [ ] **Step 5: Confirm repository independence**

Run:

```powershell
rg -n --hidden --glob '!.git/**' "fluent-automation|from fluent|import fluent" .
```

Expected: only the design/plan documentation and `AGENTS.md` contain the string `fluent-automation`; no Python, Tcl, PowerShell, or configuration file imports or executes it.

- [ ] **Step 6: Commit documentation and verification**

```powershell
git add README.md docs/setup.md scripts/verify.ps1
git commit -m "docs: add Stage 0 setup and verification"
```

---

## Final Stage 0 Review

- [ ] Set `WELD_AGENT_PYTHONOCC_PYTHON` to the tested OCC interpreter, run `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1`, and capture the passing summary.
- [ ] Run the HyperMesh manual capability probe and preserve only the boolean results and selected IDs/names; do not commit the customer model or exported geometry.
- [ ] Run `git status --short` and verify it is empty.
- [ ] Run `git log --oneline --decorate -10` and confirm each task has an independent commit.
- [ ] Write the Stage 1 plan using the observed HyperMesh command capabilities; do not assume `*geomexport` is present until the probe confirms it.

## Deferred Plans

- Stage 1: selected-Component CAD export, external process invocation, HyperMesh preview, explicit accept/reject, and creation of unrealized Connector.
- Stage 2: geometry algorithm selection, labeled examples, accuracy metrics, and real candidate provider.
- Stage 3: controlled Agent tools and natural-language orchestration.
