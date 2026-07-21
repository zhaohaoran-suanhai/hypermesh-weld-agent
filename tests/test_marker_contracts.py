import json
from pathlib import Path

import pytest

from weld_agent.contracts import ContractValidationError, load_document, validate_document


FIXTURES = Path(__file__).parent / "fixtures"


def payload() -> dict:
    return json.loads(
        (FIXTURES / "marker-input-manifest.valid.json").read_text(encoding="utf-8")
    )


def test_marker_manifest_accepts_one_or_more_unique_components() -> None:
    document = load_document(
        FIXTURES / "marker-input-manifest.valid.json",
        "marker-input-manifest.schema.json",
    )
    assert document["run_id"] == "marker-run-001"
    assert [item["id"] for item in document["components"]] == [5, 12]


def test_marker_manifest_rejects_duplicate_component_ids() -> None:
    document = payload()
    document["components"][1]["id"] = 5
    with pytest.raises(ContractValidationError, match="distinct component IDs"):
        validate_document("marker-input-manifest.schema.json", document)


def test_marker_manifest_rejects_relative_step_paths() -> None:
    document = payload()
    document["components"][0]["step_path"] = "component-5.step"
    with pytest.raises(ContractValidationError, match="absolute"):
        validate_document("marker-input-manifest.schema.json", document)


def test_marker_manifest_requires_millimetres() -> None:
    document = payload()
    document["hypermesh"]["units"] = "inch"
    with pytest.raises(ContractValidationError, match="mm"):
        validate_document("marker-input-manifest.schema.json", document)


def test_weld_marker_result_accepts_known_and_unknown_markers() -> None:
    document = {
        "schema_version": "1.0",
        "run_id": "marker-run-001",
        "status": "success",
        "input": {
            "manifest_path": "C:/synthetic/marker-input-manifest.json",
            "manifest_sha256": "a" * 64,
        },
        "algorithm": {
            "name": "explicit-solid-marker-identification",
            "version": "marker-topology-1.0",
            "occ_version": "7.9.0",
        },
        "hypermesh": {
            "build": "HyperMesh 2017",
            "model_name": "synthetic-marker-model",
            "units": "mm",
            "coordinate_system": "global",
        },
        "summary": {
            "component_count": 1,
            "marker_count": 1,
            "cylinder_marker": 0,
            "triangular_marker": 0,
            "unknown_marker": 1,
        },
        "components": [
            {
                "id": 5,
                "name": "MARKERS-A",
                "marker_count": 1,
                "cylinder_marker": 0,
                "triangular_marker": 0,
                "unknown_marker": 1,
            }
        ],
        "markers": [
            {
                "marker_id": "C000005-S000001",
                "component_id": 5,
                "component_name": "MARKERS-A",
                "solid_index": 1,
                "marker_type": "unknown",
                "center": [5, 5, 5],
                "axis": None,
                "bbox": [0, 0, 0, 10, 10, 10],
                "dimensions": [10, 10, 10],
                "volume": 1000,
                "evidence": {
                    "face_count": 6,
                    "surface_types": {"plane": 6},
                    "edge_counts": [4, 4, 4, 4, 4, 4],
                    "rule": "unsupported-topology",
                },
                "warnings": ["UNSUPPORTED_MARKER_TOPOLOGY"],
            }
        ],
        "warnings": [],
        "elapsed_ms": 1,
    }
    validate_document("weld-markers.schema.json", document)
