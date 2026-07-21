# 终端焊点标记识别设计规格

日期：2026-07-21  
状态：已批准

## 1. 目标

第一阶段只识别汽车车门 CAD 中已经存在的显式焊点标记，并通过仓库中的版本化脚本在终端报告结果。

系统回答：

> 当前导出的 CAD 几何中有哪些可识别的焊点标记，它们位于哪里，属于哪一种几何类型？

这一阶段不根据钣金搭接关系重新生成焊点，也不判断焊接面、板层数或 Connector 参数。

## 2. 使用方式

OCC 作为后台几何内核运行，不要求用户打开 OCC 图形界面。用户在仓库根目录运行一个 PowerShell 启动脚本：

```powershell
.\scripts\identify_weld_markers.ps1 -InputManifest <marker-input-manifest.json>
```

启动脚本负责检查运行环境、调用项目 CLI，并把 Python/OCC 的标准输出直接显示在当前终端。脚本不得隐藏启动新的终端窗口。

终端至少显示：

```text
[1/4] 检查 PythonOCC 运行环境
[2/4] 读取 HyperMesh STEP 导出清单
[3/4] 识别焊点标记
[4/4] 写入识别结果

识别完成
  component_count       5
  marker_count        122
  cylinder_marker      83
  triangular_marker    39
  unknown_marker        0

详细结果：<run_dir>\weld-markers.json
表格结果：<run_dir>\weld-markers.csv
运行日志：<run_dir>\identify-weld-markers.log
```

错误必须输出明确的错误代码、原因和失败阶段，并以非零退出码结束。

## 3. 输入边界

输入为本功能专用的 `marker-input-manifest.json`，其中列出一个或多个明确选定的小型候选 Component 及其 STEP 文件。它与现有固定包含两个钣金件的 `export-manifest.json` 相互独立，不修改已有两 Component 导出合同。

每个 Component 输入至少包含：

- HyperMesh Component ID；
- Component 名称；
- STEP 文件绝对路径；
- 曲面数、实体数和包围盒；
- 模型单位，第一版只接受毫米；
- HyperMesh build 和源模型名称；
- 唯一运行编号。

第一版采用“小部件验证”范围：由用户或上游 HyperMesh 导出步骤明确指定疑似包含焊点标记的少量 Component。当前车门回归样本明确输入 5 个名称含 `(SW)` 的 Component，但识别程序不依赖名称字符串完成几何分类，也不扫描其余 29 个 Component。识别程序不读取 `.hm` 文件、不控制 HyperMesh，也不根据名称自动扩大输入范围。

输入 STEP 和客户 CAD 不复制到 Git 仓库。运行结果写入仓库外的唯一运行目录：

```text
%TEMP%\hypermesh-weld-agent\<run_id>\marker-identification\
```

## 4. 识别规则

识别以 STEP B-Rep 中彼此独立的 Solid 为最小候选单元。每个 Solid 通过 OCC 拓扑和解析曲面类型分类，不依赖截图、颜色或屏幕投影。

第一版支持两类已在当前车门样本中观测到的标记：

### 4.1 圆柱类标记

满足以下特征：

- 包含圆柱曲面；
- 包含两个端部平面；
- 能从圆柱曲面获得有限、非零的轴线方向；
- 能计算有限的实体质心、包围盒和尺寸。

当前车门样本可能因为 STEP 拓扑分割而把一个圆柱侧面表示为两个圆柱 Face，因此分类不能固定要求恰好一个圆柱 Face。

### 4.2 三棱柱类标记

满足以下特征：

- 所有 Face 均为平面；
- 存在两个三边形端面；
- 两个三边形端面中心可以确定有限、非零的轴线；
- 能计算有限的实体质心、包围盒和尺寸。

### 4.3 未知标记

不能可靠匹配上述规则的 Solid 必须输出为 `unknown`，同时记录实际 Face 数、曲面类型统计、端面边数统计和警告。禁止静默丢弃，也禁止选择一个“最接近”的已知类型冒充成功识别。

第一版只报告几何类型。`cylinder` 是否代表 2T、`triangular_prism` 是否代表 3T，属于后续板层验证阶段，不写死在本阶段识别合同中。

## 5. 输出合同

主输出文件为 `weld-markers.json`。顶层至少包含：

- `schema_version`；
- `run_id`；
- 输入 manifest 路径和摘要；
- OCC 和算法版本；
- 单位和坐标系；
- Component 级统计；
- 焊点标记列表；
- 警告和总耗时。

每个标记至少包含：

- 稳定的本次运行标记 ID；
- 来源 Component ID 和名称；
- 来源 Solid 在该 Component 中的顺序号；
- `marker_type`：`cylinder`、`triangular_prism` 或 `unknown`；
- 全局坐标系中心点；
- 单位化轴线；
- 包围盒和三个方向尺寸；
- Face 数和曲面类型统计；
- 分类所依据的证据；
- 警告列表。

