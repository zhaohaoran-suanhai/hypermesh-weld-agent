# HyperMesh Weld Agent 设计规格

日期：2026-07-20  
状态：已完成会话评审，等待书面规格复核  
目标仓库：`git@github.com:zhaohaoran-suanhai/hypermesh-weld-agent.git`

## 1. 背景与结论

本项目以汽车车门点焊前处理为切入点，验证“Agent + 几何算法 + HyperMesh 脚本”能否形成可落地的 CAE 前处理闭环。

路线判断如下：

- 几何算法负责确定性的几何分析和候选焊点生成；
- Agent 负责理解任务、调用受控工具、解释异常和组织人机协作；
- HyperMesh 2017 Tcl 负责选择实体、导出几何、显示预览和创建 Connector；
- 用户负责批准候选点，Agent 不获得创建正式 Connector 的自主权限；
- 项目与 `C:\Users\25335\Documents\GitHub\fluent-automation` 完全解耦。

首要实现目标为 MVP-A：用户在 HyperMesh 中明确选择两个钣金 Component，系统分析两者之间的潜在搭接区域，生成候选焊点并在 HyperMesh 中预览；只有用户确认后，系统才创建未 Realize 的 Spot Connector。

## 2. 设计原则

1. **候选而非断言**：几何接近只能证明存在潜在搭接条件，不能证明真实制造工艺一定为点焊。
2. **确定性内核**：坐标、距离、区域和布点由可测试的几何模块计算，不由 LLM 猜测。
3. **显式人工门**：接受候选点必须由用户在 HyperMesh 中明确操作。
4. **非破坏性预览**：分析和预览不得修改原始 Component 的几何、网格或正式连接关系。
5. **接口优先**：先冻结输入输出合同，具体几何算法另行设计和验证。
6. **可替换适配器**：几何模块、Agent 层和 HyperMesh 适配器通过结构化数据通信。
7. **可追溯**：每次运行保存输入、参数、版本、结果、错误和人工决策。

## 3. 总体架构

采用“HyperMesh 选择与导出 + 外部几何服务 + HyperMesh 回写”的混合架构：

```text
HyperMesh 中选择两个 Components
    -> Tcl 验证选择并导出临时 CAD
    -> selection.json + 临时 CAD
    -> Python/OCC 几何模块
    -> weld_candidates.json
    -> Tcl 创建隔离的候选预览点
    -> 用户接受、拒绝或重新计算
    -> 接受后创建未 Realize Spot Connector
```

HyperMesh 14.0.120 提供 `*geomexport`。适配器应检测实际 HyperMesh build，并在不具备该命令时使用经过验证的兼容导出通道。版本差异只能存在于 HyperMesh 适配器内，不得泄漏到几何领域模型。

首选临时 CAD 交换格式为 STEP；旧 build 的兼容格式可以是 IGES。交换格式及文件路径由 `selection.json` 明确声明，几何模块不能依赖文件扩展名猜测格式。

## 4. 仓库与模块边界

独立仓库路径：

```text
C:\Users\25335\Documents\GitHub\hypermesh-weld-agent
```

规划结构：

```text
hypermesh-weld-agent/
├─ src/weld_agent/
│  ├─ domain/             # Component、候选区域、候选焊点等领域模型
│  ├─ geometry/           # 可替换的几何分析提供器
│  ├─ workflow/           # 确定性任务编排和状态管理
│  ├─ agent/              # Agent 工具和权限边界
│  └─ adapters/
│     └─ hypermesh/       # HyperMesh 数据与进程适配
├─ hypermesh/
│  └─ tcl/                # HM2017 选择、导出、预览和 Connector 脚本
├─ schemas/               # 交换文件的 JSON Schema
├─ tests/                 # 单元、合同、样例和集成测试
├─ examples/              # 可公开的最小测试几何
└─ docs/
```

模块职责：

- `domain` 不依赖 OCC、HyperMesh 或 Agent 框架；
- `geometry` 只接收标准输入并返回候选结果，不直接控制 HyperMesh；
- `workflow` 管理运行状态、输入输出校验、调用顺序和失败传播；
- `agent` 只能调用受控工作流工具，不能拼接并执行任意 Tcl；
- `adapters/hypermesh` 和 `hypermesh/tcl` 负责所有 HyperMesh 版本差异；
- `schemas` 是 Python、Tcl 和后续 Agent 工具之间的稳定合同。

## 5. PythonOCC 运行时

本机已经存在可用环境：

```text
C:\Users\25335\Documents\GitHub\pythonocc\.m\envs\occ\python.exe
```

已验证：

- Python 3.11.15；
- `OCC.VERSION` 报告 7.9.0；
- MVP 所需的基础 OCC 模块可以导入。

新仓库通过本地忽略的配置指向该解释器，不复制 `pythonocc` 工作区，也不把绝对路径写入受版本控制的公共配置。新仓库仍独立声明自己的依赖和运行时能力要求，以便在其他机器重建环境。

