# 人工验收索引

这里保存必须在真实 HyperMesh/本机环境中执行的可重复检查。客户模型、STEP、manifest 和运行结果留在仓库外；runbook 只记录命令、摘要和安全证据。

| Runbook | 验证内容 | 当前证据 |
|---|---|---|
| [HyperMesh 2017 capability probe](hm2017-capability-probe.md) | Component 选择和关键 Tcl 命令存在性 | `geomexport`、旧 `geomoutputdata`、Connector create 命令均存在 |
| [HyperMesh 2017 STEP export probe](hm2017-step-export-probe.md) | 两个 Component 隔离 STEP 导出、状态恢复和 OCC 摘要 | 两个真实 STEP 可读并通过合同/包围盒验证 |
| [Terminal weld marker identification](terminal-weld-marker-identification.md) | 5 个显式 marker Component 的终端分类 | 122 = 83 cylinder + 39 triangular prism + 0 unknown |

人工验收不是自动测试替代品。先运行 pytest/`scripts/verify.ps1`，再在需要真实 HyperMesh 行为时使用本目录。
