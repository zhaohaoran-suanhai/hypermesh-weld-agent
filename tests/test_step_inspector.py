import math
from pathlib import Path

import pytest

from weld_agent.geometry.step_inspector import PythonOccStepInspector, StepInspectionError


def test_missing_step_is_classified(tmp_path: Path) -> None:
    with pytest.raises(StepInspectionError) as caught:
        PythonOccStepInspector().inspect(tmp_path / "missing.step")
    assert caught.value.code == "STEP_READ_FAILED"


def test_invalid_step_is_classified(tmp_path: Path) -> None:
    path = tmp_path / "invalid.step"
    path.write_text("not a STEP file", encoding="utf-8")
    with pytest.raises(StepInspectionError) as caught:
        PythonOccStepInspector().inspect(path)
    assert caught.value.code == "STEP_READ_FAILED"


@pytest.mark.occ_integration
def test_occ_reads_a_generated_box(tmp_path: Path) -> None:
    pytest.importorskip("OCC", reason="PythonOCC runtime is not installed")
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
    from OCC.Core.IFSelect import IFSelect_RetDone
    from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer

    path = tmp_path / "box.step"
    writer = STEPControl_Writer()
    assert (
        writer.Transfer(BRepPrimAPI_MakeBox(10, 20, 30).Shape(), STEPControl_AsIs)
        == IFSelect_RetDone
    )
    assert writer.Write(str(path)) == IFSelect_RetDone

    result = PythonOccStepInspector().inspect(path)
    assert result.face_count == 6
    assert result.solid_count == 1
    assert all(math.isfinite(value) for value in result.bbox)
    assert result.bbox == pytest.approx((0, 0, 0, 10, 20, 30), abs=1e-5)


@pytest.mark.occ_integration
def test_occ_uses_an_optimal_bbox_for_curved_geometry(tmp_path: Path) -> None:
    pytest.importorskip("OCC", reason="PythonOCC runtime is not installed")
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeSphere
    from OCC.Core.IFSelect import IFSelect_RetDone
    from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer

    path = tmp_path / "sphere.step"
    writer = STEPControl_Writer()
    assert (
        writer.Transfer(BRepPrimAPI_MakeSphere(10).Shape(), STEPControl_AsIs)
        == IFSelect_RetDone
    )
    assert writer.Write(str(path)) == IFSelect_RetDone

    result = PythonOccStepInspector().inspect(path)
    assert result.bbox == pytest.approx((-10, -10, -10, 10, 10, 10), abs=1e-9)
