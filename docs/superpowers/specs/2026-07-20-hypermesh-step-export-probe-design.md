# HyperMesh 2017 双 Component STEP 导出探针设计规格

日期：2026-07-20
状态：会话设计已批准，等待书面规格复核
适用阶段：MVP-A / 阶段 1 的几何导出入口

## 1. 目的

本探针用于验证并固化以下最小闭环：用户在一个 HyperMesh 车门模型中明确选择两个钣金 Component，系统在不修改原始模型的前提下，将它们分别导出为两个可追溯的 STEP 文件，并由 PythonOCC 验证导出结果，最终生成符合现有合同的 `selection.json`。

这一阶段解决的是“选中的两个 Component 能否被可靠地交给外部几何模块”，不判断真实焊点，也不创建预览或 Connector。

## 2. 已确认事实

真实 HyperMesh 2017 车门模型中的能力探针结果为：

- `*geomexport` 可用；
- `*geomoutputdata` 可用；
- `*CE_ConnectorCreate` 可用；
- 模型包含 34 个 Component 和 17514 个显示 Surface；
- 显示 Surface 的整体包围盒尺寸约为 `1280.166 × 346.911 × 1325.448`；
- 该尺寸与汽车车门的毫米尺度一致，因此本集成探针明确使用毫米，不进行自动单位猜测。

首个真实集成样本使用：

- Component 15：`6101081-DD01-A`；
- Component 20：`6101161-DD01-A`。

## 3. 方案选择

采用“每个 Component 单独导出一个 STEP”的方案。

导出每个 Component 时，Tcl 临时隐藏其他 Component，只显示当前目标 Component，然后调用 `*geomexport`。完成两个导出后恢复运行前的显示状态。

没有采用把两个 Component 合并到同一 STEP 的方案，因为不同 STEP 读取器对装配层级和名称的保留并不完全一致，合并导出会削弱 Component 身份与几何之间的一一对应关系。旧的 `*geomoutputdata` 只作为后续显式兼容方案，不在首版中静默回退。

## 4. 总体数据流

```text
HyperMesh 中选择恰好两个 Components
    -> Tcl 校验选择并保存当前 Component 显示状态
    -> 仅显示 Component A，导出 component-<A-id>.step
    -> 仅显示 Component B，导出 component-<B-id>.step
    -> Tcl 恢复原始显示状态
    -> Tcl 写入 export-manifest.json
    -> Python 校验 manifest 和 STEP 文件
    -> PythonOCC 读取两个 STEP，统计拓扑并计算包围盒
    -> 对比 HyperMesh 源摘要与 OCC 导入摘要
    -> 写入 export-validation.json
    -> 所有检查通过后写入 selection.json
```

Tcl 与 Python 的职责保持分离：Tcl 负责 HyperMesh 内的选择、查询和导出；Python 负责文件摘要、合同校验和 OCC 读取。Tcl 不生成需要 SHA-256 或 OCC 结果的正式 `selection.json`。

这细化了总设计中“Tcl 导出临时几何并写入 `selection.json`”的概括描述：在实际接口里，Tcl 先写中间 manifest，Python 完成不可由 Tcl 可靠提供的 SHA-256 和 OCC 校验后再写正式 selection；对后续几何模块暴露的最终合同不变。

## 5. 运行目录与文件

每次运行使用仓库外的独立目录：

```text
%TEMP%\hypermesh-weld-agent\<run-id>\
├── component-<A-id>.step
├── component-<B-id>.step
├── export-manifest.json
├── export-validation.json
└── selection.json
```

`run-id` 必须满足现有 Schema 的格式限制，并在同一工作站上避免碰撞。临时 CAD 和客户模型信息不得提交到 Git，也不得由程序上传到网络。

文件写入顺序体现完成状态：

1. STEP 文件；
2. 两个 STEP 都成功后写 `export-manifest.json`；
3. PythonOCC 完成读取和对比后写 `export-validation.json`；
4. 仅在全部必需校验通过后写 `selection.json`。

存在旧的同名最终文件时，探针必须拒绝覆盖或使用新的 `run-id`，不得把新旧运行产物混合。

## 6. HyperMesh Tcl 导出职责

### 6.1 输入与选择

Tcl 入口接受一个输出根目录，并通过 HyperMesh 选择面板要求用户选择恰好两个不同的 Component。选择数量不为两个、ID 重复、Component 不存在或 Component 不包含可导出的 Surface/几何时立即失败。

模型可以尚未保存。此时 manifest 将模型名称记录为 `Untitled` 并产生警告，但不阻止导出；程序不得自动保存 `.hm` 文件。

