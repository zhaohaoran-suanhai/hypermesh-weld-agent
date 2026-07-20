# HyperMesh 2017 STEP Export Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个非破坏性的 HyperMesh 2017 双 Component 导出探针，分别生成两个 STEP，经 PythonOCC 校验后产出正式 `selection.json`。

**Architecture:** HyperMesh Tcl 只负责选择、源几何摘要、显示隔离、STEP 导出和中间 manifest；Python 负责严格合同校验、SHA-256、OCC 拓扑/包围盒检查、校验报告和最终 selection。两个阶段通过版本化 JSON 和每次运行唯一的临时目录解耦，任何失败都不得修改模型或产生可被下游误用的正式 selection。

**Tech Stack:** Windows 10/PowerShell、Python 3.11、pytest、jsonschema、PythonOCC 7.9.0、HyperMesh 2017、Tcl 8.5、STEP AP214。

## Global Constraints

- 仓库路径固定为 `C:\Users\25335\Documents\GitHub\hypermesh-weld-agent`，直接在 `main` 开发。
- 不导入、复制或运行 `fluent-automation` 中的代码。
- Python 版本为 `>=3.11,<3.12`；当前 OCC 环境为 Python 3.11.15 / OCC 7.9.0。
- 本地 OCC 解释器只能通过命令参数或环境变量发现，不得把用户绝对路径提交到 Git。
- HyperMesh 侧兼容 Tcl 8.5，不使用 `try/finally`、字典映射等 Tcl 8.6 专有能力。
- 每次只接受两个不同 Component，并分别导出 `component-<id>.step`。
- STEP 固定使用 AP214、Millimeters、Displayed、LayerMode=None、GeometryMode=Standard、TopologyMode=Solid/Shell、AssemblyMode=Hierarchy、WriteNameFrom=Component、OptimizeForCAD=Off。
- 首版只调用 `*geomexport`；失败时不得静默回退到 `*geomoutputdata`。
- 导出成功、失败或取消后都必须精确恢复运行前显示的 Component ID 集合。
- 不修改几何、网格、Component 归属或 Connector，不保存或覆盖 `.hm` 模型。
- 客户 CAD、临时 STEP、运行输出和本地路径不得提交或上传。
- 本计划不实现焊点算法、预览、Connector、Realize 或 Agent。
- 每个任务先写失败测试，再做最小实现，通过后独立提交。

---

## Planned File Map

```text
config/integration-probe-1.json                   # 明确标为探针用途的容差与必需 selection 参数
schemas/export-manifest.schema.json              # Tcl -> Python 中间合同
schemas/export-validation.schema.json            # OCC 校验报告合同
schemas/integration-profile.schema.json          # 集成探针参数合同
src/weld_agent/export_finalizer.py                # manifest 到 validation/selection 的编排
src/weld_agent/geometry/__init__.py               # 几何检查接口导出
src/weld_agent/geometry/step_inspector.py         # PythonOCC STEP 读取、计数、包围盒
src/weld_agent/cli.py                             # 新增 finalize-export 命令
hypermesh/tcl/weld_agent_export.tcl               # HM2017 选择、摘要、隔离、导出和恢复
tests/fixtures/export_manifest.valid.json         # 有效中间合同样例
tests/fixtures/integration_profile.valid.json     # 有效探针配置样例
tests/test_export_contracts.py                    # Schema 与跨字段约束
tests/test_step_inspector.py                      # OCC 检查接口单元/本地集成测试
tests/test_export_finalizer.py                    # SHA、bbox、报告和 selection 测试
tests/test_export_cli.py                          # finalize-export CLI 测试
tests/test_hypermesh_export_tcl.py                # Tcl 8.5 命令桩测试
docs/manual-tests/hm2017-step-export-probe.md     # 真实车门模型操作与验收记录
docs/setup.md                                     # 新接口和本地运行说明
README.md                                         # 当前阶段状态和入口
scripts/verify.ps1                                # 统一验证包含导出探针测试
```

---

### Task 1: Freeze the Export Contracts and Integration Profile

**Files:**
- Create: `schemas/export-manifest.schema.json`
- Create: `schemas/export-validation.schema.json`
- Create: `schemas/integration-profile.schema.json`
- Modify: `schemas/selection.schema.json`
- Create: `config/integration-probe-1.json`
- Create: `tests/fixtures/export_manifest.valid.json`
- Create: `tests/fixtures/integration_profile.valid.json`
- Create: `tests/test_export_contracts.py`
- Modify: `tests/test_contracts.py`
- Modify: `src/weld_agent/contracts.py`

**Interfaces:**
- Consumes: `validate_document(schema_name: str, payload: Mapping[str, Any])`.
- Produces: strict Schema 1.0 documents; semantic checks for two distinct IDs and two distinct absolute STEP paths.

- [ ] **Step 1: Write failing contract tests**

```python
# tests/test_export_contracts.py
import copy
from pathlib import Path

import pytest

from weld_agent.contracts import ContractValidationError, load_document, validate_document


FIXTURES = Path(__file__).parent / "fixtures"


def test_valid_export_manifest_passes() -> None:
    payload = load_document(
        FIXTURES / "export_manifest.valid.json",
        "export-manifest.schema.json",
    )
    assert [item["id"] for item in payload["components"]] == [15, 20]
    assert payload["export_options"]["units"] == "Millimeters"


def test_manifest_rejects_duplicate_paths() -> None:
    payload = load_document(
        FIXTURES / "export_manifest.valid.json",
        "export-manifest.schema.json",
    )
    payload = copy.deepcopy(payload)
    payload["components"][1]["step_path"] = payload["components"][0]["step_path"]
    with pytest.raises(ContractValidationError, match="distinct STEP paths"):
        validate_document("export-manifest.schema.json", payload)


def test_profile_rejects_negative_bbox_tolerance() -> None:
    payload = load_document(
        FIXTURES / "integration_profile.valid.json",
        "integration-profile.schema.json",
    )
    payload = copy.deepcopy(payload)
    payload["bbox_absolute_tolerance"] = -1
    with pytest.raises(ContractValidationError, match="greater than or equal"):
        validate_document("integration-profile.schema.json", payload)
```

