from pathlib import Path

from weld_agent.contracts import load_document


def test_hypermesh_probe_fixture_passes() -> None:
    path = Path(__file__).parent / "fixtures" / "hypermesh_probe.valid.json"
    payload = load_document(path, "hypermesh-probe.schema.json")
    assert len(payload["selected_components"]) == 2
    assert isinstance(payload["capabilities"]["geomexport"], bool)
