import json
from pathlib import Path

from weld_agent.cli import main
from weld_agent.marker_identification import (
    IdentificationArtifacts,
    MarkerIdentificationError,
    PROGRESS_MESSAGES,
)


def test_identify_markers_prints_progress_summary_and_paths(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "marker-identification"
    output_dir.mkdir()
    json_path = output_dir / "weld-markers.json"
    csv_path = output_dir / "weld-markers.csv"
    log_path = output_dir / "identify-weld-markers.log"
    json_path.write_text(
        json.dumps(
            {
                "summary": {
                    "component_count": 5,
                    "marker_count": 122,
                    "cylinder_marker": 83,
                    "triangular_marker": 39,
                    "unknown_marker": 0,
                }
            }
        ),
        encoding="utf-8",
    )

    def fake_identify(manifest_path, reader, emit):
        assert manifest_path == tmp_path / "input.json"
        for message in PROGRESS_MESSAGES:
            emit(message)
        return IdentificationArtifacts(json_path, csv_path, log_path)

    monkeypatch.setattr("weld_agent.cli.identify_weld_markers", fake_identify)
    code = main(
        ["identify-markers", "--manifest", str(tmp_path / "input.json")]
    )

    assert code == 0
    output = capsys.readouterr().out
    assert "[1/4] 检查 PythonOCC 运行环境" in output
    assert "component_count       5" in output
    assert "marker_count        122" in output
    assert "cylinder_marker      83" in output
    assert "triangular_marker    39" in output
    assert "unknown_marker        0" in output
    assert f"详细结果：{json_path}" in output
    assert f"表格结果：{csv_path}" in output
    assert f"运行日志：{log_path}" in output


def test_identify_markers_reports_classified_failure(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    def fail(*args, **kwargs):
        raise MarkerIdentificationError(
            "STEP_READ_FAILED",
            "missing component-5.step",
        )

    monkeypatch.setattr("weld_agent.cli.identify_weld_markers", fail)
    code = main(
        ["identify-markers", "--manifest", str(tmp_path / "input.json")]
    )
    assert code == 2
    assert (
        "error: STEP_READ_FAILED: missing component-5.step"
        in capsys.readouterr().err
    )
