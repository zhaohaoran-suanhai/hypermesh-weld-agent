import hashlib
import json
from pathlib import Path

import pytest

from weld_agent.contracts import load_document
from weld_agent.export_finalizer import ExportFinalizationError, finalize_export
from weld_agent.geometry.step_inspector import StepInspection, StepInspectionError


FIXTURES = Path(__file__).parent / "fixtures"


class FakeInspector:
    def inspect(self, path: Path) -> StepInspection:
        return StepInspection(12, 0, (0, 0, 0, 100, 50, 5))


def _manifest(tmp_path: Path) -> Path:
    run_dir = tmp_path / "hm-test-run"
    run_dir.mkdir()
    payload = json.loads(
        (FIXTURES / "export_manifest.valid.json").read_text(encoding="utf-8")
    )
    payload["run_id"] = run_dir.name
    for component in payload["components"]:
        step = run_dir / f"component-{component['id']}.step"
        step.write_bytes(f"STEP-{component['id']}".encode("ascii"))
        component["step_path"] = str(step.resolve())
        component["summary"]["bbox"] = [0, 0, 0, 100, 50, 5]
    path = run_dir / "export-manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_finalize_writes_valid_selection_after_validation(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    result = finalize_export(
        manifest,
        FIXTURES / "integration_profile.valid.json",
        FakeInspector(),
    )

    selection = load_document(result.selection_path, "selection.schema.json")
    validation = load_document(
        result.validation_path,
        "export-validation.schema.json",
    )
    expected = hashlib.sha256(
        (manifest.parent / "component-15.step").read_bytes()
    ).hexdigest()
    assert selection["components"][0]["geometry"]["sha256"] == expected
    assert selection["parameters"]["rule_profile_version"].startswith(
        "integration-probe-1"
    )
    assert validation["status"] == "success"
    assert [item["checks_passed"] for item in validation["components"]] == [
        True,
        True,
    ]


def test_bbox_mismatch_writes_failure_report_but_no_selection(tmp_path: Path) -> None:
    class MismatchInspector:
        def inspect(self, path: Path) -> StepInspection:
            return StepInspection(1, 0, (0, 0, 0, 1000, 500, 50))

    manifest = _manifest(tmp_path)
    with pytest.raises(ExportFinalizationError) as caught:
        finalize_export(
            manifest,
            FIXTURES / "integration_profile.valid.json",
            MismatchInspector(),
        )

    assert caught.value.code == "EXPORT_MISMATCH"
    assert not (manifest.parent / "selection.json").exists()
    report = load_document(
        manifest.parent / "export-validation.json",
        "export-validation.schema.json",
    )
    assert report["status"] == "failure"
    assert report["errors"][0]["code"] == "EXPORT_MISMATCH"
    assert report["components"][0]["checks_passed"] is False


def test_inspector_failure_is_preserved_in_failure_report(tmp_path: Path) -> None:
    class FailingInspector:
        def inspect(self, path: Path) -> StepInspection:
            raise StepInspectionError("STEP_READ_FAILED", "forced read failure")

    manifest = _manifest(tmp_path)
    with pytest.raises(ExportFinalizationError) as caught:
        finalize_export(
            manifest,
            FIXTURES / "integration_profile.valid.json",
            FailingInspector(),
        )

    assert caught.value.code == "STEP_READ_FAILED"
    report = load_document(
        manifest.parent / "export-validation.json",
        "export-validation.schema.json",
    )
    assert report["components"] == []
    assert report["errors"][0]["message"] == "forced read failure"


def test_existing_final_output_is_never_overwritten(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    existing = manifest.parent / "selection.json"
    existing.write_text("user-owned", encoding="utf-8")

    with pytest.raises(ExportFinalizationError) as caught:
        finalize_export(
            manifest,
            FIXTURES / "integration_profile.valid.json",
            FakeInspector(),
        )

    assert caught.value.code == "OUTPUT_CONFLICT"
    assert existing.read_text(encoding="utf-8") == "user-owned"
    assert not (manifest.parent / "export-validation.json").exists()
