# PythonOCC 接口

PythonOCC 是本仓库的外部、无 GUI B-Rep 几何内核。HyperMesh 2017 负责模型交互和导出；PythonOCC 在独立 Python 3.11 进程读取 STEP，不能访问 HyperMesh 会话对象。

## 配置和探针

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
& $env:WELD_AGENT_PYTHONOCC_PYTHON -m pip install -e '.[dev]'
& $env:WELD_AGENT_PYTHONOCC_PYTHON -m weld_agent.cli doctor `
  --pythonocc-python $env:WELD_AGENT_PYTHONOCC_PYTHON
```

当前已验证 Python 3.11.15 / OCC 7.9.0。不要把环境变量展开后的私有路径写进仓库。

## 无 GUI 原则

正式 adapter 只导入 `OCC.Core`。不导入 `OCC.Display`，不启动 Qt，不要求打开 OCC GUI。原因是：

- 终端日志和 JSON/CSV 比隐藏窗口更可审计；
- CI/pytest 和 batch 环境不依赖桌面会话；
- OCC 只承担几何内核职责；
- 可视化若将来需要，应作为独立、可选调试工具设计。

## 当前可复用接口

| Protocol/实现 | 输入 | 普通 Python 输出 | 用途 |
|---|---|---|---|
| `StepInspector` / `PythonOccStepInspector` | STEP `Path` | `StepInspection` | Face/Solid 数、包围盒和基本可读性 |
| `MarkerStepReader` / `PythonOccMarkerReader` | STEP `Path` | `tuple[SolidObservation, ...]` | Solid 中心、bbox、volume、Face 类型/边数/轴向 |
| `CandidateProvider` / fixture provider | selection mapping | candidate mapping | 候选算法扩展边界；fixture 仅验证管线 |

`StepInspector` 和 `MarkerStepReader` 的实现位于 `src/weld_agent/geometry/`。OCC Shape、Face、Adaptor 等对象不得穿过 adapter；工作流层只依赖 dataclass、tuple、dict 和数值。

如果新任务需要曲率、距离、投影、求交或拓扑邻接，应新增聚焦的 Protocol/adapter，而不是把 OCC import 扩散到 CLI、Schema 或 HyperMesh 层。

## STEP 读取流程

1. 检查路径存在且文件非空；
2. `STEPControl_Reader.ReadFile`；
3. `TransferRoots` 并获得完整 Shape；
4. 遍历所需拓扑类型；
5. 用 GProp/Bnd/adaptor 提取普通数值；
6. 验证有限值、非反转 bbox 和非零轴向；
7. 返回普通 observation；
8. 领域层做分类或业务判断。

稳定错误包括 `STEP_READ_FAILED`、`EMPTY_IMPORTED_SHAPE` 和上层的 `INVALID_GEOMETRY`。文件损坏导致整次读取失败；有限但不支持的单个几何可以成为 `unknown`，并保留证据。

## 合成几何测试

OCC adapter 的 pytest 不依赖客户模型。测试内可以：

- `BRepPrimAPI_MakeCylinder` 生成圆柱；
- `BRepBuilderAPI_MakePolygon` + `BRepBuilderAPI_MakeFace` + `BRepPrimAPI_MakePrism` 生成三棱柱；
- `BRepPrimAPI_MakeBox` 生成不支持的 box；
- 用 STEP writer 写到 pytest 临时目录；
- 重新读取并断言 observation/分类。

运行：

```powershell
& $env:WELD_AGENT_PYTHONOCC_PYTHON -m pytest `
  tests\test_step_inspector.py tests\test_occ_marker_reader.py -v
```

纯分类测试不应导入 OCC；它们验证规则而不是绑定库。真实客户 STEP 只用于仓库外 manual acceptance。

## 新 OCC 几何接口清单

1. 把需要的几何观察量定义为不可变普通 Python 类型；
2. 定义 Protocol，先用 fake 实现写工作流测试；
3. 用合成 Shape 写失败的 OCC integration test；
4. 在 `src/weld_agent/geometry/` 实现最小 adapter；
5. 分类 non-finite、空 Shape、损坏 STEP 和 unsupported topology；
6. 确保 JSON 合同不包含 OCC 对象；
7. 运行 focused pytest 与完整 `verify.ps1`；
8. 用 HyperMesh runbook 验证真实 STEP，但不提交它。

HyperMesh 侧如何产生这些 STEP 和身份数据见 [HyperMesh/OCC 文件桥](hypermesh-occ-bridge.md)。
