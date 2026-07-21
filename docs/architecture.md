# 当前架构

本页描述当前代码实际存在的架构，不描述尚未实现的理想系统。

## 总体数据流

```text
HyperMesh 2017 当前模型 / HyperMesh Tcl
  -> 选择、查询摘要、隔离显示、STEP 导出、状态恢复
  -> 唯一临时运行目录：STEP + JSON manifest
  -> schemas/ JSON Schema 校验
  -> src/weld_agent/geometry/ PythonOCC adapter
  -> 普通 Python 领域工作流
  -> JSON/CSV/log
  -> 人工复核
  -> 只有单独授权后才允许 HyperMesh write-back 或 Connector 操作
```

HyperMesh 与外部 Python 不共享进程内对象。STEP 承载 B-Rep 几何，JSON 承载身份、单位、坐标系、路径和摘要；Schema 是 Tcl、Python 和未来 Agent 工具之间的稳定边界。

## 模块职责

| 路径 | 当前职责 | 不应承担 |
|---|---|---|
| `hypermesh/tcl/` | HM2017 选择、查询、隔离、导出、恢复和能力探针 | OCC 几何计算、隐藏保存、未经授权的 Connector 创建 |
| `schemas/` | 跨进程 JSON 合同和字段约束 | 几何算法实现 |
| `src/weld_agent/contracts.py` | 加载 Schema、结构与跨字段校验 | 读取 OCC Shape |
| `src/weld_agent/geometry/` | STEP/OCC 适配、拓扑观察和纯几何分类 | HyperMesh UI 控制、业务 write-back |
| `src/weld_agent/export_finalizer.py` | 校验双 Component 导出并生成 selection | 识别实际焊点 |
| `src/weld_agent/marker_identification.py` | 编排 marker 识别、排序、原子写 JSON/CSV/log | 创建 Connector |
| `src/weld_agent/providers/` | `CandidateProvider` 扩展边界；当前 fixture 只验证管线 | 声称 fixture 是真实算法 |
| `src/weld_agent/cli.py` | 稳定终端入口和错误码 | 隐藏启动 GUI |
| `scripts/` | PowerShell 环境检查、可见终端入口和完整验证 | 猜测或固化私有 Python 路径 |
| `tests/` | 合同、纯 Python、合成 OCC、Tcl 静态和 CLI 测试 | 提交客户模型作为 fixture |

OCC 类型只能停留在 `src/weld_agent/geometry/` adapter。工作流层接收 dataclass、tuple、dict 和其他普通 Python 数据，因此可以用 fake reader 和合成几何测试。

## 已实现流程 A：双 Component STEP 导出

1. `::weldagent::run_export_probe` 在 HyperMesh 中要求选择恰好两个 Component；
2. Tcl 记录原显示状态，逐个隔离并用 `*geomexport` 输出 STEP；
3. Tcl 写 `export-manifest.json`，无论成功或失败都尝试恢复显示；
4. `finalize-export` 用 `export-manifest.schema.json` 校验身份、单位和路径；
5. `PythonOccStepInspector` 读取 STEP，与 HyperMesh 摘要比较并写 `export-validation.json`、`selection.json`。

这一流程证明了 HyperMesh → STEP/JSON → OCC 的桥接能力，不等于真实焊点算法。

## 已实现流程 B：多 Component 显式 marker 识别

1. 本地 `marker-input-manifest.json` 明确列出一个或多个 Component STEP；
2. `PythonOccMarkerReader` 将每个 STEP Solid 转为普通 `SolidObservation`；
3. 纯 Python 分类器输出 `cylinder`、`triangular_prism` 或 `unknown` 和证据；
4. 工作流按 Component/Solid 稳定排序，验证 `weld-markers.schema.json`；
5. 原子写入 `weld-markers.json`、`weld-markers.csv` 和日志。

## 合同地图

| Schema | 生产者 → 消费者 |
|---|---|
| `hypermesh-probe.schema.json` | HM 能力探针 → Python 校验/人工检查 |
| `export-manifest.schema.json` | HyperMesh Tcl → `finalize-export` |
| `export-validation.schema.json` | `finalize-export` → 人工/自动检查 |
| `selection.schema.json` | 导出最终化 → `CandidateProvider` 工作流 |
| `marker-input-manifest.schema.json` | 明确的 STEP 清单 → marker 识别工作流 |
| `weld-markers.schema.json` | marker 识别工作流 → 人工复核/未来下游 |
| `weld-candidates.schema.json` | candidate provider → advisory 候选结果 |

所有几何相关合同当前使用毫米和全局坐标系。若要支持其他单位或局部坐标系，应先修改合同与测试，不能在适配器中静默换算。

## 错误与副作用边界

- 文件损坏、合同错误、单位错误或空几何导致分类错误码和非零退出；
- 单个有限但不支持的 Solid 输出 `unknown`，不静默丢弃；
- 输出先写临时文件再原子替换；同一运行结果不默认覆盖；
- HyperMesh 查询和导出可以改变临时 mark/显示状态，但必须恢复；
- 当前 Python/OCC 工作流不修改 `.hm`；任何 write-back 都应使用单独接口、预览和用户批准。

具体本机协作接口见 [integrations/](integrations/)。
