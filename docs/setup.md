# 环境设置兼容入口

环境知识已拆分为可维护的稳定文档：

- [本机已验证环境](integrations/local-environment.md)
- [开发、测试与提交](development.md)
- [HyperMesh 2017 Tcl/GUI/batch 接口](integrations/hypermesh-2017.md)
- [PythonOCC adapter 与测试](integrations/pythonocc.md)
- [HyperMesh/OCC STEP + JSON 文件桥](integrations/hypermesh-occ-bridge.md)

在仓库根目录设置当前 PythonOCC 解释器：

```powershell
$env:WELD_AGENT_PYTHONOCC_PYTHON = (Resolve-Path '..\pythonocc\.m\envs\occ\python.exe').Path
```

后续命令、版本探针和故障排查以以上文档为准，本页不再复制维护第二套说明。