- [ ] **Step 2: Run the tests and verify missing schemas fail**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_export_contracts.py -v
```

Expected: FAIL with `schema not found: export-manifest.schema.json`.

- [ ] **Step 3: Add the strict manifest and profile schemas**

Create `export-manifest.schema.json` with these exact top-level fields and nested requirements:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://zhaohaoran-suanhai.github.io/hypermesh-weld-agent/export-manifest.schema.json",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "run_id", "hypermesh", "export_options", "components", "warnings"],
  "properties": {
    "schema_version": {"const": "1.0"},
    "run_id": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"},
    "hypermesh": {
      "type": "object", "additionalProperties": false,
      "required": ["build", "model_name", "units", "coordinate_system"],
      "properties": {
        "build": {"type": "string", "minLength": 1},
        "model_name": {"type": "string", "minLength": 1},
        "units": {"const": "mm"},
        "coordinate_system": {"const": "global"}
      }
    },
    "export_options": {
      "type": "object", "additionalProperties": false,
      "required": ["cad_type", "version", "units", "export", "layer_mode", "geometry_mode", "topology_mode", "assembly_mode", "write_name_from", "optimize_for_cad"],
      "properties": {
        "cad_type": {"const": "step_ct"}, "version": {"const": "AP214"},
        "units": {"const": "Millimeters"}, "export": {"const": "Displayed"},
        "layer_mode": {"const": "None"}, "geometry_mode": {"const": "Standard"},
        "topology_mode": {"const": "Solid/Shell"}, "assembly_mode": {"const": "Hierarchy"},
        "write_name_from": {"const": "Component"}, "optimize_for_cad": {"const": "Off"}
      }
    },
    "components": {
      "type": "array", "minItems": 2, "maxItems": 2,
      "items": {
        "type": "object", "additionalProperties": false,
        "required": ["id", "name", "step_path", "summary"],
        "properties": {
          "id": {"type": "integer", "minimum": 1},
          "name": {"type": "string", "minLength": 1},
          "step_path": {"type": "string", "minLength": 1},
          "summary": {"$ref": "selection.schema.json#/$defs/geometry_summary"}
        }
      }
    },
    "warnings": {"type": "array", "items": {"type": "string", "minLength": 1}}
  }
}
```

Before using the `$ref`, move the existing `summary` object from `selection.schema.json` into `$defs.geometry_summary` and reference it from both schemas. Keep the accepted `selection.json` shape unchanged and add a regression assertion to `tests/test_contracts.py`.

Because these are cross-file references, replace the one-schema validator construction in `contracts.py` with a local, offline registry; it must never resolve project schemas over the network:

```python
from referencing import Registry, Resource


def _schema_registry() -> Registry:
    resources = []
    for path in SCHEMA_DIR.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


validator = Draft202012Validator(schema, registry=_schema_registry())
```

Create `integration-profile.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://zhaohaoran-suanhai.github.io/hypermesh-weld-agent/integration-profile.schema.json",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "profile_name", "bbox_absolute_tolerance", "bbox_relative_tolerance", "parameters"],
  "properties": {
    "schema_version": {"const": "1.0"},
    "profile_name": {"const": "integration-probe-1"},
    "bbox_absolute_tolerance": {"type": "number", "minimum": 0},
    "bbox_relative_tolerance": {"type": "number", "minimum": 0},
    "parameters": {"$ref": "selection.schema.json#/properties/parameters"}
  }
}
```

Use this tracked profile and identical fixture content:

```json
{
  "schema_version": "1.0",
  "profile_name": "integration-probe-1",
  "bbox_absolute_tolerance": 0.01,
  "bbox_relative_tolerance": 0.000001,
  "parameters": {
    "search_distance": 5.0,
    "max_gap": 2.0,
    "pitch": 40.0,
    "end_offset": 20.0,
    "edge_clearance": 10.0,
    "rule_profile_version": "integration-probe-1-not-engineering-standard"
  }
}
```

Use this exact manifest fixture:

```json
{
  "schema_version": "1.0",
  "run_id": "hm-20260720-120000-1",
  "hypermesh": {"build": "2017", "model_name": "FDOOR", "units": "mm", "coordinate_system": "global"},
  "export_options": {
    "cad_type": "step_ct", "version": "AP214", "units": "Millimeters",
    "export": "Displayed", "layer_mode": "None", "geometry_mode": "Standard",
    "topology_mode": "Solid/Shell", "assembly_mode": "Hierarchy",
    "write_name_from": "Component", "optimize_for_cad": "Off"
  },
  "components": [
    {
      "id": 15, "name": "6101081-DD01-A",
      "step_path": "C:/Temp/hypermesh-weld-agent/hm-20260720-120000-1/component-15.step",
      "summary": {"surface_count": 20, "solid_count": 0, "element_count": 0, "bbox": [0, 0, 0, 100, 50, 5]}
    },
    {
      "id": 20, "name": "6101161-DD01-A",
      "step_path": "C:/Temp/hypermesh-weld-agent/hm-20260720-120000-1/component-20.step",
      "summary": {"surface_count": 16, "solid_count": 0, "element_count": 0, "bbox": [20, 10, 1, 80, 40, 6]}
    }
  ],
  "warnings": []
}
```

- [ ] **Step 4: Add semantic uniqueness and absolute-path checks**

Add this helper and branch to `contracts.py`:

