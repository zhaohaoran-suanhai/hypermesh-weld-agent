import json
from pathlib import Path

from weld_agent.cli import main


FIXTURE = Path(__file__).parent / "fixtures" / "selection.valid.json"


def test_analyze_command_writes_valid_candidate_file(tmp_path: Path) -> None:
    exit_code = main(
        [
            "analyze",
            "--selection",
            str(FIXTURE),
            "--output-root",
            str(tmp_path),
            "--provider",
            "fixture",
        ]
    )
    assert exit_code == 0
    output = tmp_path / "run-001" / "weld_candidates.json"
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["provider"] == "fixture-test-only"
    events = (output.parent / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(events[-1])["event"] == "analysis_completed"


def test_validate_command_rejects_wrong_schema(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{}", encoding="utf-8")
    assert main(["validate", "--schema", "selection.schema.json", "--input", str(invalid)]) == 2
