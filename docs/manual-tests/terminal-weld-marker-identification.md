# 终端焊点标记识别

本手册验证第一阶段闭环：对明确选择的小型 STEP Component 中已有的显式 Solid 标记进行几何分类，并在当前终端输出结果。该阶段不扫描完整车门，不推断 2T/3T，不识别焊接面，不修改 HyperMesh，也不创建 Connector。

## 前提

- 在仓库根目录运行命令；
- PythonOCC 使用 Python 3.11，且已安装本项目；
- 候选 Component 已分别导出为 STEP；
- 本地 manifest 符合 `schemas/marker-input-manifest.schema.json`；
- STEP、manifest 和结果目录位于仓库外，不提交到 Git。

OCC 只作为后台几何库运行，不需要打开 OCC GUI。

## 1. 配置解释器

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
```

也可以在启动命令中使用 `-PythonOccPython` 显式传入解释器。

## 2. 准备输入 manifest

为本次运行新建唯一目录，例如：

```text
%TEMP%\hypermesh-weld-agent\door-marker-20260721-001\
```

在其中创建 `marker-input-manifest.json`。每个 Component 记录 HyperMesh ID、名称、STEP 绝对路径、曲面数、实体数、单元数和全局包围盒。当前车门基线只包含 Component 5、8、12、13、21；识别器不会因为名称含 `(SW)` 而自动扫描其他 Component。

## 3. 运行

```powershell
$manifestPath = 'C:\absolute\run-directory\marker-input-manifest.json'
.\scripts\identify_weld_markers.ps1 -InputManifest $manifestPath
```

终端应依次显示：

```text
[1/4] 检查 PythonOCC 运行环境
[2/4] 读取焊点 Component STEP
[3/4] 识别焊点标记
[4/4] 写入识别结果
```

成功后还会显示 Component 数、标记总数、圆柱类、三棱柱类、未知类数量，以及三个结果文件的绝对路径。

## 4. 检查结果

结果位于 manifest 同级目录：

```text
marker-identification\weld-markers.json
marker-identification\weld-markers.csv
marker-identification\identify-weld-markers.log
```

JSON 是正式合同；CSV 是便于人工检查的扁平视图；日志保留阶段、统计与路径。每个标记都必须包含来源 Component 和从 1 开始的 Solid 序号。

可以只读检查：

```powershell
$resultDir = Join-Path (Split-Path -Parent $manifestPath) 'marker-identification'
Get-Content (Join-Path $resultDir 'weld-markers.json') -Encoding UTF8
Import-Csv (Join-Path $resultDir 'weld-markers.csv') | Group-Object marker_type
```

若提示 `OUTPUT_CONFLICT`，保留已有结果，创建新的唯一运行目录和 `run_id` 后再运行。

## 5. 当前车门回归基线

2026-07-21 已用仓库脚本在本机真实运行并通过：

- 运行编号：`door-marker-20260721-001`；
- Component 5：14 圆柱，0 三棱柱；
- Component 8：2 圆柱，0 三棱柱；
- Component 12：50 圆柱，14 三棱柱；
- Component 13：17 圆柱，22 三棱柱；
- Component 21：0 圆柱，3 三棱柱；
- 总数：122；
- 圆柱类：83；
- 三棱柱类：39；
- 未知类：0；
- JSON 标记数与 CSV 行数均为 122；
- 122 条记录均包含 marker、Component 和 Solid 身份；
- 运行期间没有打开 OCC GUI，没有修改 HyperMesh 模型，也没有创建 Connector。

这些数量只用于当前车门样本回归，不是其他车型的工程标准，也不能单独证明圆柱等于 2T、三棱柱等于 3T。

## 6. 自动化验证

`scripts/verify.ps1` 使用未过滤的 pytest 调用，因此会自动发现焊点标记识别相关测试；不把客户数据运行加入 CI。
