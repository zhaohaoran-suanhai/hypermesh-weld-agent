from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import Literal


Vector3 = tuple[float, float, float]
BBox = tuple[float, float, float, float, float, float]
MarkerType = Literal["cylinder", "triangular_prism", "unknown"]


@dataclass(frozen=True)
class FaceObservation:
    surface_type: str
    edge_count: int
    centroid: Vector3 | None
    axis: Vector3 | None


@dataclass(frozen=True)
class SolidObservation:
    center: Vector3
    bbox: BBox
    volume: float
    faces: tuple[FaceObservation, ...]


@dataclass(frozen=True)
class MarkerRecord:
    marker_id: str
    component_id: int
    component_name: str
    solid_index: int
    marker_type: MarkerType
    center: Vector3
    axis: Vector3 | None
    bbox: BBox
    dimensions: Vector3
    volume: float
    evidence: dict[str, object]
    warnings: tuple[str, ...]


class InvalidMarkerGeometry(ValueError):
    """Raised when an observation cannot be represented safely."""


def _is_finite_vector(values: tuple[float, ...]) -> bool:
    return all(math.isfinite(value) for value in values)


def _normalized_axis(vector: Vector3) -> Vector3 | None:
    if not _is_finite_vector(vector):
        raise InvalidMarkerGeometry("axis contains a non-finite value")
    length = math.sqrt(sum(value * value for value in vector))
    if length == 0:
        return None
    normalized = tuple(value / length for value in vector)
    sign_index = max(range(3), key=lambda index: abs(normalized[index]))
    if normalized[sign_index] < 0:
        normalized = tuple(-value for value in normalized)
    return normalized  # type: ignore[return-value]


def _validate_observation(observation: SolidObservation) -> None:
    if len(observation.center) != 3 or not _is_finite_vector(observation.center):
        raise InvalidMarkerGeometry("center must contain three finite values")
    if len(observation.bbox) != 6 or not _is_finite_vector(observation.bbox):
        raise InvalidMarkerGeometry("bbox must contain six finite values")
    if any(observation.bbox[index] > observation.bbox[index + 3] for index in range(3)):
        raise InvalidMarkerGeometry("bbox lower bound exceeds upper bound")
    if not math.isfinite(observation.volume) or observation.volume < 0:
        raise InvalidMarkerGeometry("volume must be finite and non-negative")


def _evidence(observation: SolidObservation, rule: str) -> dict[str, object]:
    surface_types = Counter(face.surface_type for face in observation.faces)
    return {
        "face_count": len(observation.faces),
        "surface_types": dict(sorted(surface_types.items())),
        "edge_counts": sorted(face.edge_count for face in observation.faces),
        "rule": rule,
    }


def _triangle_axis(observation: SolidObservation) -> Vector3 | None:
    triangular_faces = [
        face
        for face in observation.faces
        if face.surface_type == "plane" and face.edge_count == 3
    ]
    if len(triangular_faces) != 2:
        return None
    first = triangular_faces[0].centroid
    second = triangular_faces[1].centroid
    if first is None or second is None:
        return None
    if not _is_finite_vector(first) or not _is_finite_vector(second):
        raise InvalidMarkerGeometry("triangular end centroid is non-finite")
    return _normalized_axis(
        (
            second[0] - first[0],
            second[1] - first[1],
            second[2] - first[2],
        )
    )


def classify_marker(
    component_id: int,
    component_name: str,
    solid_index: int,
    observation: SolidObservation,
) -> MarkerRecord:
    _validate_observation(observation)
    if component_id < 1:
        raise ValueError("component_id must be positive")
    if solid_index < 1:
        raise ValueError("solid_index must be positive")
    if not component_name:
        raise ValueError("component_name must not be empty")

    marker_type: MarkerType = "unknown"
    axis: Vector3 | None = None
    warnings: tuple[str, ...] = ("UNSUPPORTED_MARKER_TOPOLOGY",)
    rule = "unsupported-topology"

    cylindrical_faces = [
        face for face in observation.faces if face.surface_type == "cylinder"
    ]
    planar_faces = [
        face for face in observation.faces if face.surface_type == "plane"
    ]
    if cylindrical_faces and len(planar_faces) == 2:
        candidate_axes = [face.axis for face in cylindrical_faces if face.axis is not None]
        for candidate in candidate_axes:
            axis = _normalized_axis(candidate)
            if axis is not None:
                break
        if axis is None:
            warnings = ("ZERO_LENGTH_AXIS",)
            rule = "cylinder-axis-invalid"
        else:
            marker_type = "cylinder"
            warnings = ()
            rule = "cylinder-surfaces"
    elif len(observation.faces) == 5 and len(planar_faces) == 5:
        axis = _triangle_axis(observation)
        if axis is None:
            triangular_count = sum(face.edge_count == 3 for face in planar_faces)
            if triangular_count == 2:
                warnings = ("ZERO_LENGTH_AXIS",)
                rule = "triangular-prism-axis-invalid"
        else:
            marker_type = "triangular_prism"
            warnings = ()
            rule = "triangular-prism-planes"

    dimensions: Vector3 = (
        observation.bbox[3] - observation.bbox[0],
        observation.bbox[4] - observation.bbox[1],
        observation.bbox[5] - observation.bbox[2],
    )
    return MarkerRecord(
        marker_id=f"C{component_id:06d}-S{solid_index:06d}",
        component_id=component_id,
        component_name=component_name,
        solid_index=solid_index,
        marker_type=marker_type,
        center=observation.center,
        axis=axis,
        bbox=observation.bbox,
        dimensions=dimensions,
        volume=observation.volume,
        evidence=_evidence(observation, rule),
        warnings=warnings,
    )