同时生成扁平的 `weld-markers.csv` 供人工检查。CSV 是 JSON 的派生视图，JSON 是正式合同。

输出必须使用临时文件写完后原子替换目标文件，避免中断时留下貌似完整的半文件。同一 `run_id` 的输入、参数和结果必须可以追溯。

## 6. 代码边界

计划新增以下职责清晰的模块：

```text
src/weld_agent/geometry/marker_identification.py
    纯领域结果类型、分类规则和单个 Shape 的识别流程

src/weld_agent/geometry/occ_marker_reader.py
    STEP 读取、OCC 拓扑遍历和几何量提取

src/weld_agent/marker_identification.py
    manifest 校验、运行编排、JSON/CSV/日志写入

schemas/marker-input-manifest.schema.json
    一个或多个候选标记 Component 的输入合同

scripts/identify_weld_markers.ps1
    Windows 终端入口和 PythonOCC 解释器检查
```

CLI 接入现有 `weld_agent.cli`，不另建第二套命令框架。OCC 对象不得进入 JSON 合同或工作流层。几何规则接收普通 Python 数据并返回普通领域结果，以便不启动 GUI 即可测试。

本地 PythonOCC 绝对路径不得提交。启动脚本优先读取：

```text
WELD_AGENT_PYTHONOCC_PYTHON
```

未设置或路径无效时，脚本必须给出配置命令示例并退出，不在磁盘中猜测解释器位置。

## 7. 错误处理

第一版错误代码包括：

- `RUNTIME_UNAVAILABLE`：PythonOCC 解释器或 OCC 模块不可用；
- `INVALID_MANIFEST`：输入清单不符合合同；
- `STEP_READ_FAILED`：STEP 不存在、为空或 OCC 无法读取；
- `EMPTY_IMPORTED_SHAPE`：没有可识别的 Face 或 Solid；
- `INVALID_GEOMETRY`：中心、包围盒或候选轴线包含非有限值，无法写入可靠结果；
- `UNIT_MISMATCH`：输入不是毫米或单位不一致；
- `OUTPUT_CONFLICT`：目标运行结果已存在且没有显式覆盖许可；
- `OUTPUT_WRITE_FAILED`：结果无法完整写入。

单个 Solid 分类为 `unknown` 不导致整个运行失败；文件损坏、合同错误或运行时缺失导致整个运行失败。

## 8. 可观察性与协作约束

- 所有正式分析必须由仓库中的版本化脚本执行；
- 不使用隐藏的一次性内联 Python 作为正式验证证据；
- 终端显示阶段、数量、耗时、警告和输出位置；
- 详细逐点数据进入 JSON/CSV，不用海量终端输出淹没摘要；
- 每个结论都能从输入 manifest、脚本版本和结果文件复现；
- OCC 图形界面不属于第一版交付，后续只能作为可选调试工具加入。

## 9. 测试与验收

自动化测试至少覆盖：

- OCC 生成的圆柱样例被识别为 `cylinder`；
- OCC 生成的三棱柱样例被识别为 `triangular_prism`；
- 不支持的实体输出为 `unknown` 且保留证据；
- 非有限中心或零长度轴线被拒绝；
- 多个 STEP Component 的标记 ID 唯一且顺序确定；
- manifest 损坏、STEP 缺失和单位错误产生指定错误；
- JSON 和 CSV 数量一致；
- 输出文件采用原子写入；
- 相同输入产生相同排序和分类结果；
- PowerShell 启动脚本在运行时缺失时给出可操作错误。

车门人工验收使用明确指定的本地运行目录，不把 STEP 或 `.hm` 文件提交到 Git。验收成功要求：

1. 用户在仓库终端运行一条命令即可启动；
2. 终端持续显示可理解的阶段和最终统计；
3. 当前车门样本识别出 122 个独立 Solid 标记；
4. 结果中记录 83 个圆柱类和 39 个三棱柱类标记，未知数量为 0；
5. JSON、CSV 和日志均能定位到对应 Component 和 Solid；
6. 运行不打开 OCC GUI，不修改或保存 HyperMesh 模型，也不创建 Connector。

第 3、4 项是当前样本的回归基线，不代表其他车型必须具有相同数量。

## 10. 非目标与后续阶段

第一版明确不实现：

- 扫描车门全部 34 个 Component；
- 自动发现应该导出的 HyperMesh Component；
- 识别焊接面或相邻钣金件；
- 验证 2T/3T 板层数语义；
- 根据搭接区域生成新焊点；
- 在 HyperMesh 中创建预览点或 Connector；
- 自动保存、覆盖或修改 `.hm` 模型；
- Agent 自动接受几何结论；
- OCC 图形界面。

第一版通过复核后，下一份独立设计再处理“焊点轴线与邻近板件求交、验证 2T/3T 和识别焊接面”。
