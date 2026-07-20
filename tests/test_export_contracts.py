import copy
from pathlib import Path
import tomllib

import pytest

from weld_agent.contracts import ContractValidationError, load_document, validate_document


FIXTURES = Path(__file__).parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_referencing_is_declared_as_a_direct_dependency() -> None:
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = project["project"]["dependencies"]
    assert any(item.startswith("referencing") for item in dependencies)


def test_valid_export_manifest_passes() -> None:
    payload = load_document(
        FIXTURES / "export_manifest.valid.json",
        "export-manifest.schema.json",
    )
    assert [item["id"] for item in payload["components"]] == [15, 20]
    assert payload["export_options"]["units"] == "Millimeters"


def test_manifest_rejects_duplicate_component_ids() -> None:
    payload = load_document(
        FIXTURES / "export_manifest.valid.json",
        "export-manifest.schema.json",
    )
    payload = copy.deepcopy(payload)
    payload["components"][1]["id"] = payload["components"][0]["id"]
    with pytest.raises(ContractValidationError, match="distinct component IDs"):
        validate_document("export-manifest.schema.json", payload)


def test_manifest_rejects_duplicate_paths() -> None:
    payload = load_document(
        FIXTURES / "export_manifest.valid.json",
        "export-manifest.schema.json",
    )
    payload = copy.deepcopy(payload)
    payload["components"][1]["step_path"] = payload["components"][0]["step_path"]
    with pytest.raises(ContractValidationError, match="distinct STEP paths"):
        validate_document("export-manifest.schema.json", payload)


def test_manifest_rejects_relative_step_path() -> None:
    payload = load_document(
        FIXTURES / "export_manifest.valid.json",
        "export-manifest.schema.json",
    )
    payload = copy.deepcopy(payload)
    payload["components"][0]["step_path"] = "component-15.step"
    with pytest.raises(ContractValidationError, match="must be absolute"):
        validate_document("export-manifest.schema.json", payload)


def test_profile_rejects_negative_bbox_tolerance() -> None:
    payload = load_document(
        FIXTURES / "integration_profile.valid.json",
        "integration-profile.schema.json",
    )
    payload = copy.deepcopy(payload)
    payload["bbox_absolute_tolerance"] = -1
    with pytest.raises(ContractValidationError, match="minimum of 0"):
        validate_document("integration-profile.schema.json", payload)