```python
from pathlib import PurePosixPath, PureWindowsPath


def _is_absolute_any_platform(value: str) -> bool:
    return PureWindowsPath(value).is_absolute() or PurePosixPath(value).is_absolute()


def _validate_two_component_identity(payload: Mapping[str, Any], *, path_key: str | None) -> None:
    components = payload["components"]
    ids = [component["id"] for component in components]
    if len(set(ids)) != 2:
        raise ContractValidationError("document requires two distinct component IDs")
    if path_key is not None:
        paths = [component[path_key] for component in components]
        if len(set(paths)) != 2:
            raise ContractValidationError("manifest requires two distinct STEP paths")
        if not all(_is_absolute_any_platform(value) for value in paths):
            raise ContractValidationError("manifest STEP paths must be absolute")
```

Call it for `selection.schema.json` with `path_key=None` and for `export-manifest.schema.json` with `path_key="step_path"`.

- [ ] **Step 5: Add the validation-report schema**

Create `export-validation.schema.json` with the complete structure below. Finite-number enforcement remains in Python because JSON Schema’s `number` type alone does not reject every non-standard parser representation.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://zhaohaoran-suanhai.github.io/hypermesh-weld-agent/export-validation.schema.json",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "run_id", "status", "components", "warnings", "errors"],
  "properties": {
    "schema_version": {"const": "1.0"},
    "run_id": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"},
    "status": {"enum": ["success", "failure"]},
    "components": {
      "type": "array", "maxItems": 2,
      "items": {
        "type": "object", "additionalProperties": false,
        "required": ["id", "step_path", "file_size", "sha256", "read_status", "face_count", "solid_count", "occ_bbox", "bbox_delta", "checks_passed"],
        "properties": {
          "id": {"type": "integer", "minimum": 1},
          "step_path": {"type": "string", "minLength": 1},
          "file_size": {"type": "integer", "minimum": 1},
          "sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
          "read_status": {"const": "success"},
          "face_count": {"type": "integer", "minimum": 0},
          "solid_count": {"type": "integer", "minimum": 0},
          "occ_bbox": {"$ref": "selection.schema.json#/$defs/bbox"},
          "bbox_delta": {"$ref": "selection.schema.json#/$defs/bbox"},
          "checks_passed": {"type": "boolean"}
        }
      }
    },
    "warnings": {"type": "array", "items": {"type": "string", "minLength": 1}},
    "errors": {
      "type": "array",
      "items": {
        "type": "object", "additionalProperties": false,
        "required": ["code", "message"],
        "properties": {
          "code": {"type": "string", "minLength": 1},
          "message": {"type": "string", "minLength": 1}
        }
      }
    }
  },
  "allOf": [
    {"if": {"properties": {"status": {"const": "success"}}}, "then": {"properties": {"components": {"minItems": 2}, "errors": {"maxItems": 0}}}},
    {"if": {"properties": {"status": {"const": "failure"}}}, "then": {"properties": {"errors": {"minItems": 1}}}}
  ]
}
```

When extracting the existing bbox array, define it as `$defs.bbox`, then make `$defs.geometry_summary.properties.bbox` reference `#/$defs/bbox`.

- [ ] **Step 6: Run contracts and commit**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_export_contracts.py tests/test_contracts.py -v
```

Expected: PASS.

Commit:

```powershell
git add schemas config src/weld_agent/contracts.py tests/fixtures tests/test_contracts.py tests/test_export_contracts.py
git commit -m "feat: define STEP export contracts"
```

---

### Task 2: Implement the PythonOCC STEP Inspector

**Files:**
- Create: `src/weld_agent/geometry/__init__.py`
- Create: `src/weld_agent/geometry/step_inspector.py`
- Create: `tests/test_step_inspector.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Consumes: a local STEP `Path`.
- Produces: `StepInspection(face_count: int, solid_count: int, bbox: tuple[float, float, float, float, float, float])`; protocol `StepInspector.inspect(path)`; classified `StepInspectionError(code, message)`.

- [ ] **Step 1: Write unit tests against the public interface**

```python
# tests/test_step_inspector.py
import math
from pathlib import Path

import pytest

from weld_agent.geometry.step_inspector import PythonOccStepInspector, StepInspectionError


def test_missing_step_is_classified(tmp_path: Path) -> None:
    with pytest.raises(StepInspectionError) as caught:
        PythonOccStepInspector().inspect(tmp_path / "missing.step")
    assert caught.value.code == "STEP_READ_FAILED"


@pytest.mark.occ_integration
def test_occ_reads_a_generated_box(tmp_path: Path) -> None:
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
    from OCC.Core.IFSelect import IFSelect_RetDone
    from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer

    path = tmp_path / "box.step"
    writer = STEPControl_Writer()
    assert writer.Transfer(BRepPrimAPI_MakeBox(10, 20, 30).Shape(), STEPControl_AsIs) == IFSelect_RetDone
    assert writer.Write(str(path)) == IFSelect_RetDone

    result = PythonOccStepInspector().inspect(path)
    assert result.face_count == 6
    assert result.solid_count == 1
    assert all(math.isfinite(value) for value in result.bbox)
    assert result.bbox == pytest.approx((0, 0, 0, 10, 20, 30), abs=1e-5)
```

Register `occ_integration` in `pyproject.toml` under pytest markers so strict marker mode accepts it.

- [ ] **Step 2: Run tests and verify the module is absent**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_step_inspector.py -v
```

Expected: collection FAIL with `No module named 'weld_agent.geometry'`.

- [ ] **Step 3: Implement the inspector with lazy OCC imports**

```python
# src/weld_agent/geometry/step_inspector.py
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


BBox = tuple[float, float, float, float, float, float]


@dataclass(frozen=True)
class StepInspection:
    face_count: int
    solid_count: int
    bbox: BBox


class StepInspectionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class StepInspector(Protocol):
    def inspect(self, path: Path) -> StepInspection:
        raise NotImplementedError


def _count(shape: object, topology_type: int) -> int:
    from OCC.Core.TopExp import TopExp_Explorer

    explorer = TopExp_Explorer(shape, topology_type)
    count = 0
    while explorer.More():
        count += 1
        explorer.Next()
    return count


