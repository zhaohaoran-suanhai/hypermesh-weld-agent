from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from weld_agent.contracts import ContractValidationError, load_document, validate_document
from weld_agent.geometry.step_inspector import StepInspectionError, StepInspector
from weld_agent.run_workspace import RUN_ID


@dataclass(frozen=True)
class FinalizationResult:
    validation_path: Path
    selection_path: Path


class ExportFinalizationError(ValueError):
    """Classified failure while validating a HyperMesh STEP export."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _bbox_delta(
    source: list[float],
    imported: tuple[float, ...],
) -> list[float]:
    return [
        float(actual - expected)
        for expected, actual in zip(source, imported, strict=True)
    ]


def _bbox_matches(
    source: list[float],
    imported: tuple[float, ...],
    absolute: float,
    relative: float,
) -> bool:
    return all(
        math.isclose(expected, actual, abs_tol=absolute, rel_tol=relative)
        for expected, actual in zip(source, imported, strict=True)
    )


def _failure_report(
    run_id: str,
    components: list[dict[str, Any]],
    warnings: list[str],
    failure: ExportFinalizationError,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "run_id": run_id,
        "status": "failure",
        "components": components,
        "warnings": warnings,
        "errors": [{"code": failure.code, "message": str(failure)}],
    }


def finalize_export(
    manifest_path: Path,
    profile_path: Path,
    inspector: StepInspector,
) -> FinalizationResult:
    run_dir = manifest_path.resolve().parent
    validation_path = run_dir / "export-validation.json"
    selection_path = run_dir / "selection.json"
    if validation_path.exists() or selection_path.exists():
        raise ExportFinalizationError(
            "OUTPUT_CONFLICT",
            "final output already exists",
        )

    run_id_hint = run_dir.name if RUN_ID.fullmatch(run_dir.name) else "unknown"
    component_reports: list[dict[str, Any]] = []
    warnings: list[str] = []

    try:
        try:
            manifest = load_document(
                manifest_path,
                "export-manifest.schema.json",
            )
        except ContractValidationError as exc:
            raise ExportFinalizationError("MANIFEST_INVALID", str(exc)) from exc
        if manifest["run_id"] != run_dir.name:
            raise ExportFinalizationError(
                "OUTPUT_CONFLICT",
                "manifest run_id does not match its directory",
            )
        run_id_hint = manifest["run_id"]
        warnings = list(manifest["warnings"])

        try:
            profile = load_document(
                profile_path,
                "integration-profile.schema.json",
            )
        except ContractValidationError as exc:
            raise ExportFinalizationError("PROFILE_INVALID", str(exc)) from exc

        selection_components: list[dict[str, Any]] = []
        for component in manifest["components"]:
            step_path = Path(component["step_path"]).resolve()
            if step_path.parent != run_dir:
                raise ExportFinalizationError(
                    "OUTPUT_CONFLICT",
                    f"STEP is outside run directory: {step_path}",
                )
            if not step_path.is_file() or step_path.stat().st_size == 0:
                raise ExportFinalizationError(
                    "STEP_READ_FAILED",
                    f"missing or empty STEP: {step_path}",
                )

            digest = _sha256(step_path)
            inspection = inspector.inspect(step_path)
            source_bbox = component["summary"]["bbox"]
            delta = _bbox_delta(source_bbox, inspection.bbox)
            matches = _bbox_matches(
                source_bbox,
                inspection.bbox,
                profile["bbox_absolute_tolerance"],
                profile["bbox_relative_tolerance"],
            )
            component_reports.append(
                {
                    "id": component["id"],
                    "step_path": str(step_path),
                    "file_size": step_path.stat().st_size,
                    "sha256": digest,
                    "read_status": "success",
                    "face_count": inspection.face_count,
                    "solid_count": inspection.solid_count,
                    "occ_bbox": list(inspection.bbox),
                    "bbox_delta": delta,
                    "checks_passed": matches,
                }
            )
            if not matches:
                raise ExportFinalizationError(
                    "EXPORT_MISMATCH",
                    f"bbox mismatch for Component {component['id']}",
                )
            selection_components.append(
                {
                    "id": component["id"],
                    "name": component["name"],
                    "geometry": {
                        "path": str(step_path),
                        "format": "STEP",
                        "sha256": digest,
                    },
                    "summary": component["summary"],
                }
            )

        success_report = {
            "schema_version": "1.0",
            "run_id": run_id_hint,
            "status": "success",
            "components": component_reports,
            "warnings": warnings,
            "errors": [],
        }
        selection = {
            "schema_version": "1.0",
            "run_id": run_id_hint,
            "hypermesh": manifest["hypermesh"],
            "components": selection_components,
            "parameters": profile["parameters"],
        }
        validate_document("export-validation.schema.json", success_report)
        validate_document("selection.schema.json", selection)
        _write_json_atomic(validation_path, success_report)
        try:
            _write_json_atomic(selection_path, selection)
        except OSError as exc:
            validation_path.unlink(missing_ok=True)
            raise ExportFinalizationError("OUTPUT_WRITE_FAILED", str(exc)) from exc
        return FinalizationResult(validation_path, selection_path)
    except StepInspectionError as exc:
        failure = ExportFinalizationError(exc.code, str(exc))
    except OSError as exc:
        failure = ExportFinalizationError("STEP_READ_FAILED", str(exc))
    except ContractValidationError as exc:
        failure = ExportFinalizationError("MANIFEST_INVALID", str(exc))
    except ExportFinalizationError as exc:
        failure = exc

    validation_path.unlink(missing_ok=True)
    report = _failure_report(
        run_id_hint,
        component_reports,
        warnings,
        failure,
    )
    validate_document("export-validation.schema.json", report)
    _write_json_atomic(validation_path, report)
    raise failure
