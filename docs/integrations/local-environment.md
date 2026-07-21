# 本机已验证开发环境

本页记录 2026-07-21 在当前 Windows 电脑上只读检查得到的环境事实。安装升级或迁移机器后应重新运行探针并更新本页。

## HyperWorks 2017

安装根目录：`C:\Program Files\Altair\2017`

| 用途 | 已验证路径 |
|---|---|
| HyperMesh GUI | `C:\Program Files\Altair\2017\hm\bin\win64\hmopengl.exe` |
| HyperMesh batch | `C:\Program Files\Altair\2017\hm\bin\win64\hmbatch.exe` |
| HyperWorks 入口 | `C:\Program Files\Altair\2017\hw\bin\win64\hw.exe` |

只读检查：

```powershell
$hmRoot = 'C:\Program Files\Altair\2017'
Get-Item `
  (Join-Path $hmRoot 'hm\bin\win64\hmopengl.exe'), `
  (Join-Path $hmRoot 'hm\bin\win64\hmbatch.exe'), `
  (Join-Path $hmRoot 'hw\bin\win64\hw.exe')
```

GUI 和 batch 是不同入口。当前仓库的交互式选择/导出脚本已在 GUI Tcl Console 验证；除非有专门测试，不要假定它们可直接由 `hmbatch.exe` 无交互运行。

## PythonOCC

相对仓库根目录的解释器：`..\pythonocc\.m\envs\occ\python.exe`

已验证版本：

- Python 3.11.15；
- OCC 7.9.0。

正式脚本通过环境变量获得解释器：

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
```

只读版本探针：

```powershell
& $env:WELD_AGENT_PYTHONOCC_PYTHON -c `
  "import sys; from OCC import VERSION; print(sys.version.split()[0]); print(VERSION)"
```

仓库 runtime 探针：

```powershell
& $env:WELD_AGENT_PYTHONOCC_PYTHON -m weld_agent.cli doctor `
  --pythonocc-python $env:WELD_AGENT_PYTHONOCC_PYTHON
```

不得把环境变量解析后的用户目录绝对路径提交到 Git。其他机器可设置同名变量指向自己的 PythonOCC 解释器。

## 仓库与临时目录

- 所有开发命令默认从仓库根目录执行；
- 客户几何和中间结果使用 `%TEMP%\hypermesh-weld-agent\<run_id>\`；
- 每次真实运行使用唯一 `run_id`，不要复用包含完整结果的目录；
- Git 只保存 Tcl、Python、Schema、测试和不含客户数据的文档。

## 常见问题

### 找不到 PythonOCC interpreter

确认相邻环境存在并重新设置 `WELD_AGENT_PYTHONOCC_PYTHON`。不要修改脚本去猜测磁盘路径。

### OCC import 失败

用同一个解释器运行 `from OCC import VERSION`，检查是否误用了系统 Python。项目要求 Python `>=3.11,<3.12`。

### HyperMesh 无法启动

先确认 executable 存在，再检查 Altair license 和当前机器环境。启动/许可证失败与仓库几何算法分开诊断。

### Tcl 命令在 batch 中失败

先确认该 proc 是否包含 `*createmarkpanel` 等 GUI 交互；当前交互式 proc 不能自动视为 batch-safe。为 batch 单独设计无交互入口和测试。

### 结果报 `OUTPUT_CONFLICT`

保留旧结果用于审计，创建新的 `run_id` 目录。不要直接删除或覆盖已有成功结果。

### pytest 临时目录权限异常

先确认问题是否来自测试沙箱/ACL，而非 OCC 几何实现；用相同 Python 在正常终端复现，并保留具体错误输出。

## 可移植性边界

`C:\Program Files\Altair\2017` 和上述版本是当前电脑的已验证事实；Python 版本范围、环境变量名、文件合同和安全规则是仓库级要求。迁移机器时允许安装位置改变，但必须更新本机探针结果，不能把旧路径当作产品保证。
