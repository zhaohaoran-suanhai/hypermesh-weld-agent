# 仓库文档知识库设计规格

日期：2026-07-21  
状态：根据书面复核意见修订，待再次确认

## 1. 目标

为 `hypermesh-weld-agent` 建立一套由 Codex 与人类开发者共同使用的仓库内知识库，使没有聊天历史的新对话或第一次打开仓库的开发者能够：

- 区分项目长期方向、当前实际能力和尚未实现的设想；
- 找到当前架构、领域术语、运行方式、验证证据和通用扩展方法；
- 在当前电脑上配置并调用 HyperMesh 2017、HyperMesh Tcl、外部 Python 3.11 和 PythonOCC；
- 理解 HyperMesh 与 OCC 之间的文件接口和进程边界，并把它复用于焊点识别以外的前处理开发；
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
│  └─ 唯一当前状态源：已实现、证据、限制和开放问题
├─ architecture.md
│  └─ 当前实际架构、模块职责、数据流和接口边界
├─ domain-model.md
│  └─ 领域术语、几何类型与工程语义的区别
├─ development.md
│  └─ 开发环境、命令、测试、数据安全和提交前检查
├─ integrations/
│  ├─ local-environment.md
│  │  └─ 本机已验证安装、环境变量、版本探针和启动方式
│  ├─ hypermesh-2017.md
│  │  └─ GUI Console、Tcl、batch 入口、命令能力和状态保护规则
│  ├─ pythonocc.md
│  │  └─ 外部 Python/OCC 环境、可复用几何接口和无 GUI 约束
│  └─ hypermesh-occ-bridge.md
│     └─ STEP + JSON 文件桥、Schema、运行目录、错误和扩展模式
├─ roadmap.md
│  └─ 阶段状态和准入条件；不是接手开发的必读前置
├─ decisions/
│  └─ 长期有效的 Architecture Decision Records
├─ manual-tests/
│  └─ 可重复的人工验收步骤和真实证据
└─ superpowers/
   ├─ specs/  历史批准设计
   └─ plans/  历史实施计划
```

`docs/setup.md` 保留为兼容入口，但不再独立维护一套环境事实；它应引导到 `docs/development.md` 和 `docs/integrations/local-environment.md`。

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
5. 若任务涉及 HyperMesh 或 OCC，先读 `docs/integrations/` 下的对应接口文档；
6. 根据任务进入专题文档：
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
- 沿 marker 轴线与邻近板件求交只是候选研究方向之一；它尚未实现，也不是接手仓库后的默认开发任务；
- OCC 是无 GUI 的后台几何内核，正式验证必须通过仓库中的版本化脚本在终端运行；
- 任何正式 Connector 创建必须由用户显式批准，Agent 不得自主执行。

知识库不得把“下一项焊点研究”塑造成仓库唯一开发目的。`current-state.md` 应重点描述可复用的平台能力和已验证边界；未来方向放在 `roadmap.md`，并清楚区分已批准工作与普通候选方向。

## 7. 本机开发环境与通用协作接口

知识库必须记录以下已经在当前电脑上验证的事实，同时避免提交用户私有解释器绝对路径：

- 操作系统：Windows；
- HyperWorks 2017 安装根目录：`C:\Program Files\Altair\2017`；
- HyperMesh GUI：`C:\Program Files\Altair\2017\hm\bin\win64\hmopengl.exe`；
- HyperMesh batch：`C:\Program Files\Altair\2017\hm\bin\win64\hmbatch.exe`；
- HyperWorks 入口：`C:\Program Files\Altair\2017\hw\bin\win64\hw.exe`；
- PythonOCC 环境相对本仓库位于 `..\pythonocc\.m\envs\occ\python.exe`；
- 已验证 Python 版本为 3.11.15，OCC 版本为 7.9.0；
- 正式脚本通过 `WELD_AGENT_PYTHONOCC_PYTHON` 获取解释器，不在源码或配置中保存用户目录绝对路径。

`docs/integrations/hypermesh-2017.md` 必须说明：

- 如何打开 HyperMesh Tcl Console、`source` 仓库脚本并调用命名空间 proc；
- 交互式 GUI、录制/诊断命令和 `hmbatch.exe` 的适用边界；
- 当前已验证的 Tcl 能力：mark/selection、`hm_getvalue`、`hm_getboundingbox`、`*geomexport`、旧 `*geomoutputdata` 和 Connector 创建命令存在性；
- 新脚本使用 `::weldagent` 命名空间、显式参数和分类错误；
- 在任何导出或显示切换前记录状态，并在成功或失败后恢复；
- 未经用户授权不得保存或覆盖 `.hm`，不得创建正式 Connector。

`docs/integrations/pythonocc.md` 必须说明：

- 如何设置解释器、安装 editable package、运行 `doctor`、pytest 和 `verify.ps1`；
- OCC 只在 `src/weld_agent/geometry/` 适配层出现，工作流和合同层使用普通 Python 类型；
- 当前可复用接口包括 `StepInspector`、`MarkerStepReader`、`CandidateProvider` 及其实现边界；
- 如何用仓库测试生成合成 OCC Shape/STEP，而不依赖客户模型；
- 正式流程不导入 `OCC.Display`，不要求 OCC GUI。

`docs/integrations/hypermesh-occ-bridge.md` 必须把通用桥接合同写清楚：

```text
HyperMesh 2017 当前模型
  -> 版本化 Tcl：选择/读取摘要/隔离/STEP 导出/恢复状态
  -> 唯一临时运行目录：STEP + JSON manifest
  -> 外部 Python 3.11：Schema 校验
  -> PythonOCC：读取 B-Rep、计算几何观察量
  -> 普通 Python 工作流：领域处理
  -> JSON/CSV/log
  -> 人工复核；只有显式授权才能回写 HyperMesh
