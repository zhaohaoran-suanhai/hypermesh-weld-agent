# ADR-0002：PythonOCC 作为无 GUI 外部几何内核

## Status

Accepted

## Context

HyperMesh 2017 Tcl 适合读取会话实体和导出几何，但复杂 B-Rep 遍历、曲面类型、质心、包围盒和求交更适合 OCC。把 OCC GUI 作为正式入口会引入 Qt/桌面依赖，难以进行 pytest、batch 和终端审计。让 OCC 对象扩散到工作流层又会把业务规则绑死在库 API 上。

## Decision

PythonOCC/OpenCascade 在独立 Python 3.11 进程中作为 headless geometry kernel。正式代码只使用 `OCC.Core`，不导入 `OCC.Display`。OCC 类型停留在 `src/weld_agent/geometry/` adapter，跨层返回普通 Python dataclass、tuple、dict 和数值；上层依赖 `StepInspector`、`MarkerStepReader` 等 Protocol。

## Consequences

- 几何 adapter 可用合成 Shape/STEP 自动测试；
- 领域逻辑可用 fake adapter 测试，不需要 OCC runtime；
- 正式执行适用于终端和未来 batch/CI；
- 如需可视调试，必须作为可选工具单独设计，不能成为生产合同；
- STEP 与普通数据的转换边界需要明确错误和有限值校验。