## 5.1 运行工作区与数据边界

每次分析使用仓库外的唯一临时目录：

```text
%TEMP%\hypermesh-weld-agent\<run_id>\
```

该目录保存本次运行的 `selection.json`、临时 CAD、`weld_candidates.json`、人工决策和日志。临时 CAD 与模型几何不得进入 Git，不得由 Agent 或日志组件上传到网络。拒绝、取消或成功接受后，默认清理临时 CAD；只有用户明确选择保留诊断包时才保留完整运行目录。

## 6. 几何算法合同

### 6.1 目的

给定用户在 HyperMesh 中明确选择的两个 Component，分析它们之间是否存在可能布置点焊的搭接区域，并生成供工程师检查的候选焊点。

算法回答的问题是：

> 这两个零件在什么位置可能具备布置点焊的几何条件？

算法不直接断言候选位置一定是真实制造焊点。

### 6.2 输入

必需输入：

- 两个 Component 的导出几何；
- 两个 Component 的 ID 和名称；
- 模型坐标系和单位；
- 唯一运行编号；
- 当前模型、选择和导出几何的来源信息。

来源信息至少包括 HyperMesh build、Component ID 和名称、几何实体数量、轴对齐包围盒、导出文件摘要以及交换格式。它用于阻止错模型、错运行和明显过期结果，不能被描述为对任意内部几何修改的绝对检测。

工程参数：

- 几何搜索范围；
- 允许的装配间隙；
- 焊点间距；
- 首尾偏置；
- 边缘、孔等区域的避让要求；
- 使用的规则配置版本。

参数必须显式记录。Agent 可以解释或建议参数，但不能把未确认的推测当作工程标准。

### 6.3 输出

几何模块输出统一的 `weld_candidates.json`，至少包含：

- 是否发现候选搭接区域；
- 候选区域列表；
- 每个区域中的候选焊点；
- 焊点三维坐标；
- 建议连接的两个 Component；
- 建议投影或连接方向；
- 支持结果的几何证据；
- 置信度或风险标记；
- 警告和无法处理的原因；
- 输入参数、算法版本、运行编号和耗时等追溯信息。

所有候选点初始状态均为 `pending_review`。几何模块不创建 Connector，也不修改 HyperMesh 正式模型。

### 6.4 失败合同

失败也必须产生结构化结果。初始错误分类包括：

- `NO_PROXIMITY`
- `NO_VALID_OVERLAP`
- `INVALID_GEOMETRY`
- `UNSUPPORTED_GEOMETRY`
- `AMBIGUOUS_RESULT`
- `EXPORT_MISMATCH`

禁止静默失败，禁止用缺失或无效结果文件冒充“没有候选焊点”。

### 6.5 非目标

MVP 不负责：

- 扫描车门全部 Component 并自动推断零件关系；
- 判断点焊、胶接、铆接或包边的真实工艺意图；
- 处理三层及更多钣金件；
- 优化焊点数量或结构性能；
- 自动 Realize；
- 未经用户确认修改正式模型。

### 6.6 算法可替换性

具体采用 OCC 精确 B-Rep、离散网格、规则模型或学习方法，由后续算法设计和实验决定。只要满足本节合同，HyperMesh 和 Agent 层不应随算法实现变化而重写。

## 7. HyperMesh 用户流程

### 7.1 启动分析

1. 用户在 Model Browser 或图形区选择两个 Components；
2. 用户运行 `Weld Agent -> Analyze Selected Components`；
3. Tcl 验证选择数量、实体有效性、单位和运行环境；
4. Tcl 导出临时几何并写入 `selection.json`；
5. 工作流调用外部几何模块；
6. 结果通过 Schema 校验后回到 HyperMesh。

### 7.2 预览

候选点写入唯一的临时 Component，例如：

```text
__WA_PREVIEW__20260720_183500
```

每个预览实体必须与候选 ID 建立映射。预览实体不是 Connector，不参与求解器连接定义。预览允许以下操作：

- `Accept Selected`
- `Accept All`
- `Reject/Clear`
- `Recompute`

### 7.3 接受候选点

接受前必须重新验证：

- 原始两个 Component 仍然存在；
- Component ID、名称、单位和几何摘要与分析时一致；
- 候选文件属于当前运行且通过 Schema 校验；
- 坐标和方向为有限值，并处于合理模型范围内。

验证通过后，Tcl 只为已接受的候选点创建 Spot Connector，将两个原始 Component 设置为 Links，并保持 Connector 未 Realize。新建 Connector ID 必须记录到运行报告中。

## 8. 模型保护与回滚

