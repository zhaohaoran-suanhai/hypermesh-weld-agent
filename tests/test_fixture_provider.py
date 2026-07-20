import json
from pathlib import Path

from weld_agent.contracts import validate_document
from weld_agent.providers.fixture import FixtureCandidateProvider


FIXTURE = Path(__file__).parent / "fixtures" / "selection.valid.json"


def test_fixture_provider_marks_output_as_test_only() -> None:
    selection = json.loads(FIXTURE.read_text(encoding="utf-8"))
    result = FixtureCandidateProvider().analyze(selection)
    validate_document("weld-candidates.schema.json", result)
    assert result["provider"] == "fixture-test-only"
    assert result["parameters"] == selection["parameters"]
    assert result["elapsed_ms"] == 0
    assert result["has_candidate_regions"] is True
    assert result["regions"][0]["risk_flags"] == ["TEST_PROVIDER_ONLY"]
    assert result["regions"][0]["candidates"][0]["status"] == "pending_review"


def test_fixture_provider_reports_non_overlapping_bounding_boxes() -> None:
    selection = json.loads(FIXTURE.read_text(encoding="utf-8"))
    selection["components"][1]["summary"]["bbox"] = [200, 200, 200, 210, 210, 210]
    result = FixtureCandidateProvider().analyze(selection)
    validate_document("weld-candidates.schema.json", result)
    assert result["status"] == "failure"
    assert result["has_candidate_regions"] is False
    assert result["errors"][0]["code"] == "NO_PROXIMITY"
