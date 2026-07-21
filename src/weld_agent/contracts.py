from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


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


def _schema_registry() -> Registry:
    resources = []
    for path in SCHEMA_DIR.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


def _is_absolute_any_platform(value: str) -> bool:
    return PureWindowsPath(value).is_absolute() or PurePosixPath(value).is_absolute()


def _validate_two_component_identity(
    payload: Mapping[str, Any],
    *,
    document_name: str,
    path_key: str | None,
) -> None:
    components = payload["components"]
    ids = [component["id"] for component in components]
    if len(set(ids)) != 2:
        raise ContractValidationError(
            f"{document_name} requires two distinct component IDs"
        )
    if path_key is None:
        return
    paths = [component[path_key] for component in components]
    if len(set(paths)) != 2:
        raise ContractValidationError("manifest requires two distinct STEP paths")
    if not all(_is_absolute_any_platform(value) for value in paths):
        raise ContractValidationError("manifest STEP paths must be absolute")


def _validate_marker_component_identity(payload: Mapping[str, Any]) -> None:
    components = payload["components"]
    ids = [component["id"] for component in components]
    if len(set(ids)) != len(ids):
        raise ContractValidationError(
            "marker manifest requires distinct component IDs"
        )
    paths = [component["step_path"] for component in components]
    if len(set(paths)) != len(paths):
        raise ContractValidationError(
            "marker manifest requires distinct STEP paths"
        )
    if not all(_is_absolute_any_platform(value) for value in paths):
        raise ContractValidationError(
            "marker manifest STEP paths must be absolute"
        )


def validate_document(schema_name: str, payload: Mapping[str, Any]) -> None:
    schema = json.loads(_schema_path(schema_name).read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema, registry=_schema_registry()).iter_errors(payload),
        key=lambda item: list(item.path),
    )
    if errors:
        first = errors[0]
        location = "$" + "".join(f"[{value!r}]" for value in first.path)
        raise ContractValidationError(f"{location}: {first.message}")
    if schema_name == "selection.schema.json":
        _validate_two_component_identity(
            payload,
            document_name="selection",
            path_key=None,
        )
    if schema_name == "export-manifest.schema.json":
        _validate_two_component_identity(
            payload,
            document_name="manifest",
            path_key="step_path",
        )
    if schema_name == "marker-input-manifest.schema.json":
        _validate_marker_component_identity(payload)


def load_document(path: Path, schema_name: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractValidationError(f"cannot read JSON document {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ContractValidationError("document root must be an object")
    validate_document(schema_name, payload)
    return payload
