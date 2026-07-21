# HyperMesh Weld Agent

这是一个面向 HyperMesh 2017 的几何自动化开发仓库。它把 HyperMesh Tcl、外部 Python 3.11、PythonOCC 和 JSON Schema 组织成可测试、可审计、由人复核的前处理工作流。第一个完成真实验证的应用是 CAD 显式焊点标记识别，但这套接口也可用于其他 HyperMesh 几何与前处理开发。

## 从这里开始

Codex 与人类开发者使用同一阅读顺序：

1. 本页了解项目定位；
2. [AGENTS.md](AGENTS.md) 接受仓库规则；
3. [docs/current-state.md](docs/current-state.md) 确认当前实际能力；
4. [docs/architecture.md](docs/architecture.md) 理解模块和数据流；
5. 根据任务进入 [docs/integrations/](docs/integrations/) 或完整的 [docs/index.md](docs/index.md)。

不要从历史实施计划推断当前能力，也不要依赖先前聊天记录接手仓库。

## 当前能力摘要

- 在 HyperMesh 2017 Tcl Console 中运行版本化能力探针；
- 隔离选定 Component、导出 STEP AP214，并恢复原显示状态；
- 通过 JSON manifest 和 Schema 把 HyperMesh 输出交给外部 Python；
- 使用无 GUI 的 PythonOCC 读取 STEP B-Rep、统计拓扑和提取几何观察量；
- 识别显式 `cylinder`、`triangular_prism` 或 `unknown` Solid marker；
- 在终端输出进度，并生成 JSON、CSV 和日志。

当前分类只证明几何类型与空间信息，不证明 2T/3T、焊接面或 Connector 工程语义。详见 [当前状态](docs/current-state.md)。

## 本机快速验证

从仓库根目录执行：

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

本机 HyperMesh、PythonOCC 和终端协作方式见 [docs/integrations/](docs/integrations/)；完整开发命令见 [docs/development.md](docs/development.md)。

## 安全边界

- 不提交客户 CAD、`.hm`、STEP/IGES、临时 manifest、运行结果或私有解释器绝对路径；
- OCC 是后台几何内核，正式流程不要求 OCC GUI；
- 默认流程只读模型或导出临时文件；保存/覆盖 `.hm`、回写模型和创建 Connector 需要独立接口与用户显式批准；
- 几何输出是供人复核的证据，不得冒充尚未验证的工程语义。

## 文档地图

- [知识库总索引](docs/index.md)
- [当前状态](docs/current-state.md)
- [架构与数据流](docs/architecture.md)
- [领域模型](docs/domain-model.md)
- [开发指南](docs/development.md)
- [本机 HyperMesh/OCC 集成](docs/integrations/)
- [人工验收记录](docs/manual-tests/)
- [架构决策](docs/decisions/)
- [路线与候选方向](docs/roadmap.md)
- [历史设计和计划](docs/superpowers/)
