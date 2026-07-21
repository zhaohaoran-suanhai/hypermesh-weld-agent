from pathlib import Path

import pytest

from weld_agent.geometry.marker_identification import classify_marker
from weld_agent.geometry.occ_marker_reader import (
    MarkerStepReadError,
    PythonOccMarkerReader,
)


def write_step(path: Path, shape) -> Path:
    from OCC.Core.IFSelect import IFSelect_RetDone
    from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer

    writer = STEPControl_Writer()
    assert writer.Transfer(shape, STEPControl_AsIs) == IFSelect_RetDone
    assert writer.Write(str(path)) == IFSelect_RetDone
    return path


def make_triangular_prism():
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
    from OCC.Core.gp import gp_Pnt, gp_Vec

    polygon = BRepBuilderAPI_MakePolygon()
    polygon.Add(gp_Pnt(0, 0, 0))
    polygon.Add(gp_Pnt(6, 0, 0))
    polygon.Add(gp_Pnt(3, 4, 0))
    polygon.Close()
    face = BRepBuilderAPI_MakeFace(polygon.Wire()).Face()
    return BRepPrimAPI_MakePrism(face, gp_Vec(0, 0, 6)).Shape()


def test_missing_step_is_classified(tmp_path: Path) -> None:
    with pytest.raises(MarkerStepReadError) as caught:
        PythonOccMarkerReader().read(tmp_path / "missing.step")
    assert caught.value.code == "STEP_READ_FAILED"


def test_invalid_step_is_classified(tmp_path: Path) -> None:
    path = tmp_path / "invalid.step"
    path.write_text("not a STEP file", encoding="utf-8")
    with pytest.raises(MarkerStepReadError) as caught:
        PythonOccMarkerReader().read(path)
    assert caught.value.code == "STEP_READ_FAILED"


@pytest.mark.occ_integration
def test_reader_extracts_cylinder_observation(tmp_path: Path) -> None:
    pytest.importorskip("OCC", reason="PythonOCC runtime is not installed")
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder

    path = write_step(
        tmp_path / "cylinder.step",
        BRepPrimAPI_MakeCylinder(3, 6).Shape(),
    )
    reader = PythonOccMarkerReader()
    observations = reader.read(path)
    assert reader.occ_version == "7.9.0"
    assert len(observations) == 1
    assert any(face.surface_type == "cylinder" for face in observations[0].faces)
    assert classify_marker(5, "MARKERS", 1, observations[0]).marker_type == "cylinder"


@pytest.mark.occ_integration
def test_reader_extracts_triangular_prism_observation(tmp_path: Path) -> None:
    pytest.importorskip("OCC", reason="PythonOCC runtime is not installed")
    path = write_step(tmp_path / "triangle.step", make_triangular_prism())
    observation = PythonOccMarkerReader().read(path)[0]
    assert classify_marker(12, "MARKERS", 1, observation).marker_type == "triangular_prism"


@pytest.mark.occ_integration
def test_reader_keeps_box_as_unknown(tmp_path: Path) -> None:
    pytest.importorskip("OCC", reason="PythonOCC runtime is not installed")
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox

    path = write_step(tmp_path / "box.step", BRepPrimAPI_MakeBox(6, 6, 6).Shape())
    observation = PythonOccMarkerReader().read(path)[0]
    assert classify_marker(12, "MARKERS", 1, observation).marker_type == "unknown"


@pytest.mark.occ_integration
def test_reader_rejects_step_without_solids(tmp_path: Path) -> None:
    pytest.importorskip("OCC", reason="PythonOCC runtime is not installed")
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
    from OCC.Core.gp import gp_Pnt

    edge = BRepBuilderAPI_MakeEdge(gp_Pnt(0, 0, 0), gp_Pnt(1, 0, 0)).Edge()
    path = write_step(tmp_path / "edge.step", edge)
    with pytest.raises(MarkerStepReadError) as caught:
        PythonOccMarkerReader().read(path)
    assert caught.value.code == "EMPTY_IMPORTED_SHAPE"