- 不删除、移动或修改原始几何和网格；
- 不自动保存或覆盖当前 `.hm` 文件；
- 不自动 Realize；
- 每次运行使用唯一 ID；
- 重新计算、拒绝或取消时只清理本次运行创建的预览实体；
- 模型在导出后发生相关变化时，旧候选结果失效；
- Connector 创建失败时，只回滚本批次已创建的 Connector；
- 输入或输出校验失败时，不创建任何正式实体；
- 所有清理操作必须基于本次运行记录的显式实体 ID，不能使用宽泛名称匹配或全局删除。

预览会向 HyperMesh 数据库增加隔离、可逆的临时实体，但不会修改正式连接关系。用户未接受前，这些实体必须可以完整清理。

## 9. Agent 权限边界

Agent 可以：

- 检查选择；
- 启动分析；
- 解释结果和错误；
- 建议或调整非破坏性参数；
- 清理预览；
- 重新计算。

Agent 不能自行：

- 接受候选点；
- 创建正式 Connector；
- Realize；
- 保存或覆盖模型；
- 执行未注册的任意 Tcl。

接受动作必须由用户在 HyperMesh 中明确触发。Agent 工具权限应从接口层保证，而不是仅依赖提示词约束。

## 10. 分阶段交付

### 阶段 0：独立仓库与运行环境

- 初始化独立 Git 仓库并配置远程；
- 建立 Python 包、Tcl 适配器、Schema、测试和文档结构；
- 独立声明依赖；
- 通过本地配置发现现有 PythonOCC 环境；
- 验证 Python、OCC 和 HyperMesh 版本能力；
- 建立统一的运行目录和日志约定。

### 阶段 1：HyperMesh 往返闭环

使用受控的测试候选提供器验证完整集成链路：

```text
选择两个 Components
-> 导出选择和几何
-> 外部程序读取
-> 返回符合 Schema 的测试候选点
-> HyperMesh 显示预览
-> 用户接受或拒绝
-> 接受后创建未 Realize Connector
```

阶段 1 只证明基础设施闭环成立，不宣称测试候选点由真实几何算法正确识别。

### 阶段 2：真实几何算法

通过独立的算法设计、样例标注和实验选型，将测试候选提供器替换为真实实现。输入输出合同保持不变。

### 阶段 3：Agent 接入

把已验证工作流注册为受控 Agent 工具，增加自然语言参数解释、错误诊断和重算编排。人工接受权限保持不变。

## 11. 测试策略

### 11.1 Python 自动化测试

- 输入输出 Schema；
- 工作流状态转换；
- 单位和坐标校验；
- 错误分类和异常传播；
- 相同输入与参数的可重复性；
- 几何提供器的可替换性；
- 旧运行、错模型和损坏结果文件的拒绝逻辑。

### 11.2 HyperMesh 集成测试

- 选择数量不是两个时拒绝启动；
- 正确记录 Component ID 和名称；
- 导出前后包围盒、单位和坐标一致；
- 预览点只进入本次临时 Component；
- Reject 后不残留本次预览实体；
- Accept 只创建本批次 Connector；
- Connector Links 恰好指向原始两个 Components；
- Connector 保持未 Realize；
- 失败时原始几何和网格实体数量不变；
- 模型变化后拒绝应用旧结果。

### 11.3 阶段 1 验收条件

- 选择两个 Components 后可以启动完整往返流程；
- Python 与 Tcl 通过规定的 JSON 合同通信；
- 候选点可以在正确坐标预览；
- 用户可以接受、拒绝、清理和重新计算；
- 接受后 Connector Links 正确且未 Realize；
- 任一步失败都产生明确错误且不污染原始模型；
- 系统不自动保存、覆盖或 Realize 模型；
- 仓库不依赖 `fluent-automation` 的代码、环境或运行时。

## 12. 推迟到阶段 2 的算法指标

在具体算法确定前，本规格不预设搭接区域准确率、焊点位置误差、召回率、性能目标或完整曲面支持范围。这些指标必须基于标注样例、真实车门 Component 对和工程师审核结果另行确定，不能由当前设计凭空给出。

## 13. 主要风险及隔离方式

- **HyperMesh build 差异**：由版本探测和适配器封装隔离；
- **CAD 导出身份丢失**：通过运行清单、Component 元数据和几何摘要校验；
- **单位或坐标错误**：通过导出前后包围盒、单位和有限值检查阻断；
- **几何算法不成熟**：通过稳定合同和可替换提供器隔离；
- **Agent 越权**：通过工具能力拆分和人工接受接口隔离；
- **临时实体污染模型**：通过唯一运行 ID、显式实体清单和定向回滚隔离；
- **兄弟仓库耦合**：通过独立依赖声明、独立 Git 历史和本地运行时配置隔离。

## 14. 设计完成标准

本规格确定了 MVP-A 的目标、架构、模块边界、几何算法合同、HyperMesh 人机流程、安全边界、分阶段交付和阶段 1 验收方式。具体几何算法和阶段 2 精度指标被明确排除在本规格之外，并作为后续独立设计议题处理。
