# HyperMesh 2017 接口

本页说明如何在当前 HyperMesh 2017 中调用仓库 Tcl、什么已经验证、哪些操作会影响模型状态，以及如何安全扩展。

## 三种入口

| 入口 | 用途 | 当前状态 |
|---|---|---|
| `hmopengl.exe` GUI | 打开模型、人工选择、Tcl Console、可视检查 | 已用于能力探针和 STEP 导出验收 |
| Tcl Console | `source` 版本化脚本并调用 `::weldagent` proc | 当前主要集成入口 |
| `hmbatch.exe` | 未来的无界面、无交互批处理 | executable 已存在；现有交互 proc 未宣称 batch-safe |

`hw.exe` 可作为 HyperWorks 总入口，但本仓库的 HM2017 验收以 `hmopengl.exe` 中的 HyperMesh/Tcl Console 为准。

## 在 GUI 中运行仓库 Tcl

1. 用 HyperMesh 2017 打开目标模型；
2. 打开 `View > Tcl Console`（不同工作区菜单名称可能略有差异）；
3. 用正斜杠路径加载脚本：

```tcl
source {<repo>/hypermesh/tcl/weld_agent_probe.tcl}
```

4. 调用公开 proc，并把输出写到仓库外唯一临时目录：

```tcl
::weldagent::run_probe {<temp>/hypermesh-weld-agent/hm2017-probe.json}
```

不要在 Console 临时粘贴一大段未版本化 Tcl 作为正式实现。探索命令确认后应进入 `hypermesh/tcl/`，并配套测试和 runbook。

## 当前公开 Tcl 接口

### `weld_agent_probe.tcl`

| proc | 输入 | 输出/作用 |
|---|---|---|
| `::weldagent::command_available name` | HM 命令名 | 命令是否存在 |
| `::weldagent::run_probe output_path` | JSON 输出路径 | 交互选择两个 Component，写能力与身份报告 |

探针使用 `hm_getvalue` 读取名称，并确认 `*geomexport`、旧 `*geomoutputdata` 和 `*CE_ConnectorCreate` 的存在性。命令存在不等于已授权执行，尤其是 Connector 命令。

### `weld_agent_export.tcl`

| proc | 职责 |
|---|---|
| `::weldagent::component_summary component_id` | Surface/Solid/Element 数和 `hm_getboundingbox` |
| `::weldagent::displayed_component_ids entity_types` | 查询按 entity type 当前显示的 Component |
| `::weldagent::set_component_display_state element_ids geometry_ids` | 精确设置显示状态 |
| `::weldagent::export_component_step component_id step_path` | 隔离后用 `*geomexport` 写 STEP AP214/mm |
| `::weldagent::write_export_manifest run_dir run_id records` | 原子写 JSON manifest |
| `::weldagent::run_export_probe output_root` | 交互选择两个 Component、逐个导出并恢复状态 |

公开入口返回 manifest 路径；外部 Python 再做 Schema/OCC 校验。Tcl 不负责 OCC 分析。

## mark 与查询约定

- mark ID 是 HyperMesh 会话中的临时工作区，不是持久身份；
- `*createmarkpanel components 1 ...` 会等待人工选择；
- `hm_getmark components 1` 返回 Component ID；
- `hm_getvalue` 用于名称、collector 等查询；
- `hm_getboundingbox` 应针对包含 Surface 的 mark 查询；空 Component mark 可能返回 `No entities found`；
- 查询 Surface 全局包围盒时先建立 Surface mark，并核对 `hm_marklength`。

新脚本必须明确使用哪个 mark ID、会覆盖什么临时 mark，以及调用结束后是否需要清理。

## STEP 导出合同

- 当前使用 `*geomexport "step_ct"`；
- profile 固定 STEP AP214 和 Millimeters；
- 每个 Component 单独导出，避免 OCC 侧丢失来源身份；
- 导出后立即检查文件存在且非空；
- Tcl manifest 保存 Component ID、名称、数量、包围盒、单位、坐标系和绝对 STEP 路径；
- 外部 Python 负责再次读取和验证，HyperMesh 成功返回不是最终几何成功证据。

## 状态恢复与错误

状态恢复是接口合同，不是 UI 细节：

1. 进入导出前记录 element 与 geometry 的显示 Component；
2. 主流程放入 `catch`；
3. 无论主流程成功或失败，独立执行恢复；
4. 主流程错误与恢复错误都保留，不能用恢复失败覆盖原始原因；
5. 不自动保存 `.hm`，不修改 Component 归属、网格或 Connector。

导出失败使用明确错误，例如 `EXPORT_FAILED`。新的 Tcl 功能也应使用稳定错误前缀，使外部工作流能分类而不是匹配整段自然语言。

## GUI 与 batch 边界

包含 `*createmarkpanel` 的 proc 依赖 GUI 交互，不能直接当成 `hmbatch.exe` 入口。要支持 batch，需新增无交互 proc，让 Component ID、输入模型和输出目录成为显式参数，并单独验证：

- 命令在 batch 环境存在；
- 模板/profile 初始化一致；
- 输入模型只读打开还是允许保存；
- exit code、stdout/stderr 和输出合同；
- license 与工作目录错误。

在完成这些验证前，batch 只是候选能力。

## 新 HyperMesh 功能的安全清单

1. 用只读探针确认 HM2017 命令和返回格式；
2. 明确实体类型、mark、单位、坐标系和模板/profile；
3. 定义 proc 的显式输入、输出文件和错误前缀；
4. 记录所有将改变的选择、显示或模型状态；
5. 用 `catch` 保证成功/失败后的状态恢复；
6. 为跨进程数据先定义 JSON Schema；
7. 添加 Tcl 静态测试和真实 runbook；
8. 若功能可能保存、删除、write-back 或创建 Connector，先停下并取得用户对确切操作的授权。

跨到外部 OCC 的完整模式见 [HyperMesh/OCC 文件桥](hypermesh-occ-bridge.md)。
