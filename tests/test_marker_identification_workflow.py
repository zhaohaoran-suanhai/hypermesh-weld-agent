import csv
import hashlib
import json
import math
from dataclasses import replace
from pathlib import Path

import pytest

from weld_agent.geometry.marker_identification import FaceObservation, SolidObservation
from weld_agent.marker_identification import (
    MarkerIdentificationError,
    identify_weld_markers,
)


def cylinder_observation() -> SolidObservation:
    return SolidObservation(
        center=(0.0, 0.0, 3.0),
        bbox=(-3.0, -3.0, 0.0, 3.0, 3.0, 6.0),
        volume=169.646,
        faces=(
            FaceObservation("cylinder", 4, None, (0.0, 0.0, 1.0)),
            FaceObservation("plane", 2, (0.0, 0.0, 0.0), None),
            FaceObservation("plane", 2, (0.0, 0.0, 6.0), None),
        ),
    )


def triangular_observation() -> SolidObservation:
    return SolidObservation(
        center=(22.0, 2.0, 3.0),
        bbox=(20.0, 0.0, 0.0, 24.0, 4.0, 6.0),
        volume=48.0,
        faces=(
            FaceObservation("plane", 3, (22.0, 1.0, 0.0), None),
            FaceObservation("plane", 3, (22.0, 1.0, 6.0), None),
            FaceObservation("plane", 4, None, None),
            FaceObservation("plane", 4, None, None),
            FaceObservation("plane", 4, None, None),
        ),
    )


class FakeReader:
    occ_version = "7.9-test"

    def __init__(self, observations: dict[str, tuple[SolidObservation, ...]]) -> None:
        self.observations = observations

    def read(self, path: Path) -> tuple[SolidObservation, ...]:
        return self.observations[path.name]


def write_manifest(tmp_path: Path, *, units: str = "mm") -> Path:
    component_5 = tmp_path / "component-5.step"
    component_12 = tmp_path / "component-12.step"
    component_5.write_bytes(b"STEP-A")
    component_12.write_bytes(b"STEP-B")
    manifest = tmp_path / "marker-input-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "run_id": "marker-workflow-001",
                "hypermesh": {
                    "build": "HyperMesh 2017",
                    "model_name": "synthetic-marker-model",
                    "units": units,
                    "coordinate_system": "global",
                },
                "components": [
                    {
                        "id": 12,
                        "name": "MARKERS-B",
                        "step_path": str(component_12.resolve()),
                        "summary": {
                            "surface_count": 5,
                            "solid_count": 1,
                            "element_count": 0,
                            "bbox": [20, 0, 0, 24, 4, 6],
                        },
                    },
                    {
                        "id": 5,
                        "name": "MARKERS-A",
                        "step_path": str(component_5.resolve()),
                        "summary": {
                            "surface_count": 3,
                            "solid_count": 1,
                            "element_count": 0,
                            "bbox": [-3, -3, 0, 3, 3, 6],
                        },
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def fake_reader() -> FakeReader:
    return FakeReader(
        {
            "component-5.step": (cylinder_observation(),),
            "component-12.step": (triangular_observation(),),
        }
    )


def test_identification_writes_deterministic_auditable_artifacts(tmp_path: Path) -> None:
    manifest = write_manifest(tmp_path)
    messages: list[str] = []
    artifacts = identify_weld_markers(manifest, fake_reader(), messages.append)
    payload = json.loads(artifacts.json_path.read_text(encoding="utf-8"))
    with artifacts.csv_path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))

    assert messages == [
        "[1/4] 检查 PythonOCC 运行环境",
        "[2/4] 读取焊点 Component STEP",
        "[3/4] 识别焊点标记",
        "[4/4] 写入识别结果",
    ]
    assert [item["marker_id"] for item in payload["markers"]] == [
        "C000005-S000001",
        "C000012-S000001",
    ]
    assert payload["summary"] == {
        "component_count": 2,
        "marker_count": 2,
        "cylinder_marker": 1,
        "triangular_marker": 1,
        "unknown_marker": 0,
    }
    assert len(rows) == payload["summary"]["marker_count"] == 2
    assert payload["input"]["manifest_sha256"] == hashlib.sha256(
        manifest.read_bytes()
    ).hexdigest()
    assert artifacts.json_path.parent.name == "marker-identification"
    assert artifacts.log_path.read_text(encoding="utf-8").startswith("[1/4]")
    assert not list(artifacts.json_path.parent.glob("*.tmp"))


def test_existing_output_is_a_classified_conflict(tmp_path: Path) -> None:
    manifest = write_manifest(tmp_path)
    identify_weld_markers(manifest, fake_reader(), lambda message: None)
    with pytest.raises(MarkerIdentificationError) as caught:
        identify_weld_markers(manifest, fake_reader(), lambda message: None)
    assert caught.value.code == "OUTPUT_CONFLICT"


def test_missing_step_is_classified(tmp_path: Path) -> None:
    manifest = write_manifest(tmp_path)
    (tmp_path / "component-5.step").unlink()
    with pytest.raises(MarkerIdentificationError) as caught:
        identify_weld_markers(manifest, fake_reader(), lambda message: None)
    assert caught.value.code == "STEP_READ_FAILED"


def test_non_mm_manifest_is_classified(tmp_path: Path) -> None:
    manifest = write_manifest(tmp_path, units="inch")
    with pytest.raises(MarkerIdentificationError) as caught:
        identify_weld_markers(manifest, fake_reader(), lambda message: None)
    assert caught.value.code == "UNIT_MISMATCH"


def test_empty_component_is_classified(tmp_path: Path) -> None:
    manifest = write_manifest(tmp_path)
    reader = FakeReader({"component-5.step": (), "component-12.step": ()})
    with pytest.raises(MarkerIdentificationError) as caught:
        identify_weld_markers(manifest, reader, lambda message: None)
    assert caught.value.code == "EMPTY_IMPORTED_SHAPE"


def test_invalid_solid_geometry_is_classified(tmp_path: Path) -> None:
    manifest = write_manifest(tmp_path)
    invalid = replace(cylinder_observation(), center=(math.nan, 0.0, 0.0))
    reader = FakeReader(
        {
            "component-5.step": (invalid,),
            "component-12.step": (triangular_observation(),),
        }
    )
    with pytest.raises(MarkerIdentificationError) as caught:
        identify_weld_markers(manifest, reader, lambda message: None)
    assert caught.value.code == "INVALID_GEOMETRY"
