# HyperMesh/OCC 文件桥

当前稳定集成是 STEP + JSON 的显式文件桥，而不是进程内 API。它可被焊点以外的 HyperMesh 前处理功能复用。

## 总体流程

```text
HyperMesh 2017 当前模型
  -> 版本化 HyperMesh Tcl：选择/查询摘要/隔离/STEP 导出/状态恢复
  -> 唯一临时运行目录：STEP + JSON manifest
  -> 外部 Python 3.11：JSON Schema 校验
  -> PythonOCC adapter：读取 B-Rep、计算几何观察量
  -> 普通 Python workflow：领域处理
  -> 原子写 JSON/CSV/log
  -> 人工复核
  -> 只有显式授权后才允许 HyperMesh write-back
```

这个边界使 HyperMesh 2017 的旧 Tcl 环境、现代 Python 测试和 OCC 几何内核彼此解耦。

## 文件所有权

| 文件/对象 | 生产者 | 消费者 | 作用 |
|---|---|---|---|
| 当前 `.hm` 会话 | HyperMesh/用户 | Tcl | 权威模型；默认不保存、不覆盖 |
| Component STEP | HyperMesh Tcl | PythonOCC | B-Rep 几何交换 |
| manifest JSON | HyperMesh Tcl 或明确的上游准备步骤 | Python contracts/workflow | 身份、单位、坐标、路径和摘要 |
| validation/selection JSON | Python export finalizer | 下游 provider/人工 | 确认导出可读且摘要一致 |
| observation dataclass | OCC adapter | 普通 Python workflow | 隔离 OCC 类型 |
| result JSON | workflow | 人工/未来受控下游 | 正式机器合同 |
| CSV/log | workflow | 人工 | 检查与追踪 |

JSON 是正式合同；CSV 是派生视图；STEP 和运行结果均留在仓库外。

## Schema 地图

| Schema | 场景 |
|---|---|
| `hypermesh-probe.schema.json` | HM2017 命令能力与所选 Component |
| `export-manifest.schema.json` | 恰好两个 Component 的独立 STEP 导出 |
| `export-validation.schema.json` | OCC 可读性和 HyperMesh/OCC 摘要比较 |
| `selection.schema.json` | 进入 candidate provider 的选择合同 |
| `marker-input-manifest.schema.json` | 一个或多个显式 marker Component STEP |
| `weld-markers.schema.json` | marker 几何分类结果 |
| `weld-candidates.schema.json` | advisory candidate 结果 |

新增功能应新增或复用语义匹配的 Schema，不要给旧合同塞入无关字段。

## 临时运行目录

标准位置：

```text
%TEMP%\hypermesh-weld-agent\<run_id>\
```

要求：

- `run_id` 唯一并写入 manifest；
- STEP 路径是绝对路径，便于跨进程读取；
- manifest 保存模型来源、Component 身份、单位和全局坐标系；
- 结果写在同一运行目录的明确子目录；
- 已存在正式结果时返回 `OUTPUT_CONFLICT`，创建新运行而不是覆盖；
- 运行目录和客户数据不进入 Git。

## 错误和完整性

- Tcl 导出后检查 STEP 存在且非空；
- Python 在 OCC 前先做 Schema、单位、路径和身份校验；
- OCC 区分 `STEP_READ_FAILED` 与 `EMPTY_IMPORTED_SHAPE`；
- 几何层拒绝 non-finite 数据和反转 bbox；
- JSON/CSV/log 先写 `.tmp` 再原子替换；
- Tcl 主流程与状态恢复错误分别保留；
- 终端输出阶段、错误码、数量和产物路径，不隐藏执行。

## 两个现有实例

### 双 Component 导出

HyperMesh 交互选择两个钣金 Component，Tcl 分别导出 STEP，外部 `finalize-export` 用 `StepInspector` 比较拓扑/包围盒并生成 `selection.json`。该实例验证桥本身，不声称找到焊点。

### 显式 marker 识别

本地 manifest 列出多个小型 STEP Component，`MarkerStepReader` 提取 Solid observation，普通 Python 分类并写 `weld-markers.json`/CSV/log。该实例验证几何分类，不声称已经确认 2T/3T 或 welding face。

## 新增非焊点功能

以下流程适用于几何质量、Component 分析、孔/边/间隙识别、清理建议等其他 HyperMesh 功能：

1. **能力探针**：在 HM2017 用只读 Tcl 确认命令、entity、mark 和返回格式；
2. **合同先行**：定义 JSON Schema，冻结单位、坐标、身份、输入和输出；
3. **Tcl adapter**：使用 `::weldagent`、显式参数、唯一目录、分类错误和状态恢复；
4. **Python/OCC adapter**：只在 geometry 层接触 OCC，返回普通 Python observation；
5. **领域 workflow**：独立于 HyperMesh/OCC 实现判断、排序和结果合同；
6. **自动测试**：fake adapter 测工作流，合成 OCC Shape 测几何，静态测试约束 Tcl；
7. **人工 runbook**：在真实 HyperMesh 中验证输入、输出、计数和模型状态；
8. **人工复核和授权**：默认只报告；任何保存、删除、write-back 或 Connector 操作必须单独批准。

这个顺序使新功能可以替换几何算法而不重写 HyperMesh 与 Agent 接口。

## 何时不使用 STEP 桥

只有在 STEP 明确丢失任务必需信息（例如网格、属性、材料、装配语义或特定实体 ID）时，才设计额外 JSON、求解器 deck 或其他导出。先明确缺失信息和新合同，不要为了“更直接”而把任意 Tcl 命令暴露给外部 Agent。
