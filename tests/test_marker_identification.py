import math
from dataclasses import replace

import pytest

from weld_agent.geometry.marker_identification import (
    FaceObservation,
    InvalidMarkerGeometry,
    SolidObservation,
    classify_marker,
)


def cylinder_observation() -> SolidObservation:
    return SolidObservation(
        center=(0.0, 0.0, 3.0),
        bbox=(-3.0, -3.0, 0.0, 3.0, 3.0, 6.0),
        volume=169.646,
        faces=(
            FaceObservation("cylinder", 4, None, (0.0, 0.0, -1.0)),
            FaceObservation("cylinder", 4, None, (0.0, 0.0, -1.0)),
            FaceObservation("plane", 2, (0.0, 0.0, 0.0), None),
            FaceObservation("plane", 2, (0.0, 0.0, 6.0), None),
        ),
    )


def triangular_observation() -> SolidObservation:
    return SolidObservation(
        center=(2.0, 2.0, 3.0),
        bbox=(0.0, 0.0, 0.0, 4.0, 4.0, 6.0),
        volume=48.0,
        faces=(
            FaceObservation("plane", 3, (2.0, 1.0, 0.0), None),
            FaceObservation("plane", 3, (2.0, 1.0, 6.0), None),
            FaceObservation("plane", 4, (2.0, 0.0, 3.0), None),
            FaceObservation("plane", 4, (3.0, 2.0, 3.0), None),
            FaceObservation("plane", 4, (1.0, 2.0, 3.0), None),
        ),
    )


def box_observation() -> SolidObservation:
    return SolidObservation(
        center=(3.0, 3.0, 3.0),
        bbox=(0.0, 0.0, 0.0, 6.0, 6.0, 6.0),
        volume=216.0,
        faces=tuple(
            FaceObservation("plane", 4, None, None) for _ in range(6)
        ),
    )


def zero_axis_triangle() -> SolidObservation:
    observation = triangular_observation()
    faces = list(observation.faces)
    faces[1] = replace(faces[1], centroid=faces[0].centroid)
    return replace(observation, faces=tuple(faces))


def test_split_cylinder_faces_are_classified_as_cylinder() -> None:
    result = classify_marker(5, "MARKERS", 1, cylinder_observation())
    assert result.marker_id == "C000005-S000001"
    assert result.marker_type == "cylinder"
    assert result.axis == pytest.approx((0.0, 0.0, 1.0))
    assert result.dimensions == pytest.approx((6.0, 6.0, 6.0))
    assert result.evidence["surface_types"] == {"cylinder": 2, "plane": 2}


def test_five_plane_triangular_prism_is_classified() -> None:
    result = classify_marker(12, "MARKERS", 3, triangular_observation())
    assert result.marker_id == "C000012-S000003"
    assert result.marker_type == "triangular_prism"
    assert result.axis == pytest.approx((0.0, 0.0, 1.0))
    assert result.evidence["edge_counts"] == [3, 3, 4, 4, 4]


def test_box_is_unknown_and_preserves_topology_evidence() -> None:
    result = classify_marker(12, "MARKERS", 4, box_observation())
    assert result.marker_type == "unknown"
    assert result.axis is None
    assert result.evidence["face_count"] == 6
    assert result.warnings == ("UNSUPPORTED_MARKER_TOPOLOGY",)


def test_non_finite_center_is_invalid_geometry() -> None:
    observation = replace(cylinder_observation(), center=(math.nan, 0.0, 0.0))
    with pytest.raises(InvalidMarkerGeometry, match="center"):
        classify_marker(5, "MARKERS", 1, observation)


def test_reversed_bbox_is_invalid_geometry() -> None:
    observation = replace(cylinder_observation(), bbox=(3, -3, 0, -3, 3, 6))
    with pytest.raises(InvalidMarkerGeometry, match="bbox"):
        classify_marker(5, "MARKERS", 1, observation)


def test_zero_length_triangle_axis_is_unknown() -> None:
    result = classify_marker(12, "MARKERS", 1, zero_axis_triangle())
    assert result.marker_type == "unknown"
    assert result.axis is None
    assert "ZERO_LENGTH_AXIS" in result.warnings
