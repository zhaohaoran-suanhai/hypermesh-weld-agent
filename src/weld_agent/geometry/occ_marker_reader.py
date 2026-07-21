from __future__ import annotations

from pathlib import Path
from typing import Protocol

from weld_agent.geometry.marker_identification import (
    BBox,
    FaceObservation,
    SolidObservation,
    Vector3,
)


class MarkerStepReadError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class MarkerStepReader(Protocol):
    @property
    def occ_version(self) -> str:
        raise NotImplementedError

    def read(self, path: Path) -> tuple[SolidObservation, ...]:
        raise NotImplementedError


def _xyz(point) -> Vector3:
    return (float(point.X()), float(point.Y()), float(point.Z()))


def _edge_count(shape) -> int:
    from OCC.Core.TopAbs import TopAbs_EDGE
    from OCC.Core.TopExp import TopExp_Explorer

    explorer = TopExp_Explorer(shape, TopAbs_EDGE)
    count = 0
    while explorer.More():
        count += 1
        explorer.Next()
    return count


def _bbox(shape) -> BBox:
    from OCC.Core.BRepBndLib import brepbndlib
    from OCC.Core.Bnd import Bnd_Box

    box = Bnd_Box()
    brepbndlib.AddOptimal(shape, box, False, False)
    try:
        values = box.Get()
    except RuntimeError as exc:
        raise MarkerStepReadError(
            "EMPTY_IMPORTED_SHAPE",
            "OCC returned a void bounding box",
        ) from exc
    return tuple(float(value) for value in values)  # type: ignore[return-value]


def _surface_name(surface_type: int) -> str:
    from OCC.Core.GeomAbs import (
        GeomAbs_BSplineSurface,
        GeomAbs_BezierSurface,
        GeomAbs_Cone,
        GeomAbs_Cylinder,
        GeomAbs_OffsetSurface,
        GeomAbs_OtherSurface,
        GeomAbs_Plane,
        GeomAbs_Sphere,
        GeomAbs_SurfaceOfExtrusion,
        GeomAbs_SurfaceOfRevolution,
        GeomAbs_Torus,
    )

    names = {
        int(GeomAbs_Plane): "plane",
        int(GeomAbs_Cylinder): "cylinder",
        int(GeomAbs_Cone): "cone",
        int(GeomAbs_Sphere): "sphere",
        int(GeomAbs_Torus): "torus",
        int(GeomAbs_BezierSurface): "bezier",
        int(GeomAbs_BSplineSurface): "bspline",
        int(GeomAbs_SurfaceOfRevolution): "revolution",
        int(GeomAbs_SurfaceOfExtrusion): "extrusion",
        int(GeomAbs_OffsetSurface): "offset",
        int(GeomAbs_OtherSurface): "other",
    }
    return names.get(surface_type, f"surface_type_{surface_type}")


def _face_observation(face) -> FaceObservation:
    from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
    from OCC.Core.BRepGProp import brepgprop
    from OCC.Core.GProp import GProp_GProps
    from OCC.Core.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane

    adaptor = BRepAdaptor_Surface(face, True)
    surface_type = int(adaptor.GetType())
    centroid: Vector3 | None = None
    axis: Vector3 | None = None
    if surface_type == int(GeomAbs_Plane):
        properties = GProp_GProps()
        brepgprop.SurfaceProperties(face, properties)
        centroid = _xyz(properties.CentreOfMass())
    elif surface_type == int(GeomAbs_Cylinder):
        direction = adaptor.Cylinder().Axis().Direction()
        axis = _xyz(direction)
    return FaceObservation(
        surface_type=_surface_name(surface_type),
        edge_count=_edge_count(face),
        centroid=centroid,
        axis=axis,
    )


def _solid_observation(solid) -> SolidObservation:
    from OCC.Core.BRepGProp import brepgprop
    from OCC.Core.GProp import GProp_GProps
    from OCC.Core.TopAbs import TopAbs_FACE
    from OCC.Core.TopExp import TopExp_Explorer

    properties = GProp_GProps()
    brepgprop.VolumeProperties(solid, properties)
    faces: list[FaceObservation] = []
    explorer = TopExp_Explorer(solid, TopAbs_FACE)
    while explorer.More():
        faces.append(_face_observation(explorer.Current()))
        explorer.Next()
    return SolidObservation(
        center=_xyz(properties.CentreOfMass()),
        bbox=_bbox(solid),
        volume=float(properties.Mass()),
        faces=tuple(faces),
    )


class PythonOccMarkerReader:
    @property
    def occ_version(self) -> str:
        import OCC

        return str(OCC.VERSION)

    def read(self, path: Path) -> tuple[SolidObservation, ...]:
        if not path.is_file() or path.stat().st_size == 0:
            raise MarkerStepReadError(
                "STEP_READ_FAILED",
                f"missing or empty STEP: {path}",
            )

        from OCC.Core.IFSelect import IFSelect_RetDone
        from OCC.Core.STEPControl import STEPControl_Reader
        from OCC.Core.TopAbs import TopAbs_SOLID
        from OCC.Core.TopExp import TopExp_Explorer

        reader = STEPControl_Reader()
        if reader.ReadFile(str(path)) != IFSelect_RetDone:
            raise MarkerStepReadError(
                "STEP_READ_FAILED",
                f"OCC could not read STEP: {path}",
            )
        if reader.TransferRoots() <= 0:
            raise MarkerStepReadError(
                "STEP_READ_FAILED",
                f"OCC transferred no STEP roots: {path}",
            )
        shape = reader.OneShape()
        if shape.IsNull():
            raise MarkerStepReadError(
                "EMPTY_IMPORTED_SHAPE",
                f"OCC returned a null shape: {path}",
            )

        observations: list[SolidObservation] = []
        explorer = TopExp_Explorer(shape, TopAbs_SOLID)
        while explorer.More():
            observations.append(_solid_observation(explorer.Current()))
            explorer.Next()
        if not observations:
            raise MarkerStepReadError(
                "EMPTY_IMPORTED_SHAPE",
                f"STEP contains no Solid markers: {path}",
            )
        return tuple(observations)
