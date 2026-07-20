import json
from pathlib import Path

import pytest

from weld_agent.contracts import ContractValidationError, load_document, validate_document


FIXTURES = Path(__file__).parent / "fixtures"


def test_valid_selection_fixture_passes() -> None:
    payload = load_document(FIXTURES / "selection.valid.json", "selection.schema.json")
    assert payload["run_id"] == "run-001"
    assert payload["hypermesh"]["coordinate_system"] == "global"
    assert [item["id"] for item in payload["components"]] == [9, 12]


def test_duplicate_component_ids_are_rejected() -> None:
    payload = json.loads((FIXTURES / "selection.valid.json").read_text(encoding="utf-8"))
    payload["components"][1]["id"] = payload["components"][0]["id"]
    with pytest.raises(ContractValidationError, match="distinct component IDs"):
        validate_document("selection.schema.json", payload)


def test_missing_units_are_rejected() -> None:
    payload = json.loads((FIXTURES / "selection.valid.json").read_text(encoding="utf-8"))
    del payload["hypermesh"]["units"]
    with pytest.raises(ContractValidationError, match="units"):
        validate_document("selection.schema.json", payload)


def test_candidate_failure_requires_a_structured_error() -> None:
    payload = {
        "schema_version": "1.0",
        "run_id": "run-001",
        "status": "failure",
        "has_candidate_regions": False,
        "provider": "test",
        "algorithm_version": "test-1",
        "component_refs": [9, 12],
        "parameters": {
            "search_distance": 5,
            "max_gap": 2,
            "pitch": 40,
            "end_offset": 20,
            "edge_clearance": 10,
            "rule_profile_version": "review-only-1",
        },
        "elapsed_ms": 0,
        "regions": [],
        "warnings": [],
        "errors": [],
    }
    with pytest.raises(ContractValidationError, match="non-empty"):
        validate_document("weld-candidates.schema.json", payload)
