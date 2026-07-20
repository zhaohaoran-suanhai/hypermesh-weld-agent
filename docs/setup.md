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

## 接口边界

- Python/OCC：`OCC_PYTHON -m weld_agent.cli doctor --pythonocc-python OCC_PYTHON`
- 输入合同：`schemas/selection.schema.json`
- 输出合同：`schemas/weld-candidates.schema.json`
- HyperMesh：`hypermesh/tcl/weld_agent_probe.tcl`
- 几何算法：通过 `CandidateProvider` 协议替换；当前只有 `fixture-test-only`
