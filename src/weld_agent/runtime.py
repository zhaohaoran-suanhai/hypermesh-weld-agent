from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


PROBE_CODE = """
import json
import platform
import OCC
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
print(json.dumps({"python": platform.python_version(), "occ": OCC.VERSION}))
""".strip()


@dataclass(frozen=True)
class RuntimeProbe:
    available: bool
    executable: str
    python_version: str | None = None
    occ_version: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def probe_pythonocc(executable: Path) -> RuntimeProbe:
    try:
        completed = subprocess.run(
            [str(executable), "-c", PROBE_CODE],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return RuntimeProbe(False, str(executable), error=str(exc))
    if completed.returncode != 0:
        return RuntimeProbe(
            False,
            str(executable),
            error=completed.stderr.strip() or "probe failed",
        )
    try:
        payload = json.loads(completed.stdout)
        return RuntimeProbe(
            True,
            str(executable),
            payload["python"],
            payload["occ"],
        )
    except (json.JSONDecodeError, KeyError) as exc:
        return RuntimeProbe(False, str(executable), error=f"invalid probe output: {exc}")
