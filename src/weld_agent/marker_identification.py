from __future__ import annotations

import csv
import hashlib
import json
import os
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from weld_agent.contracts import (
    ContractValidationError,
    validate_document,
)
from weld_agent.geometry.marker_identification import (
    InvalidMarkerGeometry,
    MarkerRecord,
    classify_marker,
)
from weld_agent.geometry.occ_marker_reader import MarkerStepReadError, MarkerStepReader


ALGORITHM_VERSION = "marker-topology-1.0"
PROGRESS_MESSAGES = (
    "[1/4] 检查 PythonOCC 运行环境",
    "[2/4] 读取焊点 Component STEP",
    "[3/4] 识别焊点标记",
    "[4/4] 写入识别结果",
)


@dataclass(frozen=True)
class IdentificationArtifacts:
    json_path: Path
    csv_path: Path
    log_path: Path


class MarkerIdentificationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _read_manifest(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MarkerIdentificationError(
            "INVALID_MANIFEST",
            f"cannot read marker manifest {path}: {exc}",
        ) from exc
    if not isinstance(payload, dict):
        raise MarkerIdentificationError(
            "INVALID_MANIFEST",
            "marker manifest root must be an object",
        )
    hypermesh = payload.get("hypermesh")
    if not isinstance(hypermesh, dict) or (
        hypermesh.get("units") != "mm"
        or hypermesh.get("coordinate_system") != "global"
    ):
        raise MarkerIdentificationError(
            "UNIT_MISMATCH",
            "marker identification requires mm and global coordinates",
        )
    try:
        validate_document("marker-input-manifest.schema.json", payload)
    except ContractValidationError as exc:
        raise MarkerIdentificationError("INVALID_MANIFEST", str(exc)) from exc
    return payload, raw


def _marker_payload(record: MarkerRecord) -> dict[str, Any]:
    return {
        "marker_id": record.marker_id,
        "component_id": record.component_id,
        "component_name": record.component_name,
        "solid_index": record.solid_index,
        "marker_type": record.marker_type,
        "center": list(record.center),
        "axis": None if record.axis is None else list(record.axis),
        "bbox": list(record.bbox),
        "dimensions": list(record.dimensions),
        "volume": record.volume,
        "evidence": record.evidence,
        "warnings": list(record.warnings),
    }


def _counts(records: list[MarkerRecord]) -> dict[str, int]:
    types = Counter(record.marker_type for record in records)
    return {
        "marker_count": len(records),
        "cylinder_marker": types["cylinder"],
        "triangular_marker": types["triangular_prism"],
        "unknown_marker": types["unknown"],
    }


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


CSV_FIELDS = (
    "marker_id",
    "component_id",
    "component_name",
    "solid_index",
    "marker_type",
    "center_x",
    "center_y",
    "center_z",
    "axis_x",
    "axis_y",
    "axis_z",
    "bbox_min_x",
    "bbox_min_y",
    "bbox_min_z",
    "bbox_max_x",
    "bbox_max_y",
    "bbox_max_z",
    "size_x",
    "size_y",
    "size_z",
    "volume",
    "face_count",
    "rule",
    "warnings",
)


def _csv_row(record: MarkerRecord) -> dict[str, object]:
    axis: tuple[object, object, object]
    if record.axis is None:
        axis = ("", "", "")
    else:
        axis = record.axis
    return {
        "marker_id": record.marker_id,
        "component_id": record.component_id,
        "component_name": record.component_name,
        "solid_index": record.solid_index,
        "marker_type": record.marker_type,
        "center_x": record.center[0],
        "center_y": record.center[1],
        "center_z": record.center[2],
        "axis_x": axis[0],
        "axis_y": axis[1],
        "axis_z": axis[2],
        "bbox_min_x": record.bbox[0],
        "bbox_min_y": record.bbox[1],
        "bbox_min_z": record.bbox[2],
        "bbox_max_x": record.bbox[3],
        "bbox_max_y": record.bbox[4],
        "bbox_max_z": record.bbox[5],
        "size_x": record.dimensions[0],
        "size_y": record.dimensions[1],
        "size_z": record.dimensions[2],
        "volume": record.volume,
        "face_count": record.evidence["face_count"],
        "rule": record.evidence["rule"],
        "warnings": ";".join(record.warnings),
    }


def _write_csv_atomic(path: Path, records: list[MarkerRecord]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow(_csv_row(record))
    os.replace(temporary, path)


def _write_log_atomic(
    path: Path,
    summary: dict[str, int],
    artifacts: IdentificationArtifacts,
) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    lines = [*PROGRESS_MESSAGES, "", "识别完成"]
    lines.extend(f"{key}={value}" for key, value in summary.items())
    lines.extend(
        (
            f"json={artifacts.json_path}",
            f"csv={artifacts.csv_path}",
            f"log={artifacts.log_path}",
        )
    )
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def identify_weld_markers(
    manifest_path: Path,
    reader: MarkerStepReader,
    emit: Callable[[str], None],
) -> IdentificationArtifacts:
    start = time.perf_counter_ns()
    emit(PROGRESS_MESSAGES[0])
    try:
        occ_version = reader.occ_version
    except (ImportError, OSError, RuntimeError) as exc:
        raise MarkerIdentificationError("RUNTIME_UNAVAILABLE", str(exc)) from exc

    resolved_manifest = manifest_path.resolve()
    manifest, raw_manifest = _read_manifest(resolved_manifest)
    output_dir = resolved_manifest.parent / "marker-identification"
    artifacts = IdentificationArtifacts(
        json_path=output_dir / "weld-markers.json",
        csv_path=output_dir / "weld-markers.csv",
        log_path=output_dir / "identify-weld-markers.log",
    )
    if any(path.exists() for path in (artifacts.json_path, artifacts.csv_path, artifacts.log_path)):
        raise MarkerIdentificationError(
            "OUTPUT_CONFLICT",
            f"marker-identification output already exists: {output_dir}",
        )

    emit(PROGRESS_MESSAGES[1])
    observations_by_component: list[tuple[dict[str, Any], tuple[Any, ...]]] = []
    for component in manifest["components"]:
        step_path = Path(component["step_path"]).resolve()
        if not step_path.is_file() or step_path.stat().st_size == 0:
            raise MarkerIdentificationError(
                "STEP_READ_FAILED",
                f"missing or empty STEP: {step_path}",
            )
        try:
            observations = reader.read(step_path)
        except MarkerStepReadError as exc:
            raise MarkerIdentificationError(exc.code, str(exc)) from exc
        if not observations:
            raise MarkerIdentificationError(
                "EMPTY_IMPORTED_SHAPE",
                f"STEP contains no Solid markers: {step_path}",
            )
        observations_by_component.append((component, observations))

    emit(PROGRESS_MESSAGES[2])
    records: list[MarkerRecord] = []
    try:
        for component, observations in observations_by_component:
            for solid_index, observation in enumerate(observations, start=1):
                records.append(
                    classify_marker(
                        component["id"],
                        component["name"],
                        solid_index,
                        observation,
                    )
                )
    except InvalidMarkerGeometry as exc:
        raise MarkerIdentificationError("INVALID_GEOMETRY", str(exc)) from exc
    records.sort(key=lambda record: (record.component_id, record.solid_index))

    emit(PROGRESS_MESSAGES[3])
    summary = {
        "component_count": len(manifest["components"]),
        **_counts(records),
    }
    component_summaries = []
    for component in sorted(manifest["components"], key=lambda item: item["id"]):
        component_records = [
            record for record in records if record.component_id == component["id"]
        ]
        component_summaries.append(
            {
                "id": component["id"],
                "name": component["name"],
                **_counts(component_records),
            }
        )
    warnings = sorted({warning for record in records for warning in record.warnings})
    payload = {
        "schema_version": "1.0",
        "run_id": manifest["run_id"],
        "status": "success",
        "input": {
            "manifest_path": str(resolved_manifest),
            "manifest_sha256": hashlib.sha256(raw_manifest).hexdigest(),
        },
        "algorithm": {
            "name": "explicit-solid-marker-identification",
            "version": ALGORITHM_VERSION,
            "occ_version": occ_version,
        },
        "hypermesh": manifest["hypermesh"],
        "summary": summary,
        "components": component_summaries,
        "markers": [_marker_payload(record) for record in records],
        "warnings": warnings,
        "elapsed_ms": max(0, (time.perf_counter_ns() - start) // 1_000_000),
    }
    try:
        validate_document("weld-markers.schema.json", payload)
        output_dir.mkdir(parents=True, exist_ok=True)
        _write_json_atomic(artifacts.json_path, payload)
        _write_csv_atomic(artifacts.csv_path, records)
        _write_log_atomic(artifacts.log_path, summary, artifacts)
    except (ContractValidationError, OSError, ValueError) as exc:
        for temporary in output_dir.glob("*.tmp") if output_dir.exists() else ():
            temporary.unlink(missing_ok=True)
        raise MarkerIdentificationError("OUTPUT_WRITE_FAILED", str(exc)) from exc
    return artifacts
