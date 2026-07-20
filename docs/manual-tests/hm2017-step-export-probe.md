# HyperMesh 2017 双 Component STEP 导出探针

本检查验证：在不修改当前 HyperMesh 模型的前提下，将两个明确选择的 Component 分别导出为 STEP，并由 PythonOCC 读取、计算摘要，最终生成 `selection.json`。

本检查不会识别焊点，不会创建预览、Connector 或网格，也不会保存当前 `.hm` 模型。

## 1. 测试对象

在当前汽车车门模型中选择：

- Component 15：`6101081-DD01-A`；
- Component 20：`6101161-DD01-A`。

模型单位已根据整体尺寸确认采用毫米。探针固定使用 STEP AP214 和 Millimeters。

## 2. 记录运行前状态

在 HyperMesh 的 `View -> Command Window` 中执行：

```tcl
*clearmark components 1
*createmark components 1 displayed
puts "BEFORE_DISPLAYED_COMPONENTS=[hm_getmark components 1]"
foreach entity_type {surfaces solids elements connectors} {
    *clearmark $entity_type 1
    *createmark $entity_type 1 all
    puts "BEFORE_[string toupper $entity_type]_COUNT=[hm_marklength $entity_type 1]"
}
```

保存这些输出。验收时要与导出后的状态逐项比较。

## 3. 执行 HyperMesh 导出

继续在 Command Window 中执行：

```tcl
source {C:/Users/25335/Documents/GitHub/hypermesh-weld-agent/hypermesh/tcl/weld_agent_export.tcl}
set manifest [::weldagent::run_export_probe {C:/Users/25335/AppData/Local/Temp/hypermesh-weld-agent}]
puts "MANIFEST=$manifest"
```

出现 Component 选择面板后：

1. 点击黄色 `comps` 按钮打开 Component 列表；
2. 勾选 `6101081-DD01-A`（ID 15）和 `6101161-DD01-A`（ID 20）左侧的复选框；
3. 点击列表中的绿色 `select`，返回主面板后点击 `proceed`；
4. 等待命令返回 `MANIFEST=...\export-manifest.json`。

如果命令报错，不要重复使用同一个运行目录，也不要手工把不完整 STEP 当作有效输入。复制完整错误信息用于诊断。

## 4. 记录运行后状态

导出命令返回后执行：

```tcl
*clearmark components 1
*createmark components 1 displayed
puts "AFTER_DISPLAYED_COMPONENTS=[hm_getmark components 1]"
foreach entity_type {surfaces solids elements connectors} {
    *clearmark $entity_type 1
    *createmark $entity_type 1 all
    puts "AFTER_[string toupper $entity_type]_COUNT=[hm_marklength $entity_type 1]"
}
```

必须满足：

- `BEFORE_DISPLAYED_COMPONENTS` 与 `AFTER_DISPLAYED_COMPONENTS` 完全一致；
- Surface、Solid、Element、Connector 数量逐项一致；
- 模型没有被自动保存或覆盖；
- 没有新增预览实体或 Connector。

## 5. 使用 PythonOCC 最终化

在仓库根目录打开 PowerShell，执行：

```powershell
$occPython = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
$manifestPath = Read-Host 'Paste MANIFEST path printed by HyperMesh'
& $occPython -m weld_agent.cli finalize-export `
  --manifest $manifestPath `
  --profile '.\config\integration-probe-1.json'
```

成功时命令打印 `selection.json` 的绝对路径。然后执行：

```powershell
$runDir = Split-Path -Parent $manifestPath
& $occPython -m weld_agent.cli validate `
  --schema export-validation.schema.json `
  --input (Join-Path $runDir 'export-validation.json')
& $occPython -m weld_agent.cli validate `
  --schema selection.schema.json `
  --input (Join-Path $runDir 'selection.json')
Get-Content (Join-Path $runDir 'export-validation.json')
```

两个 `validate` 命令都应以退出码 0 完成。校验报告必须显示：

- `status` 为 `success`；
- 两个 Component 都有非空文件、SHA-256、Face/Solid 数量和有限包围盒；
- 两个 `checks_passed` 都为 `true`；
- `errors` 为空。

包围盒比较采用 `绝对容差 + 相对容差 × 该轴零件跨度`，而不是按全局坐标值计算相对容差。因此，同一零件在全局坐标系中平移后不会改变校验结果。OCC 侧使用不依赖三角网格近似的最优包围盒。

## 6. 已验证的真实模型结果

2026-07-21 已在当前 34-Component 车门模型上完成一次端到端验证：

- Component 15：STEP 14,626,038 bytes，OCC 读取到 775 Faces、0 Solids；
- Component 20：STEP 7,446,703 bytes，OCC 读取到 981 Faces、1 Solid；
- Component 15 六个包围盒坐标差值（OCC − HyperMesh，mm）：`[-0.0103648, -0.0045167, -0.0010731, 0.0025567, 0.0000038, 0.0007975]`；
- Component 20 六个包围盒坐标差值（OCC − HyperMesh，mm）：`[-0.0000551, -0.0060481, -0.0000108, 0.0063874, -0.0042696, 0.0011484]`；
- 两个 Component 的 STEP 均通过包围盒一致性与 JSON Schema 校验，并生成 `selection.json`；
- 运行前后均为 34 个显示 Component、17,514 Surfaces、160 Solids、0 Elements、0 Connectors；
- 未保存或覆盖 HyperMesh 模型，未创建 Connector。

这些计数只证明导出接口对本次输入有效，不代表已经实现焊点识别。

## 7. 数据边界

本次生成的 STEP、manifest、校验报告和 selection 都位于：

```text
%TEMP%\hypermesh-weld-agent\<run-id>\
```

它们属于包含客户模型信息的本地诊断数据：

- 不要提交到 Git；
- 不要上传到网络；
- 不要把 STEP 内容粘贴到聊天中；
- 反馈结果时只需提供命令状态、Component ID、实体计数、包围盒差值和错误信息。
