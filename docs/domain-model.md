# 领域模型

本页统一 HyperMesh、CAD B-Rep、焊接工程和仓库合同中的术语。核心原则是区分“几何事实”和“工程语义”。

## HyperMesh 与 CAD 实体

| 术语 | 本仓库中的含义 |
|---|---|
| Model | 当前打开的 HyperMesh 模型及其实体、显示和选择状态 |
| Component | HyperMesh 中组织几何/单元的 collector；一个车门模型可以含多个钣金件和 marker Component |
| Surface | HyperMesh 几何曲面实体；导出到 STEP 后通常对应一个或多个 B-Rep Face |
| Face | OCC B-Rep 拓扑面，具有 plane、cylinder 等曲面类型 |
| Solid | OCC 中闭合的三维拓扑实体；当前 marker 识别以独立 Solid 为候选单元 |
| STEP | HyperMesh 与外部 OCC 之间的 B-Rep 交换格式；当前使用 AP214 和毫米 |

Component、Surface、Face、Solid 不是可互换概念。尤其不能用 HyperMesh Component 数直接代替 OCC Solid 数。

## Marker 几何分类

| 类型 | 几何事实 | 当前不包含的工程语义 |
|---|---|---|
| explicit marker | CAD/STEP 中已存在、由输入清单明确提供的独立 Solid | 不表示程序已经判断它应当成为焊点 |
| `cylinder` | 含圆柱侧面、两个平面端部和有限轴向的 Solid | 不能单独证明 2T、焊两次或任何工艺规范 |
| `triangular_prism` | 五个平面 Face、两个三边端面和有限轴向的 Solid | 不能单独证明 3T、焊三次或任何工艺规范 |
| `unknown` | 几何有效但不满足当前两类规则；保留拓扑证据和警告 | 不应被强行映射到最相近类型，也不等于无效焊点 |

当前车门经验提示某些形状可能编码板层或工艺信息，但几何分类不能单独证明这种约定。需要 marker 轴线、邻近板件求交、材料/工艺元数据或人工规范作为附加证据。

## 工程语义

| 术语 | 含义与当前状态 |
|---|---|
| welding face | 实际参与连接的钣金面；当前尚未识别 |
| 2T / 3T | 两层板/三层板连接语义；当前不能从 marker 形状直接确认 |
| candidate | 算法提出、等待复核的位置或连接建议；必须保持 advisory |
| Connector | HyperMesh 中表示连接意图的正式实体；创建它会修改模型 |
| Realize | 把 Connector 转换为求解器相关连接实体的后续操作，风险高于只创建未 Realize Connector |
| preview | 供人检查的位置/几何显示，不应冒充正式 Connector |

## 证据层级

| 层级 | 示例 | 可以声称什么 |
|---|---|---|
| 拓扑几何 | Face 类型、Solid、中心、轴向、包围盒 | marker 的几何类别和位置 |
| 空间关系 | 轴线与板件求交、间隙、法向、板层数 | 潜在焊接面和连接层数证据 |
| 工程元数据 | Component 语义、材料、工艺规范、命名约定 | 工艺类型和参数依据 |
| 人工批准 | 工程师复核候选与影响范围 | 是否允许预览、write-back 或创建 Connector |

因此，`cylinder`/`triangular_prism` 的几何事实不能单独证明 2T/3T 的工程语义；candidate 也不能自动升级为 Connector。

## 身份与坐标

- HyperMesh Component ID/名称保留来源身份；
- STEP 内 Solid 以该 Component 中的一基顺序编号；
- marker ID 在单次运行中由 Component ID 与 Solid index 稳定组成；
- 当前合同只接受毫米和全局坐标系；
- JSON 是正式合同，CSV 是便于人工检查的派生视图。
