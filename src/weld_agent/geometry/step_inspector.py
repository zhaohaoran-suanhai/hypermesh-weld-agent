from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


BBox = tuple[float, float, float, float, float, float]


@dataclass(frozen=True)
class StepInspection:
    face_count: int
    solid_count: int
    bbox: BBox


class StepInspectionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class StepInspector(Protocol):
    def inspect(self, path: Path) -> StepInspection:
        raise NotImplementedError


def _count(shape: Any, topology_type: int) -> int:
    from OCC.Core.TopExp import TopExp_Explorer

    explorer = TopExp_Explorer(shape, topology_type)
    count = 0
    while explorer.More():
        count += 1
        explorer.Next()
    return count


class PythonOccStepInspector:
    def inspect(self, path: Path) -> StepInspection:
        if not path.is_file() or path.stat().st_size == 0:
            raise StepInspectionError(
                "STEP_READ_FAILED",
                f"missing or empty STEP: {path}",
            )

        from OCC.Core.Bnd import Bnd_Box
        from OCC.Core.BRepBndLib import brepbndlib
        from OCC.Core.IFSelect import IFSelect_RetDone
        from OCC.Core.STEPControl import STEPControl_Reader
        from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_SOLID

        reader = STEPControl_Reader()
        if reader.ReadFile(str(path)) != IFSelect_RetDone:
            raise StepInspectionError(
                "STEP_READ_FAILED",
                f"OCC could not read STEP: {path}",
            )
        if reader.TransferRoots() <= 0:
            raise StepInspectionError(
                "STEP_READ_FAILED",
                f"OCC transferred no STEP roots: {path}",
            )
        shape = reader.OneShape()
        if shape.IsNull():
            raise StepInspectionError(
                "EMPTY_IMPORTED_SHAPE",
                f"OCC returned a null shape: {path}",
            )

        box = Bnd_Box()
        brepbndlib.Add(shape, box)
        try:
            raw_bbox = box.Get()
        except RuntimeError as exc:
            raise StepInspectionError(
                "EMPTY_IMPORTED_SHAPE",
                f"OCC returned a void bounding box: {path}",
            ) from exc
        bbox = tuple(float(value) for value in raw_bbox)
        if len(bbox) != 6 or not all(math.isfinite(value) for value in bbox):
            raise StepInspectionError(
                "EXPORT_MISMATCH",
                f"non-finite OCC bbox: {path}",
            )

        face_count = _count(shape, TopAbs_FACE)
        solid_count = _count(shape, TopAbs_SOLID)
        if face_count == 0 and solid_count == 0:
            raise StepInspectionError(
                "EMPTY_IMPORTED_SHAPE",
                f"STEP has no faces or solids: {path}",
            )
        return StepInspection(face_count, solid_count, bbox)  # type: ignore[arg-type]
