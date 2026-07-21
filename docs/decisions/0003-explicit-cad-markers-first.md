# ADR-0003：第一个验证应用优先识别 CAD 显式 marker

## Status

Accepted

## Context

车门 CAD 中已经存在独立的圆柱和三棱柱类标记。相比直接从钣金搭接关系生成新焊点，识别这些显式 Solid 的输入边界更清楚，也能先验证 HyperMesh STEP 导出、OCC 拓扑读取、几何分类和结果合同。形状可能携带板层/工艺约定，但缺少板件求交和规范证据时不能确认该语义。

## Decision

第一个真实应用只分类明确输入 STEP Component 中已有的独立 Solid marker：`cylinder`、`triangular_prism` 或 `unknown`。它不扫描完整车门，不根据搭接区域生成焊点，不把几何类型写死为 2T/3T，也不识别 welding face。

这个决定限制第一个应用，不限制仓库平台。其他 HyperMesh 几何或前处理功能可以复用 Tcl → STEP/JSON → PythonOCC → 普通 Python workflow 的接口。

## Consequences

- 当前样本得到可重复的 122/83/39 几何基线；
- 几何分类和工程语义在合同与文档中保持分离；
- 板层、焊接面和新焊点生成需要独立设计与证据；
- 新任务不应因为仓库名称而被迫沿焊点路线开发。