### 6.2 源几何摘要

对每个 Component，Tcl 在导出前记录：

- Component ID 和名称；
- Surface、Solid 和 Element 数量；
- 由该 Component 的 Surface 或可用几何实体计算的轴对齐包围盒；
- HyperMesh build、模型名称、单位和全局坐标系声明。

已确认 `hm_getboundingbox components 1 1 0 0` 对当前 CAD Surface 模型会报告 `No entities found`。HyperMesh 2017 中经过真实模型验证的调用是：先把 Component 放入 mark，再使用 `hm_getboundingbox components 1 2 0 0`；其中 `entity_flag=2` 会对 Component 所包含的几何实体计算包围盒。不能退回使用默认的 `entity_flag=1`，也不能用 Surface 的离散表示代替 Component 几何包围盒。

### 6.3 显示状态与导出

运行开始时分别保存当前显示 FE 实体与 CAD 几何所属的 Component ID；HyperMesh 的这两个显示隔间必须独立恢复。每次导出执行：

1. 同时隐藏所有 Component 的 FE 与 CAD 几何；
2. 只在 CAD 几何隔间显示目标 Component；
3. 调用 `*geomexport` 导出 STEP；
4. 检查命令是否报错以及目标文件是否存在且非空。

成功或失败后，分别恢复原始 FE Component 集合和原始 CAD Component 集合，不能把两者合并成一个“显示 Component”列表。

首版 STEP 参数固定为：

- CAD 类型：`step_ct`；
- STEP 版本：AP214；
- 单位：Millimeters；
- Export：Displayed；
- LayerMode：None；
- GeometryMode：Standard；
- TopologyMode：Solid/Shell；
- AssemblyMode：Hierarchy；
- WriteNameFrom：Component；
- OptimizeForCAD：Off。

参数必须在 manifest 中显式记录，不能仅存在于 Tcl 的隐藏默认值中。

### 6.4 恢复保证

显示状态恢复是强制清理步骤，成功、取消或异常时都必须执行。目标状态是恢复运行前显示的 Component ID 集合，而不是简单执行“显示全部”。

HyperMesh 2017 使用 Tcl 8.5，因此实现采用 `catch` 和集中清理流程，不依赖 Tcl 8.6 的 `try/finally`。探针不得更改几何、网格、Component 归属、Connector 或当前模型文件。

## 7. `export-manifest.json` 合同

manifest 是 Tcl 与 Python 之间的中间合同，至少包含：

- Schema 版本和 `run_id`；
- HyperMesh build、模型名称、单位、坐标系；
- 固定的 STEP 导出参数；
- 两个 Component 的 ID、名称、源几何计数、源包围盒和 STEP 路径；
- Tcl 阶段的警告。

路径使用绝对路径，便于外部进程从任意工作目录读取。manifest 不包含 SHA-256，也不声称 STEP 已通过 OCC 检查。

应为 manifest 新增 JSON Schema，并沿用现有严格合同风格：必需字段明确、禁止未知字段、数组数量固定为两个、坐标与计数类型受约束。

## 8. PythonOCC 校验与最终化

Python 最终化命令读取 manifest 和显式指定的集成参数配置，执行：

1. JSON Schema 校验；
2. 检查两个 Component ID 和两个 STEP 路径互不重复；
3. 检查 STEP 文件存在、为普通文件且非空；
4. 计算每个 STEP 的 SHA-256；
5. 使用 `STEPControl_Reader` 读取并 transfer roots；
6. 确认得到非空 Shape；
7. 统计 Face 和 Solid 数量；
8. 使用 OCC 计算有限数值的轴对齐包围盒；
9. 将 OCC 包围盒与 HyperMesh 源包围盒按毫米坐标比较；
10. 写出完整校验报告；
11. 所有必需检查通过后，按现有 `selection.schema.json` 写出并再次校验 `selection.json`。

OCC Face/Solid 数量可能因 STEP 表达和读取过程与 HyperMesh Surface/Solid 数量不同，因此首版只要求两侧几何非空，不把拓扑计数相等作为通过条件。拓扑计数记录在报告中，供诊断和后续规则设计使用。

包围盒比较使用显式配置的绝对与相对容差，逐轴比较最小值和最大值。配置名称必须明确标记为集成探针参数，而不是焊接工程标准。若坐标非有限、尺度明显不符或误差超过容差，则以 `EXPORT_MISMATCH` 失败。

`export-validation.json` 至少记录每个 Component 的：

- 文件大小和 SHA-256；
- STEP 读取/transfer 状态；
- Face 和 Solid 数量；
- OCC 包围盒；
- HyperMesh 与 OCC 包围盒逐项差值；
- 每项检查的通过状态、警告和错误分类。