class PythonOccStepInspector:
    def inspect(self, path: Path) -> StepInspection:
        if not path.is_file() or path.stat().st_size == 0:
            raise StepInspectionError("STEP_READ_FAILED", f"missing or empty STEP: {path}")

        from OCC.Core.Bnd import Bnd_Box
        from OCC.Core.BRepBndLib import brepbndlib
        from OCC.Core.IFSelect import IFSelect_RetDone
        from OCC.Core.STEPControl import STEPControl_Reader
        from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_SOLID

        reader = STEPControl_Reader()
        if reader.ReadFile(str(path)) != IFSelect_RetDone:
            raise StepInspectionError("STEP_READ_FAILED", f"OCC could not read STEP: {path}")
        if reader.TransferRoots() <= 0:
            raise StepInspectionError("STEP_READ_FAILED", f"OCC transferred no STEP roots: {path}")
        shape = reader.OneShape()
        if shape.IsNull():
            raise StepInspectionError("EMPTY_IMPORTED_SHAPE", f"OCC returned a null shape: {path}")

        box = Bnd_Box()
        brepbndlib.Add(shape, box)
        bbox = tuple(float(value) for value in box.Get())
        if len(bbox) != 6 or not all(math.isfinite(value) for value in bbox):
            raise StepInspectionError("EXPORT_MISMATCH", f"non-finite OCC bbox: {path}")
        face_count = _count(shape, TopAbs_FACE)
        solid_count = _count(shape, TopAbs_SOLID)
        if face_count == 0 and solid_count == 0:
            raise StepInspectionError("EMPTY_IMPORTED_SHAPE", f"STEP has no faces or solids: {path}")
        return StepInspection(face_count, solid_count, bbox)  # type: ignore[arg-type]
```

Export `BBox`, `StepInspection`, `StepInspectionError`, `StepInspector`, and `PythonOccStepInspector` from `geometry/__init__.py`.

- [ ] **Step 4: Run tests and commit**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_step_inspector.py -v
```

Expected: 2 PASS with the configured OCC interpreter.

Commit:

```powershell
git add pyproject.toml src/weld_agent/geometry tests/test_step_inspector.py
git commit -m "feat: inspect exported STEP geometry with OCC"
```

---

### Task 3: Finalize Exports into Validation and Selection Documents

**Files:**
- Create: `src/weld_agent/export_finalizer.py`
- Create: `tests/test_export_finalizer.py`
- Modify: `src/weld_agent/cli.py`
- Create: `tests/test_export_cli.py`

**Interfaces:**
- Consumes: `finalize_export(manifest_path: Path, profile_path: Path, inspector: StepInspector) -> FinalizationResult`.
- Produces: atomic `export-validation.json`, then atomic `selection.json`; `FinalizationResult(validation_path, selection_path)`; `ExportFinalizationError(code, message)`.

- [ ] **Step 1: Write failing finalizer tests with a fake inspector**

```python
# tests/test_export_finalizer.py
import hashlib
import json
from pathlib import Path

import pytest

from weld_agent.export_finalizer import ExportFinalizationError, finalize_export
from weld_agent.geometry.step_inspector import StepInspection


FIXTURES = Path(__file__).parent / "fixtures"


class FakeInspector:
    def inspect(self, path: Path) -> StepInspection:
        return StepInspection(12, 0, (0, 0, 0, 100, 50, 5))


def _manifest(tmp_path: Path) -> Path:
    payload = json.loads((FIXTURES / "export_manifest.valid.json").read_text(encoding="utf-8"))
    payload["run_id"] = tmp_path.name
    for component in payload["components"]:
        step = tmp_path / f"component-{component['id']}.step"
        step.write_bytes(f"STEP-{component['id']}".encode("ascii"))
        component["step_path"] = str(step.resolve())
        component["summary"]["bbox"] = [0, 0, 0, 100, 50, 5]
    path = tmp_path / "export-manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_finalize_writes_valid_selection_after_validation(tmp_path: Path) -> None:
    result = finalize_export(
        _manifest(tmp_path),
        FIXTURES / "integration_profile.valid.json",
        FakeInspector(),
    )
    selection = json.loads(result.selection_path.read_text(encoding="utf-8"))
    validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
    expected = hashlib.sha256((tmp_path / "component-15.step").read_bytes()).hexdigest()
    assert selection["components"][0]["geometry"]["sha256"] == expected
    assert validation["status"] == "success"


def test_bbox_mismatch_writes_failure_report_but_no_selection(tmp_path: Path) -> None:
    class MismatchInspector:
        def inspect(self, path: Path) -> StepInspection:
            return StepInspection(1, 0, (0, 0, 0, 1000, 500, 50))

    with pytest.raises(ExportFinalizationError) as caught:
        finalize_export(
            _manifest(tmp_path),
            FIXTURES / "integration_profile.valid.json",
            MismatchInspector(),
        )
    assert caught.value.code == "EXPORT_MISMATCH"
    assert not (tmp_path / "selection.json").exists()
    report = json.loads((tmp_path / "export-validation.json").read_text(encoding="utf-8"))
    assert report["status"] == "failure"
```

- [ ] **Step 2: Run tests and verify the finalizer is absent**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_export_finalizer.py -v
```

Expected: collection FAIL with `No module named 'weld_agent.export_finalizer'`.

- [ ] **Step 3: Implement deterministic comparison and atomic outputs**

Use these exact public types and helpers in `export_finalizer.py`:

```python
from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from weld_agent.contracts import ContractValidationError, load_document, validate_document
from weld_agent.geometry.step_inspector import PythonOccStepInspector, StepInspectionError, StepInspector


@dataclass(frozen=True)
class FinalizationResult:
    validation_path: Path
    selection_path: Path


class ExportFinalizationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _bbox_delta(source: list[float], imported: tuple[float, ...]) -> list[float]:
    return [float(actual - expected) for expected, actual in zip(source, imported, strict=True)]


def _bbox_matches(source: list[float], imported: tuple[float, ...], absolute: float, relative: float) -> bool:
    return all(
        math.isclose(expected, actual, abs_tol=absolute, rel_tol=relative)
        for expected, actual in zip(source, imported, strict=True)
    )
```

Implement `finalize_export` in this fixed order:

1. Refuse if `selection.json` or `export-validation.json` already exists (`OUTPUT_CONFLICT`) and leave all existing files untouched.
2. Load and validate manifest and profile.
3. Require `manifest_path.parent.name == manifest["run_id"]` so run products cannot be mixed.
4. For each component, resolve `step_path`, require its parent to be the manifest directory, require a non-empty regular file, compute SHA-256, call the injected inspector, compare six bbox coordinates, and append a component report.
5. Before manifest validation, derive the failure-report run ID from `manifest_path.parent.name`; if it violates the run-ID regex, use `unknown`. Map `ContractValidationError` to `MANIFEST_INVALID`, STEP file `OSError` to `STEP_READ_FAILED`, retain a `StepInspectionError.code`, and classify bbox mismatch as `EXPORT_MISMATCH`. Write a failure `export-validation.json` with the component reports completed so far and `{code, message}`, then raise `ExportFinalizationError` with the same code. The preflight `OUTPUT_CONFLICT` case is the only failure that deliberately writes no report.
6. Validate and atomically write a success `export-validation.json`.
7. Build the existing selection shape from manifest identity/source summaries plus profile parameters, validate it, and atomically write `selection.json`.
8. Return both paths.

Do not catch `KeyboardInterrupt` or `SystemExit`. Default the inspector only at the CLI boundary with `PythonOccStepInspector()` so tests always inject their dependency explicitly.

Use this implementation shape so error classification and report timing are unambiguous:

```python
def finalize_export(
    manifest_path: Path,
    profile_path: Path,
    inspector: StepInspector,
) -> FinalizationResult:
    run_dir = manifest_path.resolve().parent
    validation_path = run_dir / "export-validation.json"
    selection_path = run_dir / "selection.json"
    if validation_path.exists() or selection_path.exists():
        raise ExportFinalizationError("OUTPUT_CONFLICT", "final output already exists")

    run_id_hint = run_dir.name if RUN_ID.fullmatch(run_dir.name) else "unknown"
    component_reports: list[dict[str, Any]] = []
    warnings: list[str] = []

    try:
        try:
            manifest = load_document(manifest_path, "export-manifest.schema.json")
        except ContractValidationError as exc:
            raise ExportFinalizationError("MANIFEST_INVALID", str(exc)) from exc
        if manifest["run_id"] != run_dir.name:
            raise ExportFinalizationError(
                "OUTPUT_CONFLICT", "manifest run_id does not match its directory"
            )
        run_id_hint = manifest["run_id"]
        warnings = list(manifest["warnings"])

        try:
            profile = load_document(profile_path, "integration-profile.schema.json")
        except ContractValidationError as exc:
            raise ExportFinalizationError("PROFILE_INVALID", str(exc)) from exc

        selection_components = []
        for component in manifest["components"]:
            step_path = Path(component["step_path"]).resolve()
            if step_path.parent != run_dir:
                raise ExportFinalizationError(
                    "OUTPUT_CONFLICT", f"STEP is outside run directory: {step_path}"
                )
            if not step_path.is_file() or step_path.stat().st_size == 0:
                raise ExportFinalizationError(
                    "STEP_READ_FAILED", f"missing or empty STEP: {step_path}"
                )

            digest = _sha256(step_path)
            inspection = inspector.inspect(step_path)
            source_bbox = component["summary"]["bbox"]
            delta = _bbox_delta(source_bbox, inspection.bbox)
            matches = _bbox_matches(
                source_bbox,
                inspection.bbox,
                profile["bbox_absolute_tolerance"],
                profile["bbox_relative_tolerance"],
            )
            component_reports.append({
                "id": component["id"],
                "step_path": str(step_path),
                "file_size": step_path.stat().st_size,
                "sha256": digest,
                "read_status": "success",
                "face_count": inspection.face_count,
                "solid_count": inspection.solid_count,
                "occ_bbox": list(inspection.bbox),
                "bbox_delta": delta,
                "checks_passed": matches,
            })
            if not matches:
                raise ExportFinalizationError(
                    "EXPORT_MISMATCH",
                    f"bbox mismatch for Component {component['id']}",
                )
            selection_components.append({
                "id": component["id"],
                "name": component["name"],
                "geometry": {"path": str(step_path), "format": "STEP", "sha256": digest},
                "summary": component["summary"],
            })

        success_report = {
            "schema_version": "1.0", "run_id": run_id_hint, "status": "success",
            "components": component_reports, "warnings": warnings, "errors": [],
        }
        validate_document("export-validation.schema.json", success_report)
        _write_json_atomic(validation_path, success_report)

        selection = {
            "schema_version": "1.0",
            "run_id": run_id_hint,
            "hypermesh": manifest["hypermesh"],
            "components": selection_components,
            "parameters": profile["parameters"],
        }
        validate_document("selection.schema.json", selection)
        _write_json_atomic(selection_path, selection)
        return FinalizationResult(validation_path, selection_path)
    except StepInspectionError as exc:
        failure = ExportFinalizationError(exc.code, str(exc))
    except OSError as exc:
        failure = ExportFinalizationError("STEP_READ_FAILED", str(exc))
    except ContractValidationError as exc:
        failure = ExportFinalizationError("MANIFEST_INVALID", str(exc))
    except ExportFinalizationError as exc:
        failure = exc

    if validation_path.exists():
        validation_path.unlink()
    failure_report = {
        "schema_version": "1.0", "run_id": run_id_hint, "status": "failure",
        "components": component_reports, "warnings": warnings,
        "errors": [{"code": failure.code, "message": str(failure)}],
    }
    validate_document("export-validation.schema.json", failure_report)
    _write_json_atomic(validation_path, failure_report)
    raise failure
