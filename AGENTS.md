# Repository Rules

本文件同时约束 Codex 和人类开发者。仓库直接在 `main` 开发的决定来自用户明确授权；不要自行改用其他仓库或与 `fluent-automation` 耦合。

## 必读顺序

开始修改前依次阅读：

1. `README.md`；
2. `AGENTS.md`；
3. `docs/current-state.md`；
4. `docs/architecture.md`；
5. 与任务有关的 `docs/integrations/` 文档；
6. 必要时再读 `docs/domain-model.md`、`docs/manual-tests/`、`docs/decisions/`。

完整路由见 `docs/index.md`。`docs/superpowers/specs/` 和 `docs/superpowers/plans/` 是历史记录，不是当前状态源。

## 事实优先级

发生冲突时按以下顺序判断：

1. 当前代码、Schema 和刚运行的验证结果；
2. `docs/current-state.md`；
3. `docs/architecture.md`、`docs/domain-model.md` 和 ADR；
4. 当前 manual runbook；
5. 历史 specs、plans、提交说明和聊天记录。

如果稳定文档与代码不一致，不要默默选择其一：先用只读检查确认事实，再修正文档或报告冲突。

## 开发与安全边界

- Python 必须为 `>=3.11,<3.12`；OCC 对象只能存在于 `src/weld_agent/geometry/` 适配层，跨层使用普通 Python 数据；
- 新的几何实现应隐藏在明确的 Protocol/adapter 后；现有扩展点包括 `CandidateProvider`、`StepInspector` 和 `MarkerStepReader`；
- HyperMesh Tcl 使用 `::weldagent` 命名空间、显式参数、唯一临时运行目录和分类错误；改变显示或选择状态的脚本必须在成功与失败后恢复状态；
- 不得提交客户 CAD、HyperMesh 模型、STEP/IGES、临时导出、manifest、运行结果、本地许可证信息或私有解释器绝对路径；
- 不得在未经授权时保存或覆盖 `.hm`，也不得创建、Realize 或删除正式 Connector；几何建议必须保持 advisory；
- 正式验证使用仓库中的版本化脚本并在当前终端显示信息，不使用隐藏的一次性脚本作为交付证据；
- 保持本仓库独立于 `fluent-automation`。

## 文档更新矩阵

- 当前能力、真实基线、限制或开放问题变化：更新 `docs/current-state.md`；
- 模块边界、数据流或合同变化：更新 `docs/architecture.md`；
- 领域术语或几何事实/工程语义边界变化：更新 `docs/domain-model.md`；
- 本机安装、启动方式或 HyperMesh/OCC 接口变化：更新 `docs/integrations/`；
- 开发、测试或提交命令变化：更新 `docs/development.md`；
- 人工操作或验收证据变化：更新 `docs/manual-tests/`；
- 长期且难以逆转的决策变化：新增或替代 `docs/decisions/` 中的 ADR；
- 阶段状态或候选方向变化：更新 `docs/roadmap.md`。

历史 specs 和 plans 保留批准时内容；通过索引说明其历史性质，不把它们回写成当前状态。

## 完成定义

声称工作完成前必须：

1. 对照用户授权确认没有扩大写回、Connector 或客户数据范围；
2. 更新受影响的稳定文档和 runbook；
3. 设置 `WELD_AGENT_PYTHONOCC_PYTHON`；
4. 运行 `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1`；
5. 检查 `git diff --check`、`git status --short` 和待提交文件；
6. 报告真实测试输出和仍未完成的边界，不用计划代替实现证据。
