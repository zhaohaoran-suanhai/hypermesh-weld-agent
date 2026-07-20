from pathlib import Path

from weld_agent.cli import main
from weld_agent.export_finalizer import ExportFinalizationError, FinalizationResult


def test_finalize_export_dispatches_and_prints_selection(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    manifest = tmp_path / "export-manifest.json"
    profile = tmp_path / "profile.json"
    selection = tmp_path / "selection.json"
    validation = tmp_path / "export-validation.json"
    manifest.write_text("{}", encoding="utf-8")
    profile.write_text("{}", encoding="utf-8")

    def fake_finalize(manifest_path, profile_path, inspector):
        assert manifest_path == manifest
        assert profile_path == profile
        return FinalizationResult(validation, selection)

    monkeypatch.setattr("weld_agent.cli.finalize_export", fake_finalize)
    exit_code = main(
        [
            "finalize-export",
            "--manifest",
            str(manifest),
            "--profile",
            str(profile),
        ]
    )
    assert exit_code == 0
    assert capsys.readouterr().out.strip() == str(selection)


def test_finalize_export_reports_classified_failure(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    manifest = tmp_path / "export-manifest.json"
    profile = tmp_path / "profile.json"

    def fake_finalize(manifest_path, profile_path, inspector):
        raise ExportFinalizationError("EXPORT_MISMATCH", "bbox mismatch")

    monkeypatch.setattr("weld_agent.cli.finalize_export", fake_finalize)
    exit_code = main(
        [
            "finalize-export",
            "--manifest",
            str(manifest),
            "--profile",
            str(profile),
        ]
    )
    assert exit_code == 2
    assert "EXPORT_MISMATCH: bbox mismatch" in capsys.readouterr().err
