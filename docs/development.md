# 开发指南

本页是仓库通用开发与验证入口。具体产品接口分别见 [本机环境](integrations/local-environment.md)、[HyperMesh 2017](integrations/hypermesh-2017.md)、[PythonOCC](integrations/pythonocc.md) 和 [HyperMesh/OCC 文件桥](integrations/hypermesh-occ-bridge.md)。

## 环境要求

- Windows；
- HyperMesh/HyperWorks 2017；
- Python `>=3.11,<3.12`；
- PythonOCC/OpenCascade 7.9.0；
- PowerShell 5.1 或兼容版本；
- Git。

PythonOCC 环境位于仓库相邻目录，不属于本仓库源码。进入仓库根目录后设置：

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
```

不要把解析后的私有绝对路径写入源码、配置或文档。

## 安装项目

在仓库根目录使用 OCC Python 做 editable install：

```powershell
& $env:WELD_AGENT_PYTHONOCC_PYTHON -m pip install -e '.[dev]'
```

检查运行时：

```powershell
& $env:WELD_AGENT_PYTHONOCC_PYTHON -m weld_agent.cli doctor `
  --pythonocc-python $env:WELD_AGENT_PYTHONOCC_PYTHON
```

预期可见 Python 3.11 和 OCC 7.9.0，且 `available` 为 `true`。

## 测试层级

快速纯 Python/合同测试：

```powershell
& $env:WELD_AGENT_PYTHONOCC_PYTHON -m pytest tests\test_contracts.py tests\test_marker_identification.py -v
```

OCC adapter 集成测试：

```powershell
& $env:WELD_AGENT_PYTHONOCC_PYTHON -m pytest tests\test_step_inspector.py tests\test_occ_marker_reader.py -v
```

完整验证：

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

`verify.ps1` 依次运行完整 pytest、PythonOCC runtime doctor、集成 profile Schema 校验和 `git diff --check`。

## 测试策略

- 合同层：用仓库内合成 JSON fixture 测试 Schema 和跨字段规则；
- 几何分类层：用普通 dataclass/tuple 测试，不导入 OCC；
- OCC adapter：在测试内生成圆柱、三棱柱、box 等合成 Shape，写入临时 STEP 后读取；
- 工作流：注入 fake reader/provider，验证排序、错误、JSON/CSV 和原子写；
- HyperMesh Tcl：自动测试脚本结构、命令、状态恢复和输出合同；
- 真实 HyperMesh：按 `docs/manual-tests/` 的 runbook 人工执行并保留仓库外证据。

不要把客户 STEP 或 `.hm` 加入自动测试。需要复现拓扑时，优先用 OCC 生成最小合成几何。

## 开发一个新功能

1. 先写目的、输入、输出、非目标和副作用授权；
2. 如果依赖 HM2017 命令，先增加只读 capability probe；
3. 为跨进程 JSON 定义 Schema 和 fixture；
4. 用 Protocol/adapter 隔离 HyperMesh、OCC 和领域逻辑；
5. 先写失败测试，再实现最小行为；
6. 为真实 HyperMesh 操作写 runbook，验证模型/显示/选择/Connector 计数是否保持；
7. 更新 `docs/current-state.md` 和受影响的稳定知识文档；
8. 完整验证后再提交。

通用桥接模板见 [HyperMesh/OCC 文件桥](integrations/hypermesh-occ-bridge.md)。

## Git 与数据检查

提交前运行：

```powershell
git status --short
git diff --check
git diff --cached --name-only
git ls-files '*.hm' '*.step' '*.stp' '*.iges' '*.igs' 'run-artifacts/*'
```

禁止提交：

- 客户 CAD、HyperMesh 模型和几何导出；
- `%TEMP%` 下的 manifest、JSON/CSV/log 和中间文件；
- 本地许可证、账号、机器配置和私有解释器绝对路径；
- 未经清理的截图或日志中的客户路径/名称；
- `run-artifacts/`。

## 完成报告

报告实际运行的命令、测试数量、runtime 版本、人工验收是否执行、结果文件是否只在仓库外，以及仍未证明的边界。没有新鲜验证时不得声称完成。