## 9. `selection.json` 映射

最终文件继续使用现有 `selection.schema.json` 1.0：

- `hypermesh` 来自 manifest；
- `components[].id` 和 `name` 来自 HyperMesh；
- `components[].geometry.path` 指向对应 STEP；
- `format` 固定为 `STEP`；
- `sha256` 由 Python 计算；
- `components[].summary` 使用 HyperMesh 导出前的源几何摘要；
- `parameters` 来自显式指定的集成参数配置。

OCC 专有的读取和对比细节保存在 `export-validation.json`，不为本探针破坏已有 `selection.json` 合同。

## 10. 错误与清理

错误至少分为：

- `INVALID_SELECTION`：选择数量、实体或身份不合法；
- `EMPTY_COMPONENT_GEOMETRY`：目标 Component 没有可导出几何；
- `EXPORT_FAILED`：`*geomexport` 报错或没有产生非空文件；
- `MANIFEST_INVALID`：中间合同无效；
- `STEP_READ_FAILED`：OCC 无法读取或 transfer；
- `EMPTY_IMPORTED_SHAPE`：读取后没有有效 Shape；
- `EXPORT_MISMATCH`：单位、坐标或包围盒对比失败；
- `OUTPUT_CONFLICT`：运行目录或最终文件与已有产物冲突。

禁止把失败解释为“没有焊点”。错误必须以结构化信息呈现并保留足够上下文，但日志不得包含 STEP 文件内容。

发生 Tcl 导出失败时：

- 始终恢复原始显示状态；
- 删除本次调用已经创建的不完整 STEP；
- 不写成功 manifest 和 `selection.json`；
- 不静默调用 `*geomoutputdata`。

发生 Python 校验失败时保留 manifest、STEP 和失败校验报告用于本地诊断，但不写 `selection.json`。运行本导出探针即视为用户明确选择保留这一次诊断包；这不改变完整生产流程在拒绝、取消或成功接受后默认清理临时 CAD 的总设计。后续可提供显式清理命令；本探针不删除用户未明确归属于本次运行的文件。

## 11. 测试设计

### 11.1 Tcl 自动测试

使用 Tcl 8.5 兼容的 HyperMesh 命令桩验证：

- 只接受两个不同 Component；
- 为两个 Component 分别调用一次导出；
- 每次导出只显示对应目标；
- manifest 中的身份、路径、单位和参数正确；
- 成功后精确恢复原显示集合；
- 第一个或第二个导出失败时仍恢复显示集合并清理部分产物；
- Tcl 代码不依赖 8.6 语法。

### 11.2 Python 单元与合同测试

- manifest Schema 的有效与无效样例；
- 重复 Component、重复路径、缺失和空文件；
- SHA-256 计算；
- OCC 检查器通过接口注入测试替身，覆盖读取失败、空 Shape、非有限包围盒和 mismatch；
- `selection.json` 映射及现有 Schema 回归；
- 失败时不产生正式 selection。

### 11.3 PythonOCC 本地集成测试

在已确认的 Python 3.11.15 / OCC 7.9.0 环境中读取最小 STEP 样例，验证实际导入、拓扑遍历和包围盒路径。缺少 OCC 的普通测试环境可以明确跳过该集成测试，不能伪装成已通过。

### 11.4 HyperMesh 2017 真实集成测试

在当前车门模型中选择 Component 15 和 20，验证：

- 得到两个非空且可由 OCC 读取的独立 STEP；
- STEP 与 Component ID/名称的一一对应关系成立；
- 导出前后显示的 Component ID 集合完全一致；
- 导出前后模型中的 Surface、Solid、Element 和 Connector 数量不变；
- HyperMesh 与 OCC 包围盒在配置容差内一致；
- 最终 `selection.json` 通过 Schema 校验；
- HyperMesh 模型未自动保存或覆盖。

## 12. 非目标

本设计不包括：

- 自动扫描全部 34 个 Component；
- 自动决定哪两个零件应当焊接；
- 搭接区识别或焊点布置算法；
- 候选点预览；
- Connector 创建或 Realize；
- Agent 接入；
- 自动推断单位；
- `*geomoutputdata` 兼容实现。

## 13. 完成标准

当自动测试通过，并且真实 HyperMesh 2017 车门模型完成一次 Component 15/20 的往返验证时，STEP 导出探针完成。其交付结果是两个身份明确、可由 OCC 验证的 STEP 文件以及有效的 manifest、校验报告和 `selection.json`；原始 HyperMesh 模型和显示状态保持不变。
