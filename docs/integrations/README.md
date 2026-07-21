# 本机集成文档

这里说明当前电脑上的 HyperMesh 2017、外部 PythonOCC 和仓库如何协作。它是通用前处理开发手册，不局限于焊点识别。

建议顺序：

1. [本机环境](local-environment.md)：安装位置、版本、环境变量和只读探针；
2. [HyperMesh 2017 接口](hypermesh-2017.md)：GUI/Tcl/batch、命令和状态保护；
3. [PythonOCC 接口](pythonocc.md)：外部几何内核、adapter 和测试；
4. [HyperMesh/OCC 文件桥](hypermesh-occ-bridge.md)：STEP + JSON 合同与扩展模板。

当前稳定方案不是把 Python 嵌入 HyperMesh，而是让 HyperMesh Tcl 和外部 Python 通过唯一临时运行目录交换 STEP 与 JSON。
