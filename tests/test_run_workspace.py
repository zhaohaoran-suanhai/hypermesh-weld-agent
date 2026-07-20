import json
from pathlib import Path

import pytest

from weld_agent.run_workspace import RunWorkspace


def test_workspace_writes_json_atomically(tmp_path: Path) -> None:
    workspace = RunWorkspace.create("run-001", root=tmp_path)
    target = workspace.write_json("selection.json", {"run_id": "run-001"})
    assert workspace.read_json("selection.json") == {"run_id": "run-001"}
    assert target.parent == tmp_path / "run-001"
    assert not list(target.parent.glob("*.tmp"))


def test_workspace_rejects_path_traversal(tmp_path: Path) -> None:
    workspace = RunWorkspace.create("run-001", root=tmp_path)
    with pytest.raises(ValueError, match="simple file name"):
        workspace.write_json("../outside.json", {})


def test_cleanup_removes_only_cad_exports(tmp_path: Path) -> None:
    workspace = RunWorkspace.create("run-001", root=tmp_path)
    (workspace.path / "part.step").write_text("cad", encoding="utf-8")
    (workspace.path / "result.json").write_text("{}", encoding="utf-8")
    workspace.cleanup_geometry()
    assert not (workspace.path / "part.step").exists()
    assert (workspace.path / "result.json").exists()


def test_workspace_appends_structured_event_log(tmp_path: Path) -> None:
    workspace = RunWorkspace.create("run-001", root=tmp_path)
    target = workspace.append_event("analysis_completed", {"status": "success"})
    record = json.loads(target.read_text(encoding="utf-8").splitlines()[0])
    assert record["event"] == "analysis_completed"
    assert record["details"] == {"status": "success"}
    assert record["timestamp_utc"].endswith("+00:00")
