from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
CAD_SUFFIXES = {".step", ".stp", ".iges", ".igs"}


@dataclass(frozen=True)
class RunWorkspace:
    path: Path

    @classmethod
    def create(cls, run_id: str, root: Path | None = None) -> "RunWorkspace":
        if RUN_ID.fullmatch(run_id) is None:
            raise ValueError("invalid run_id")
        base = root or Path(tempfile.gettempdir()) / "hypermesh-weld-agent"
        base_resolved = base.resolve()
        path = (base_resolved / run_id).resolve()
        if path.parent != base_resolved:
            raise ValueError("run directory escapes workspace root")
        path.mkdir(parents=True, exist_ok=True)
        return cls(path=path)

    def _child(self, name: str) -> Path:
        if not name or Path(name).name != name:
            raise ValueError("artifact name must be a simple file name")
        return self.path / name

    def write_json(self, name: str, payload: dict[str, Any]) -> Path:
        target = self._child(name)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, target)
        return target

    def read_json(self, name: str) -> dict[str, Any]:
        payload = json.loads(self._child(name).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("artifact root must be an object")
        return payload

    def append_event(self, event: str, details: dict[str, Any]) -> Path:
        if not event or any(character.isspace() for character in event):
            raise ValueError("event must be a non-empty token")
        target = self._child("events.jsonl")
        record = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "details": details,
        }
        with target.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        return target

    def cleanup_geometry(self) -> None:
        for path in self.path.iterdir():
            if path.is_file() and path.suffix.lower() in CAD_SUFFIXES:
                path.unlink()
