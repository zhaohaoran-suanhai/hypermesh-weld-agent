# 当前状态

本页是仓库当前状态的唯一文档来源。最后依据 2026-07-21 的本机验证、当前 `main` 代码和测试整理。若它与代码或新鲜验证冲突，以代码与验证为准，并同步修正本页。

## 已验证能力

- HyperMesh 2017 能力探针：从 Tcl Console 获取选定 Component，并确认 `*geomexport`、旧 `*geomoutputdata` 和 Connector 创建命令的存在性；
- 隔离 STEP 导出：显式选择两个 Component，分别导出 STEP AP214/mm，同时保存并恢复原显示状态；
- 外部几何读取：Python 3.11 通过无 GUI PythonOCC 读取 STEP，统计 Face/Solid 和包围盒；
- 文件合同：HyperMesh 与 Python 通过唯一临时运行目录、STEP、JSON manifest 和 JSON Schema 交换数据；
- 显式 marker 识别：对明确列出的多个 STEP Component，将独立 Solid 分类为 `cylinder`、`triangular_prism` 或 `unknown`；
- 可审计输出：版本化 PowerShell/CLI 在当前终端显示阶段，并写出 JSON、CSV 和日志；
- 自动验证：pytest 覆盖合同、Tcl 静态行为、OCC 合成几何、工作流、CLI 和启动脚本。

这些是可复用的平台能力，不只服务焊点识别。新的 HyperMesh 几何任务可以沿相同的 Tcl → STEP/JSON → PythonOCC → 普通 Python 工作流边界扩展。

## 验证证据

当前车门样本使用 5 个明确选择的 `(SW)` Component，识别出 122 个独立 Solid marker：

| 分类 | 数量 |
|---|---:|
| `cylinder` | 83 |
| `triangular_prism` | 39 |
| `unknown` | 0 |

JSON 与 CSV 都有 122 条记录，所有记录包含 marker、Component 和 Solid 身份。完整命令、分 Component 统计和安全确认见 [终端焊点标记识别 runbook](manual-tests/terminal-weld-marker-identification.md)。

双 Component STEP 导出和 OCC 读取证据见 [HyperMesh 2017 STEP 导出探针](manual-tests/hm2017-step-export-probe.md)；命令能力见 [HyperMesh 2017 能力探针](manual-tests/hm2017-capability-probe.md)。

## 当前限制

- marker 输入仍由人或上游步骤明确选择，不自动扫描完整车门；
- `cylinder` 和 `triangular_prism` 是几何分类，不能单独证明 2T、3T 或具体焊接工艺；
- 尚未沿 marker 轴线求取相邻板件、板层数或焊接面；
- 不根据搭接关系生成新焊点；
- 没有 HyperMesh 预览/write-back 工作流；
- 不创建或 Realize Connector；
- 现有交互式 Tcl 已在 HyperMesh GUI 中验证，不能未经测试就宣称可由 `hmbatch.exe` 完整运行。

## 开放问题

下面只是可以独立设计的研究方向，不是接手仓库后的默认开发任务，也不表示已经授权：

- 通用化 Component 选择与批量隔离导出；
- marker 轴线与邻近板件求交、2T/3T 和焊接面验证；
- 非焊点场景的几何质量检查、清理或特征识别；
- HyperMesh batch 能力边界；
- 经人工复核的预览和模型 write-back；
- Agent 工具编排与权限控制。

选择任何方向前应先明确目的、输入、输出、非目标和对 HyperMesh 模型的修改权限。
