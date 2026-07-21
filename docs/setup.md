# 开发环境

## 已验证环境

- Windows 10
- Python 3.11
- HyperMesh 2017
- PythonOCC 可导入 `BRepExtrema_DistShapeShape` 和 `BRepMesh_IncrementalMesh`

## 安装

在仓库根目录执行：

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m pip install -e '.[dev]'
```

相邻的 `pythonocc` 目录只是当前电脑上的运行时来源，不是本仓库的源码依赖。不要提交其绝对路径或内容。

不要求把该环境的 `Scripts` 目录加入系统 `PATH`；下面的命令都显式调用 OCC Python。

## 验证

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

也可以直接传入其他 OCC 解释器：

```powershell
$otherPython = (Resolve-Path '..\another-occ-env\python.exe').Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -PythonOccPython $otherPython
```

## Stage 0 往返测试

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m weld_agent.cli analyze `
  --selection tests\fixtures\selection.valid.json `
  --output-root run-artifacts `
  --provider fixture
```

输出中的点只用于验证接口管线，不是真实焊点识别结果。

## 终端识别显式焊点标记

本功能把 OCC 当作后台几何库，不打开 OCC GUI。先设置解释器：

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
```

准备符合 `schemas/marker-input-manifest.schema.json` 的本地 `marker-input-manifest.json`，其中列出一个或多个已导出的候选 Component STEP 绝对路径。客户 CAD、STEP、manifest 和运行结果均不得提交到 Git。

然后在仓库根目录运行：

```powershell
.\scripts\identify_weld_markers.ps1 -InputManifest 'C:\path\to\marker-input-manifest.json'
```

终端显示四个处理阶段及分类统计，结果写入 manifest 同级的 `marker-identification` 目录。若返回 `OUTPUT_CONFLICT`，创建一个新的 `run_id` 目录和 manifest 后重新运行，不覆盖已有审计结果。完整步骤见 [终端焊点标记识别](manual-tests/terminal-weld-marker-identification.md)。

## 双 Component STEP 导出

真实 HyperMesh 操作步骤见 [HyperMesh 2017 STEP 导出探针](manual-tests/hm2017-step-export-probe.md)。

HyperMesh 生成 `export-manifest.json` 后，在仓库根目录运行：

```powershell
$occPython = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
$manifestPath = Read-Host 'Paste MANIFEST path printed by HyperMesh'
& $occPython -m weld_agent.cli finalize-export `
  --manifest $manifestPath `
  --profile '.\config\integration-probe-1.json'
```

`config/integration-probe-1.json` 只用于集成验证，其中的参数不是焊接工程标准。

## 接口边界

- Python/OCC：`OCC_PYTHON -m weld_agent.cli doctor --pythonocc-python OCC_PYTHON`
- 输入合同：`schemas/selection.schema.json`
- 输出合同：`schemas/weld-candidates.schema.json`
- HyperMesh：`hypermesh/tcl/weld_agent_probe.tcl`
- HyperMesh 导出：`hypermesh/tcl/weld_agent_export.tcl`
- 中间合同：`schemas/export-manifest.schema.json`
- 导出校验合同：`schemas/export-validation.schema.json`
- OCC 最终化：`python -m weld_agent.cli finalize-export --manifest $manifestPath --profile config/integration-probe-1.json`
- 焊点标记输入：`schemas/marker-input-manifest.schema.json`
- 焊点标记输出：`schemas/weld-markers.schema.json`
- 终端识别：`scripts/identify_weld_markers.ps1 -InputManifest marker-input-manifest.json`
- 几何算法：通过 `CandidateProvider` 协议替换；当前只有 `fixture-test-only`
