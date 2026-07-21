# 阶段状态与候选方向

本页区分已验证事实、已授权工作和普通候选方向。它不指定新对话的默认任务；实际工作由用户当前请求决定。

## 已完成并验证

- 独立仓库、Python 3.11/PythonOCC runtime 探针、Schema 合同和测试基础；
- HyperMesh 2017 Component 选择与命令能力探针；
- 双 Component 隔离 STEP AP214/mm 导出、显示状态恢复和外部 OCC 校验；
- 显式 Solid marker 的 `cylinder`/`triangular_prism`/`unknown` 分类；
- 终端进度、JSON/CSV/log 和真实车门 122/83/39 基线；
- Codex/人类共同使用的本机 HyperMesh/OCC 知识库。

证据和限制见 [当前状态](current-state.md) 与 [人工验收索引](manual-tests/README.md)。

## 已批准但尚未实施

当前没有已批准但尚未实施的功能阶段。

设计讨论、知识库整理或候选方向不自动构成功能实现授权。若用户批准新的设计，应在此明确目标、批准日期和对应 spec。

## 候选方向（未授权）

- marker 轴线与邻近板件求交、板层数和 welding face 验证；
- 更通用的 Component 选择、隔离导出和 HyperMesh 几何检查；
- `hmbatch.exe` 无交互执行接口和 license/error contract；
- 人工复核后的 HyperMesh preview/write-back；
- Connector create/Realize 的受控分级授权接口；
- Agent 工具编排、审计和权限策略；
- 焊点之外的孔、边、间隙、几何质量或清理建议。

仓库交接不表示获准选择或执行其中任何方向。每项都应先完成目的—输入—输出—非目标设计，并明确是否允许修改 HyperMesh 模型。
