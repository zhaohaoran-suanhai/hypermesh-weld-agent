# 知识库索引

本目录是 Codex 与人类开发者共同使用的项目知识库。当前事实、稳定接口、人工证据和历史设计分层保存，避免从聊天记录猜测项目状态。

## 建议阅读顺序

1. [README](../README.md)
2. [仓库规则](../AGENTS.md)
3. [当前状态](current-state.md)
4. [架构与数据流](architecture.md)
5. 根据任务进入 [本机集成文档](integrations/)

## 按问题查找

| 问题 | 权威入口 |
|---|---|
| 现在已经实现什么、有什么证据 | [docs/current-state.md](current-state.md) |
| HyperMesh、OCC、Python 如何协作 | [docs/integrations/](integrations/) |
| 模块、Schema、进程和文件如何连接 | [docs/architecture.md](architecture.md) |
| Component、Solid、marker、2T/3T、Connector 分别是什么 | [docs/domain-model.md](domain-model.md) |
| 如何安装、测试和提交 | [docs/development.md](development.md) |
| 如何在真实 HyperMesh 中复现实验 | [docs/manual-tests/](manual-tests/) |
| 为什么做出长期架构选择 | [docs/decisions/](decisions/) |
| 哪些工作已完成、已批准或仅是候选 | [docs/roadmap.md](roadmap.md) |
| 追溯批准设计和实施过程 | [docs/superpowers/](superpowers/) |

## 事实维护规则

- 当前状态只在 `docs/current-state.md` 维护；
- 详细真实证据留在 manual runbook，状态页只摘要并链接；
- specs/plans 是历史记录，不能覆盖当前代码与新鲜验证；
- 本机集成事实变化时同步更新 `docs/integrations/`；
- 禁止把客户模型、运行产物或私有解释器绝对路径写入知识库。
