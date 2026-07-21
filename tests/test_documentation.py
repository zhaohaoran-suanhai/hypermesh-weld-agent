import re
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_common_entry_points_define_the_same_reading_path() -> None:
    for relative in ("README.md", "AGENTS.md", "docs/index.md"):
        text = read(relative)
        assert "docs/current-state.md" in text
        assert "docs/architecture.md" in text
        assert "docs/integrations/" in text


def test_current_state_separates_capability_evidence_and_limits() -> None:
    text = read("docs/current-state.md")
    for heading in ("## 已验证能力", "## 验证证据", "## 当前限制", "## 开放问题"):
        assert heading in text
    for fact in ("122", "83", "39", "unknown", "2T", "3T"):
        assert fact in text
    assert "默认开发任务" in text


def test_architecture_explains_actual_process_and_contract_boundaries() -> None:
    text = read("docs/architecture.md")
    for fact in (
        "HyperMesh Tcl",
        "STEP",
        "JSON",
        "PythonOCC",
        "src/weld_agent/geometry/",
        "schemas/",
        "JSON/CSV/log",
    ):
        assert fact in text


def test_domain_model_does_not_confuse_geometry_with_engineering_semantics() -> None:
    text = read("docs/domain-model.md")
    assert "cylinder" in text
    assert "triangular_prism" in text
    assert "几何事实" in text
    assert "工程语义" in text
    assert "不能单独证明" in text
    assert "Connector" in text


INTEGRATION_FACTS = {
    "docs/integrations/local-environment.md": (
        "C:\\Program Files\\Altair\\2017",
        "hmopengl.exe",
        "hmbatch.exe",
        "Python 3.11.15",
        "OCC 7.9.0",
        "WELD_AGENT_PYTHONOCC_PYTHON",
    ),
    "docs/integrations/hypermesh-2017.md": (
        "Tcl Console",
        "source",
        "::weldagent",
        "hm_getvalue",
        "hm_getboundingbox",
        "*geomexport",
        "状态恢复",
    ),
    "docs/integrations/pythonocc.md": (
        "StepInspector",
        "MarkerStepReader",
        "CandidateProvider",
        "OCC.Display",
        "pytest",
    ),
    "docs/integrations/hypermesh-occ-bridge.md": (
        "STEP + JSON",
        "Schema",
        "临时运行目录",
        "新增非焊点功能",
        "人工复核",
    ),
}


def test_integration_documents_record_verified_local_interfaces() -> None:
    for relative, facts in INTEGRATION_FACTS.items():
        text = read(relative)
        for fact in facts:
            assert fact in text, f"{relative} must contain {fact}"


def test_maintained_documents_do_not_embed_private_python_path() -> None:
    maintained = (
        "README.md",
        "AGENTS.md",
        "docs/current-state.md",
        "docs/architecture.md",
        "docs/development.md",
        *INTEGRATION_FACTS,
    )
    for relative in maintained:
        assert "C:\\Users\\" not in read(relative)
