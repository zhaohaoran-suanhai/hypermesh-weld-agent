# HyperMesh 2017 能力探针

这个探针用于确认当前 HyperMesh 2017 build 能否提供后续阶段所需的几何导出和 Connector 命令。它不会导出几何，也不会创建节点、单元、预览实体或 Connector。

这里的“两个 Component”是同一个车门模型树中的两个钣金零件，不是两个 STEP 文件或两个模型。

## 在 HyperMesh 中运行

1. 打开汽车车门模型。
2. 打开 `View -> Command Window`。
3. 执行：

   ```tcl
   source {C:/Users/25335/Documents/GitHub/hypermesh-weld-agent/hypermesh/tcl/weld_agent_probe.tcl}
   ::weldagent::run_probe {C:/Users/25335/AppData/Local/Temp/hypermesh-weld-agent/hm2017-probe.json}
   ```

4. 选择模型树或图形区中的两个 Component，然后完成选择。
5. 确认命令返回 `hm2017-probe.json` 路径，而且模型中没有新增几何、节点、单元或 Connector。

## 验证探针结果

在仓库根目录的 PowerShell 中执行：

```powershell
& '..\pythonocc\.m\envs\occ\python.exe' -m weld_agent.cli validate `
  --schema hypermesh-probe.schema.json `
  --input "$env:TEMP\hypermesh-weld-agent\hm2017-probe.json"
```

验证成功时命令退出码为 0。JSON 中包含：

- 两个已选择 Component 的 ID 和名称；
- `geomexport`：是否存在 `*geomexport`；
- `legacy_geomoutputdata`：是否存在旧导出命令 `*geomoutputdata`；
- `connector_create`：是否存在 `*CE_ConnectorCreate`。

只记录这些能力结果，不要把客户模型或导出的几何提交到 Git。
