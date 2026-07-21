# 仓库文档知识库设计规格

日期：2026-07-21  
状态：已批准，待书面复核

## 1. 目标

为 `hypermesh-weld-agent` 建立一套由 Codex 与人类开发者共同使用的仓库内知识库，使没有聊天历史的新对话或第一次打开仓库的开发者能够：

- 区分项目长期方向、当前实际能力和尚未实现的设想；
- 找到当前架构、领域术语、运行方式、验证证据和下一阶段入口；
- 遵守客户数据、HyperMesh 修改和 Connector 授权边界；
- 在后续开发完成时同步维护知识库，避免文档随代码演进而失效。

知识库以中文叙述为主，文件名、代码符号、命令、Schema 字段、错误码和产品名称保留英文。

## 2. 设计原则

1. **统一入口**：Codex 与人类使用相同的阅读路径，不为 Agent 另建一套隐藏知识。
2. **单一事实来源**：每类事实只有一个权威文档，其他位置只摘要并链接。
3. **当前与历史分离**：当前能力以代码、测试和 `docs/current-state.md` 为准；specs、plans 和 Git 历史用于追溯过程。
4. **逐层深入**：入口文档简短，稳定专题文档说明架构和规则，runbook 保存详细操作与证据。
5. **可验证**：关键入口、链接、章节和安全语句进入自动化文档测试。
6. **不包含客户数据**：知识库不得收录客户 STEP、`.hm`、临时 manifest、运行结果或本机私有绝对路径。

## 3. 信息架构

```text
README.md
└─ 项目简介、当前摘要和统一入口

AGENTS.md
└─ 强制规则、必读顺序、事实优先级、完成定义和更新矩阵

docs/
├─ index.md
│  └─ 知识库地图和按问题类型的路由
├─ current-state.md
│  └─ 唯一当前状态源：已实现、证据、限制和下一步
├─ architecture.md
│  └─ 当前实际架构、模块职责、数据流和接口边界
├─ domain-model.md
│  └─ 领域术语、几何类型与工程语义的区别
├─ development.md
│  └─ 开发环境、命令、测试、数据安全和提交前检查
├─ roadmap.md
│  └─ 已完成阶段、拟议阶段和阶段准入条件
├─ decisions/
│  └─ 长期有效的 Architecture Decision Records
├─ manual-tests/
│  └─ 可重复的人工验收步骤和真实证据
└─ superpowers/
   ├─ specs/  历史批准设计
   └─ plans/  历史实施计划
```

`docs/setup.md` 保留为兼容入口，但不再独立维护一套环境事实；它应引导到 `docs/development.md`。

## 4. 文档职责与事实优先级

当不同来源出现冲突时，按以下顺序判断：

1. 当前代码、Schema 和新鲜验证结果；
2. `docs/current-state.md`；
3. `docs/architecture.md`、`docs/domain-model.md` 和 ADR；
4. 当前 runbook；
5. 历史 specs、plans 和 Git 提交说明。

`README.md` 只提供摘要和导航，不承载完整架构或实验记录。`current-state.md` 只摘要真实基线并链接到对应 runbook，不在多个文件复制完整统计。`roadmap.md` 必须把“已实现”“已批准待实现”“仅拟议”分开，不把计划写成现状。

## 5. 统一接手流程

新 Codex 对话和人类开发者按以下顺序阅读：

1. `README.md`：了解项目目标和起点；
2. `AGENTS.md`：接受不可违反的开发规则；
3. `docs/current-state.md`：确认当前能力和限制；
4. `docs/architecture.md`：定位模块和合同；
5. 根据任务进入专题文档：
   - 运行或复现实验：`docs/manual-tests/`；
   - 理解术语：`docs/domain-model.md`；
   - 规划阶段：`docs/roadmap.md`；
   - 理解决策：`docs/decisions/`；
   - 追溯历史：`docs/superpowers/specs/` 和 `docs/superpowers/plans/`。

`AGENTS.md` 必须明确上述顺序，使新对话不依赖聊天记录即可接手。

## 6. 当前知识内容

整理后的知识库必须准确表达以下事实：

