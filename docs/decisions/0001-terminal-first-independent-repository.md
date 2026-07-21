# ADR-0001：独立仓库与 terminal-first

## Status

Accepted

## Context

HyperMesh 自动化涉及旧版 Tcl、外部几何内核、客户模型和人工桌面操作。如果与其他 CAE 自动化仓库耦合，依赖、权限和运行证据容易混杂。早期 OCC 验证若依赖隐藏 inline Python 或额外 GUI，也使用户无法看到实际调用和错误。

## Decision

`hypermesh-weld-agent` 保持独立，不依赖或导入 `fluent-automation`。正式流程使用仓库内版本化脚本，从当前终端启动外部 Python/OCC，并把阶段、错误和产物路径直接显示出来。探索命令确认有效后应进入仓库，不把聊天里的临时代码当成正式接口。

## Consequences

- HyperMesh 相关依赖、合同和安全规则可以独立演进；
- 用户能在同一终端观察 OCC 执行，无需学习 OCC GUI；
- 公共逻辑不能通过跨仓库隐式引用复用，需要在本仓库定义明确接口；
- 仓库必须维护启动脚本、环境说明和可重复验证。