```

Import `RUN_ID` from `weld_agent.run_workspace`. Add `PROFILE_INVALID` to the documented error vocabulary in the module docstring. The success report is deliberately written before selection; the exception path removes it before writing a failure report, so a success report can never remain without selection.

- [ ] **Step 4: Add the CLI test and `finalize-export` command**

```python
# tests/test_export_cli.py
from pathlib import Path

from weld_agent.export_finalizer import FinalizationResult
from weld_agent.cli import main


def test_finalize_export_dispatches_and_prints_selection(tmp_path: Path, monkeypatch, capsys) -> None:
    manifest = tmp_path / "export-manifest.json"
    profile = tmp_path / "profile.json"
    selection = tmp_path / "selection.json"
    validation = tmp_path / "export-validation.json"
    manifest.write_text("{}", encoding="utf-8")
    profile.write_text("{}", encoding="utf-8")

    def fake_finalize(manifest_path, profile_path, inspector):
        assert manifest_path == manifest
        assert profile_path == profile
        return FinalizationResult(validation, selection)

    monkeypatch.setattr("weld_agent.cli.finalize_export", fake_finalize)
    exit_code = main([
        "finalize-export", "--manifest", str(manifest), "--profile", str(profile)
    ])
    assert exit_code == 0
    assert capsys.readouterr().out.strip() == str(selection)
```

Extend `_parser()`:

```python
finalize = subparsers.add_parser("finalize-export")
finalize.add_argument("--manifest", type=Path, required=True)
finalize.add_argument("--profile", type=Path, required=True)
```

Dispatch it before `analyze`:

```python
if args.command == "finalize-export":
    result = finalize_export(args.manifest, args.profile, PythonOccStepInspector())
    print(result.selection_path)
    return 0
```

Add `ExportFinalizationError` and `StepInspectionError` to the existing classified CLI exception tuple so failures print one `error:` line and return exit code 2.

- [ ] **Step 5: Run finalizer/CLI tests and commit**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_export_finalizer.py tests/test_export_cli.py tests/test_workflow_cli.py -v
```

Expected: PASS, including the existing analyze and validate commands.

Commit:

```powershell
git add src/weld_agent/export_finalizer.py src/weld_agent/cli.py tests/test_export_finalizer.py tests/test_export_cli.py
git commit -m "feat: finalize STEP exports into selection input"
```

---

### Task 4: Implement the Tcl 8.5 HyperMesh Export Adapter

**Files:**
- Create: `hypermesh/tcl/weld_agent_export.tcl`
- Create: `tests/test_hypermesh_export_tcl.py`

**Interfaces:**
- Consumes: `::weldagent::run_export_probe output_root`; an interactive mark containing exactly two Component IDs.
- Produces: `%TEMP%/hypermesh-weld-agent/<run-id>/component-<id>.step` and `export-manifest.json`; returns the manifest path.

- [ ] **Step 1: Write the Tcl command-stub tests**

Use a standalone Altair Tcl harness so no real HyperMesh model is needed for automated tests:

```python
# tests/test_hypermesh_export_tcl.py
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
    candidates = sorted(Path("C:/Program Files/Altair").glob("*/hw/tcl/*/win64/bin/tclsh*.exe"))
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
        [str(tclsh)], input=source, text=True, capture_output=True,
        check=False, timeout=20,
    )


def _line(stdout: str, prefix: str) -> str:
    return next(line.removeprefix(prefix) for line in stdout.splitlines() if line.startswith(prefix))


def test_export_emits_two_steps_and_restores_display(tmp_path: Path) -> None:
    completed = _run_harness(tmp_path, fail_on=-1)
    assert completed.returncode == 0, completed.stderr
    manifest_path = Path(_line(completed.stdout, "MANIFEST="))
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_document("export-manifest.schema.json", payload)
    assert [item["id"] for item in payload["components"]] == [15, 20]
    assert [Path(item["step_path"]).name for item in payload["components"]] == [
        "component-15.step", "component-20.step",
    ]
    assert payload["export_options"]["units"] == "Millimeters"
    assert _line(completed.stdout, "EXPORTED=") == "15 20"
    assert _line(completed.stdout, "VISIBLE=") == "1 15 20"


def test_second_export_failure_cleans_steps_and_restores_display(tmp_path: Path) -> None:
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
```

- [ ] **Step 2: Run the test and verify the script is absent**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_hypermesh_export_tcl.py -v
```

Expected: FAIL because `hypermesh/tcl/weld_agent_export.tcl` is missing.

- [ ] **Step 3: Implement focused Tcl helpers**

The script must define these procs inside the existing `::weldagent` namespace:

```tcl
proc ::weldagent::component_summary {component_id} {
    *clearmark surfaces 1
    *createmark surfaces 1 "by comp id" $component_id
    set surface_count [hm_marklength surfaces 1]
    if {$surface_count == 0} {
        error "EMPTY_COMPONENT_GEOMETRY: Component $component_id has no surfaces"
    }
    set bbox [hm_getboundingbox surfaces 1 1 0 0]

    *clearmark solids 1
    *createmark solids 1 "by comp id" $component_id
    set solid_count [hm_marklength solids 1]

    *clearmark elements 1
    *createmark elements 1 "by comp id" $component_id
    set element_count [hm_marklength elements 1]

    return [list $surface_count $solid_count $element_count $bbox]
}

proc ::weldagent::set_visible_components {component_ids} {
    *displaycollectorwithfilter components "none" "" 1 0
    if {[llength $component_ids] > 0} {
        *clearmark components 2
        eval *createmark components 2 $component_ids
        *displaycollectorsbymark components 2 on 1 0
    }
}

