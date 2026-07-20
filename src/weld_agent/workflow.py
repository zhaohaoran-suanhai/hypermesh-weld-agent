from pathlib import Path

from weld_agent.contracts import load_document, validate_document
from weld_agent.providers.base import CandidateProvider
from weld_agent.run_workspace import RunWorkspace


def run_analysis(
    selection_path: Path,
    output_root: Path,
    provider: CandidateProvider,
) -> Path:
    selection = load_document(selection_path, "selection.schema.json")
    workspace = RunWorkspace.create(selection["run_id"], root=output_root)
    result = provider.analyze(selection)
    validate_document("weld-candidates.schema.json", result)
    output = workspace.write_json("weld_candidates.json", result)
    workspace.append_event(
        "analysis_completed",
        {
            "status": result["status"],
            "provider": result["provider"],
            "output": output.name,
        },
    )
    return output
