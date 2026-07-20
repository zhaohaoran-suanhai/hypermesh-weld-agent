from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class ContractValidationError(ValueError):
    """Raised when a workflow document violates its versioned contract."""


SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"


def _schema_path(schema_name: str) -> Path:
    if Path(schema_name).name != schema_name:
        raise ContractValidationError(f"invalid schema name: {schema_name}")
    path = SCHEMA_DIR / schema_name
    if not path.is_file():
        raise ContractValidationError(f"schema not found: {schema_name}")
    return path


def validate_document(schema_name: str, payload: Mapping[str, Any]) -> None:
    schema = json.loads(_schema_path(schema_name).read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(payload),
        key=lambda item: list(item.path),
    )
    if errors:
        first = errors[0]
        location = "$" + "".join(f"[{value!r}]" for value in first.path)
        raise ContractValidationError(f"{location}: {first.message}")
    if schema_name == "selection.schema.json":
        ids = [component["id"] for component in payload["components"]]
        if len(set(ids)) != 2:
            raise ContractValidationError("selection requires two distinct component IDs")


def load_document(path: Path, schema_name: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractValidationError(f"cannot read JSON document {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ContractValidationError("document root must be an object")
    validate_document(schema_name, payload)
    return payload