```

这份桥接文档同时提供“新增一个非焊点 HyperMesh 功能”的扩展清单：先做 Tcl 能力探针，再定义 JSON Schema，随后实现无 OCC 类型泄漏的 Python adapter/workflow，最后补合成几何测试、HyperMesh 人工 runbook 和状态恢复验证。

## 8. ADR 范围

本次建立少量、稳定的 ADR，至少覆盖：

1. 仓库独立于 `fluent-automation`，采用 terminal-first 工作方式；
2. OCC 作为不打开 GUI 的后台几何内核；
3. 第一阶段优先识别 CAD 中已有的显式 marker，不根据搭接关系生成新焊点；
4. Connector 创建必须经过用户显式批准。

ADR 使用连续编号，包含 Context、Decision、Consequences 和 Status。ADR 只记录长期决策，不记录临时任务进度。

## 9. 防过期机制

`AGENTS.md` 增加以下更新矩阵：

- 当前能力、真实基线、限制或开放问题变化：更新 `docs/current-state.md`；
- 模块边界、数据流或接口变化：更新 `docs/architecture.md`；
- 领域术语或“几何事实/工程语义”边界变化：更新 `docs/domain-model.md`；
- 长期有效、难以逆转的选择变化：新增或替代 ADR；
- 人工操作或验收方式变化：更新 `docs/manual-tests/`；
- 本机安装、启动命令或 HyperMesh/OCC 接口变化：更新 `docs/integrations/`；
- 阶段状态或准入条件变化：更新 `docs/roadmap.md`。

specs 和 plans 保存批准时的历史内容，不回写成当前状态。若历史文档容易被误读，应通过目录 README、索引或统一页首说明标明其历史性质，而不是修改原始技术结论。

## 10. 自动化验证

新增轻量文档测试并纳入现有 pytest/`scripts/verify.ps1`，至少验证：

- `README.md`、`AGENTS.md` 和 `docs/index.md` 包含统一接手入口；
- `docs/current-state.md` 包含已实现、证据、限制和开放问题章节；
- Connector 显式批准、客户数据禁入和 OCC 无 GUI 等关键安全语句存在；
- 仓库内 Markdown 相对链接指向已存在文件；
- 知识库索引覆盖核心稳定文档和 ADR；
- 文档不得写入本机 PythonOCC 解释器的绝对路径；
- 本机集成文档覆盖 HyperMesh GUI/batch/Tcl、PythonOCC 版本探针和 STEP + JSON 桥接接口；

测试只验证结构和关键不变量，不对普通段落措辞做脆弱的全文匹配。

## 11. 本次实施范围

本次修改：

- 重写 `README.md`；
- 扩充 `AGENTS.md`；
- 新增 `docs/index.md`、`docs/current-state.md`、`docs/architecture.md`、`docs/domain-model.md`、`docs/development.md`、`docs/roadmap.md`；
- 新增 `docs/integrations/local-environment.md`、`docs/integrations/hypermesh-2017.md`、`docs/integrations/pythonocc.md`、`docs/integrations/hypermesh-occ-bridge.md`；
- 新增 `docs/decisions/` 下的 ADR；
- 将 `docs/setup.md` 调整为兼容入口；
- 为 manual tests、specs 和 plans 建立清晰索引或分类说明；
- 新增文档结构、链接和安全边界测试。

本次不修改几何算法、Python 工作流、HyperMesh Tcl、CLI、Schema、客户数据或真实运行结果。

## 12. 验收标准

一个没有聊天历史的新 Codex 对话或人类开发者，只读取统一入口和其链接的稳定文档，就能正确回答：

1. 项目长期方向与当前阶段成果分别是什么；
2. 当前能识别什么，哪些工程语义尚未证明；
3. 从 HyperMesh/STEP 到 OCC 分类再到 JSON/CSV 的实际数据流；
4. 如何配置环境、运行识别和完成验证；
5. 哪些本地数据禁止提交；
6. 如何在本机启动 HyperMesh GUI/batch、调用版本化 Tcl、配置外部 PythonOCC 并运行探针；
7. HyperMesh 与 OCC 为什么通过 STEP + JSON 临时运行目录协作，以及如何为其他前处理功能复用该模式；
8. 哪些方向只是候选工作而非当前开发目的；
9. 为什么任何 Connector 创建都必须停下来获得用户批准。

完整 `scripts/verify.ps1` 必须通过，且 Git 中不得出现客户数据、临时运行结果或本机私有路径。
