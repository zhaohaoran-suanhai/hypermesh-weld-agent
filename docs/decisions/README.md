# Architecture Decision Records

ADR 记录长期有效、会约束后续设计的选择。它不记录任务进度；当前能力仍以 [docs/current-state.md](../current-state.md) 为准。

## 规则

- 文件使用连续编号；
- 正文包含 `Status`、`Context`、`Decision`、`Consequences`；
- 已接受 ADR 不静默改写决定；需要变化时新增 ADR，并在新旧文件中说明 superseded 关系；
- 临时实验、实现步骤和测试日志放入 spec、plan 或 runbook，不放 ADR。

## 索引

| ADR | 决策 |
|---|---|
| [0001-terminal-first-independent-repository.md](0001-terminal-first-independent-repository.md) | 独立仓库与 terminal-first 工作方式 |
| [0002-pythonocc-headless-geometry-kernel.md](0002-pythonocc-headless-geometry-kernel.md) | PythonOCC 作为无 GUI 外部几何内核 |
| [0003-explicit-cad-markers-first.md](0003-explicit-cad-markers-first.md) | 第一个验证应用先识别 CAD 显式 marker |
| [0004-user-approved-connectors.md](0004-user-approved-connectors.md) | Connector write-back 必须由用户显式批准 |