proc ::weldagent::export_component_step {component_id step_path} {
    ::weldagent::set_visible_components [list $component_id]
    set options [list \
        "Version=AP214" "LayerMode=None" "Export=Displayed" \
        "Units=Millimeters" "GeometryMode=Standard" \
        "TopologyMode=Solid/Shell" "AssemblyMode=Hierarchy" \
        "WriteNameFrom=Component" "OptimizeForCAD=Off"]
    *geomexport "step_ct" $step_path $options
    if {![file isfile $step_path] || [file size $step_path] <= 0} {
        error "EXPORT_FAILED: missing or empty STEP for Component $component_id"
    }
}
```

Make the exporter standalone by defining the JSON helpers and writer in the same file:

```tcl
proc ::weldagent::json_escape {value} {
    return [string map [list "\\" "\\\\" "\"" "\\\"" "\n" "\\n" "\r" "\\r" "\t" "\\t"] $value]
}

proc ::weldagent::json_number_array {values} {
    return "\[[join $values {, }]\]"
}

proc ::weldagent::component_record_json {record} {
    lassign $record component_id name step_path summary
    lassign $summary surface_count solid_count element_count bbox
    return [format {    {
      "id": %d,
      "name": "%s",
      "step_path": "%s",
      "summary": {
        "surface_count": %d,
        "solid_count": %d,
        "element_count": %d,
        "bbox": %s
      }
    }} $component_id \
        [::weldagent::json_escape $name] \
        [::weldagent::json_escape $step_path] \
        $surface_count $solid_count $element_count \
        [::weldagent::json_number_array $bbox]]
}

proc ::weldagent::write_export_manifest {run_dir run_id component_records} {
    set model_file [hm_info currentfile]
    set warnings_json ""
    if {$model_file eq ""} {
        set model_name "Untitled"
        set warnings_json {"HyperMesh model has not been saved; model_name is Untitled"}
    } else {
        set model_name [file rootname [file tail $model_file]]
    }
    set build [hm_info -appinfo DISPLAYVERSION]
    set component_json {}
    foreach record $component_records {
        lappend component_json [::weldagent::component_record_json $record]
    }

    set target [file join $run_dir "export-manifest.json"]
    set temporary "$target.tmp"
    set stream [open $temporary w]
    fconfigure $stream -encoding utf-8 -translation lf
    set write_status [catch {
        puts $stream "{"
        puts $stream {  "schema_version": "1.0",}
        puts $stream [format {  "run_id": "%s",} [::weldagent::json_escape $run_id]]
        puts $stream "  \"hypermesh\": {"
        puts $stream [format {    "build": "%s",} [::weldagent::json_escape $build]]
        puts $stream [format {    "model_name": "%s",} [::weldagent::json_escape $model_name]]
        puts $stream {    "units": "mm",}
        puts $stream {    "coordinate_system": "global"}
        puts $stream {  },}
        puts $stream "  \"export_options\": {"
        puts $stream {    "cad_type": "step_ct", "version": "AP214",}
        puts $stream {    "units": "Millimeters", "export": "Displayed",}
        puts $stream {    "layer_mode": "None", "geometry_mode": "Standard",}
        puts $stream {    "topology_mode": "Solid/Shell", "assembly_mode": "Hierarchy",}
        puts $stream {    "write_name_from": "Component", "optimize_for_cad": "Off"}
        puts $stream {  },}
        puts $stream {  "components": [}
        puts $stream [join $component_json ",\n"]
        puts $stream {  ],}
        puts $stream [format {  "warnings": [%s]} $warnings_json]
        puts $stream "}"
    } write_message]
    set close_status [catch {close $stream} close_message]
    if {$write_status != 0 || $close_status != 0} {
        if {[file isfile $temporary]} { file delete -force $temporary }
        if {$write_status != 0} { error $write_message }
        error $close_message
    }
    file rename $temporary $target
    return [file normalize $target]
}
```

The manifest emitted by the Tcl harness must validate against `export-manifest.schema.json` without Python post-processing.

- [ ] **Step 4: Implement the Tcl entrypoint with centralized cleanup**

Use this control structure; do not replace it with Tcl 8.6 `try`:

```tcl
proc ::weldagent::run_export_probe {output_root} {
    *clearmark components 1
    *createmarkpanel components 1 "Select exactly two Components for Weld Agent STEP export"
    set selected_ids [hm_getmark components 1]
    if {[llength $selected_ids] != 2 || [lindex $selected_ids 0] == [lindex $selected_ids 1]} {
        error "INVALID_SELECTION: select exactly two distinct Components"
    }

    *clearmark components 2
    *createmark components 2 displayed
    set original_visible [hm_getmark components 2]

    set run_id "hm-[clock format [clock seconds] -format %Y%m%d-%H%M%S]-[pid]"
    set run_dir [file normalize [file join $output_root $run_id]]
    if {[file exists $run_dir]} {
        error "OUTPUT_CONFLICT: run directory already exists: $run_dir"
    }
    file mkdir $run_dir

    set created_steps {}
    set status [catch {
        set component_records {}
        foreach component_id $selected_ids {
            set name [hm_getvalue components id=$component_id dataname=name]
            set summary [::weldagent::component_summary $component_id]
            set step_path [file normalize [file join $run_dir "component-$component_id.step"]]
            lappend created_steps $step_path
            ::weldagent::export_component_step $component_id $step_path
            lappend component_records [list $component_id $name $step_path $summary]
        }
        set manifest_path [::weldagent::write_export_manifest $run_dir $run_id $component_records]
    } message]

    set restore_status [catch {::weldagent::set_visible_components $original_visible} restore_message]
    if {$status != 0 || $restore_status != 0} {
        foreach step_path $created_steps {
            if {[file isfile $step_path]} { file delete -force $step_path }
        }
        foreach artifact [list \
            [file join $run_dir "export-manifest.json"] \
            [file join $run_dir "export-manifest.json.tmp"]] {
            if {[file isfile $artifact]} { file delete -force $artifact }
        }
        if {$restore_status == 0} { error $message }
        error "DISPLAY_RESTORE_FAILED: $restore_message"
    }
    return $manifest_path
}
```

`write_export_manifest` obtains build via `hm_info -appinfo DISPLAYVERSION`; obtains the current model with `hm_info currentfile`, mapping an empty value to `Untitled` and adding a warning. It writes a temporary `.tmp`, closes it, and renames it into place. If manifest writing fails, the entrypoint treats it like export failure and deletes the two STEP files.

- [ ] **Step 5: Run Tcl tests, contract-validate the emitted manifest, and commit**

Run:

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pytest tests/test_hypermesh_export_tcl.py tests/test_hypermesh_tcl_adapter.py -v
```