- 项目长期方向是 Agent、几何算法与 HyperMesh 2017 脚本协作的、由人复核的焊点工作流；
- 当前已经走通 HyperMesh 能力探针、隔离 Component STEP 导出、PythonOCC STEP 读取和显式 marker 识别；
- 当前真实车门基线为 5 个明确选择的 `(SW)` Component、122 个独立 Solid marker，其中 83 个 `cylinder`、39 个 `triangular_prism`、0 个 `unknown`；完整证据位于对应 runbook；
- 当前分类证明的是几何类型和空间信息，不能单独证明 `cylinder = 2T` 或 `triangular_prism = 3T`；
- 当前不扫描全部车门 Component，不生成新焊点，不识别焊接面，不创建 Connector；
- 下一项合理研究是沿 marker 轴线与邻近板件求交，验证板层数和焊接面，但该工作仍需独立设计和批准；
- OCC 是无 GUI 的后台几何内核，正式验证必须通过仓库中的版本化脚本在终端运行；
- 任何正式 Connector 创建必须由用户显式批准，Agent 不得自主执行。

## 7. ADR 范围

本次建立少量、稳定的 ADR，至少覆盖：

1. 仓库独立于 `fluent-automation`，采用 terminal-first 工作方式；
2. OCC 作为不打开 GUI 的后台几何内核；
3. 第一阶段优先识别 CAD 中已有的显式 marker，不根据搭接关系生成新焊点；
4. Connector 创建必须经过用户显式批准。

ADR 使用连续编号，包含 Context、Decision、Consequences 和 Status。ADR 只记录长期决策，不记录临时任务进度。

## 8. 防过期机制

`AGENTS.md` 增加以下更新矩阵：

- 当前能力、真实基线、限制或下一步变化：更新 `docs/current-state.md`；
- 模块边界、数据流或接口变化：更新 `docs/architecture.md`；
- 领域术语或“几何事实/工程语义”边界变化：更新 `docs/domain-model.md`；
- 长期有效、难以逆转的选择变化：新增或替代 ADR；
- 人工操作或验收方式变化：更新 `docs/manual-tests/`；
- 阶段状态或准入条件变化：更新 `docs/roadmap.md`。

specs 和 plans 保存批准时的历史内容，不回写成当前状态。若历史文档容易被误读，应通过目录 README、索引或统一页首说明标明其历史性质，而不是修改原始技术结论。

## 9. 自动化验证

新增轻量文档测试并纳入现有 pytest/`scripts/verify.ps1`，至少验证：

- `README.md`、`AGENTS.md` 和 `docs/index.md` 包含统一接手入口；
- `docs/current-state.md` 包含已实现、证据、限制和下一步章节；
- Connector 显式批准、客户数据禁入和 OCC 无 GUI 等关键安全语句存在；
- 仓库内 Markdown 相对链接指向已存在文件；
- 知识库索引覆盖核心稳定文档和 ADR；
- 文档不得写入本机 PythonOCC 解释器的绝对路径。

测试只验证结构和关键不变量，不对普通段落措辞做脆弱的全文匹配。

## 10. 本次实施范围

本次修改：

- 重写 `README.md`；
- 扩充 `AGENTS.md`；
- 新增 `docs/index.md`、`docs/current-state.md`、`docs/architecture.md`、`docs/domain-model.md`、`docs/development.md`、`docs/roadmap.md`；
- 新增 `docs/decisions/` 下的 ADR；
- 将 `docs/setup.md` 调整为兼容入口；
- 为 manual tests、specs 和 plans 建立清晰索引或分类说明；
- 新增文档结构、链接和安全边界测试。

本次不修改几何算法、Python 工作流、HyperMesh Tcl、CLI、Schema、客户数据或真实运行结果。

## 11. 验收标准

一个没有聊天历史的新 Codex 对话或人类开发者，只读取统一入口和其链接的稳定文档，就能正确回答：

1. 项目长期方向与当前阶段成果分别是什么；
2. 当前能识别什么，哪些工程语义尚未证明；
3. 从 HyperMesh/STEP 到 OCC 分类再到 JSON/CSV 的实际数据流；
4. 如何配置环境、运行识别和完成验证；
5. 哪些本地数据禁止提交；
6. 下一研究阶段是什么，以及它尚未获得实现授权；
7. 为什么任何 Connector 创建都必须停下来获得用户批准。

完整 `scripts/verify.ps1` 必须通过，且 Git 中不得出现客户数据、临时运行结果或本机私有路径。
