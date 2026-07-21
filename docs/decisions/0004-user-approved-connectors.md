# ADR-0004：Connector 操作必须由用户显式批准

## Status

Accepted

## Context

几何识别、candidate 建议、preview、Connector 创建和 Realize 对 HyperMesh 模型的影响不同。Agent 如果从几何结果直接创建 Connector，可能把误判写入正式模型；Realize 还会生成求解器相关实体。现有能力探针只证明 Connector 命令存在，不证明它应被执行。

## Decision

所有几何结果保持 advisory。preview、model write-back、Connector create 和 Connector Realize 使用不同的受控接口。任何正式 Connector 创建都必须由用户针对当前模型、候选范围和参数显式批准；Realize 需要再次明确授权。Agent 不得把一般的“继续开发”解释为模型写回授权。

## Consequences

- 当前 OCC 和 marker 工作流只写仓库外结果文件，不修改 `.hm`；
- 未来 write-back 设计必须支持预览、候选身份、审计和失败恢复；
- 自动化程度受人工门控限制，但降低了错误模型修改风险；
- 测试不得以调用真实 Connector 命令作为普通集成检查。