Expected: PASS on the installed Altair Tcl 8.5 runtime.

Commit:

```powershell
git add hypermesh/tcl/weld_agent_export.tcl tests/test_hypermesh_export_tcl.py
git commit -m "feat: export isolated HyperMesh components to STEP"
```

---

### Task 5: Document and Verify the Real HyperMesh/OCC Round Trip

**Files:**
- Create: `docs/manual-tests/hm2017-step-export-probe.md`
- Modify: `README.md`
- Modify: `docs/setup.md`
- Modify: `scripts/verify.ps1`

**Interfaces:**
- Consumes: an open real HyperMesh model, the Tcl exporter, `finalize-export`, and `config/integration-probe-1.json`.
- Produces: reproducible manual instructions and one-command local automated verification.

- [ ] **Step 1: Add the manual runbook with exact commands**

Document these HyperMesh command-window commands:

```tcl
source {C:/Users/25335/Documents/GitHub/hypermesh-weld-agent/hypermesh/tcl/weld_agent_export.tcl}
set manifest [::weldagent::run_export_probe {C:/Users/25335/AppData/Local/Temp/hypermesh-weld-agent}]
puts "MANIFEST=$manifest"
```

Tell the tester to select Component 15 `6101081-DD01-A` and Component 20 `6101161-DD01-A`, record the displayed Component IDs and entity/Connector counts before and after, and confirm they are unchanged.

Use these exact HyperMesh queries before and after the export:

```tcl
*clearmark components 1
*createmark components 1 displayed
puts "DISPLAYED_COMPONENTS=[hm_getmark components 1]"
foreach entity_type {surfaces solids elements connectors} {
    *clearmark $entity_type 1
    *createmark $entity_type 1 all
    puts "[string toupper $entity_type]_COUNT=[hm_marklength $entity_type 1]"
}
```

Document the PowerShell finalization command without a committed absolute interpreter path:

```powershell
$occPython = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
$manifestPath = Read-Host 'Paste MANIFEST path printed by HyperMesh'
& $occPython -m weld_agent.cli finalize-export `
  --manifest $manifestPath `
  --profile '.\config\integration-probe-1.json'
```

Then validate both final documents:

```powershell
$runDir = Split-Path -Parent $manifestPath
& $occPython -m weld_agent.cli validate --schema export-validation.schema.json --input (Join-Path $runDir 'export-validation.json')
& $occPython -m weld_agent.cli validate --schema selection.schema.json --input (Join-Path $runDir 'selection.json')
```

The runbook must state that generated STEP and JSON files stay under `%TEMP%`, are diagnostic customer data, and must not be committed or uploaded.

- [ ] **Step 2: Update project entry points and verification**

Update README current boundary to say the repository now supports verified two-Component STEP export input, while real weld recognition, preview, Connector and Agent remain absent. Link both the design and manual runbook.

Update `docs/setup.md` interface list with:

```text
HyperMesh 导出：hypermesh/tcl/weld_agent_export.tcl
中间合同：schemas/export-manifest.schema.json
OCC 最终化：python -m weld_agent.cli finalize-export --manifest $manifestPath --profile config/integration-probe-1.json
```

Keep `scripts/verify.ps1` using the explicitly supplied OCC interpreter and add no hard-coded local path. Pytest already discovers all new tests, so only add a comment identifying that OCC integration tests are intentionally part of the full local run.

- [ ] **Step 3: Run the full automated verification**

Run:

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

Expected:

- all pytest tests PASS;
- runtime doctor reports Python 3.11.15 and OCC 7.9.0 available;
- `git diff --check` passes.

- [ ] **Step 4: Commit documentation and verification updates**

```powershell
git add README.md docs/setup.md docs/manual-tests/hm2017-step-export-probe.md scripts/verify.ps1
git commit -m "docs: add HyperMesh STEP round-trip runbook"
```

- [ ] **Step 5: Perform the real-model checkpoint with the user**

Run the documented HyperMesh procedure on the open car-door model. Do not claim the probe complete until the user supplies the emitted manifest/finalization results and confirms display/entity counts are unchanged. Record only non-sensitive counts, IDs, command status and bounding-box deltas in the task report; never add the real STEP or run JSON to Git.

---

## Final Acceptance Checklist

- [ ] `export-manifest.json`, integration profile, validation report and final selection all pass their schemas.
- [ ] Two different Component IDs map to two different absolute, non-empty STEP paths.
- [ ] PythonOCC reads both files, transfers roots, finds non-empty topology and finite bounding boxes.
- [ ] HyperMesh/OCC bounding boxes pass the explicit integration profile tolerances.
- [ ] Failure creates a classified validation report and never leaves a formal `selection.json`.
- [ ] Tcl success/failure tests prove exact display-state restoration and partial STEP cleanup.
- [ ] Existing Stage 0 tests and CLI commands remain green.
- [ ] Real Component 15/20 run confirms no model, entity-count, Connector-count or display-state change.
- [ ] No customer geometry, runtime outputs or machine-specific interpreter paths are tracked by Git.
