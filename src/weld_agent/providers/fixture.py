from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _intersection_center(first: list[float], second: list[float]) -> list[float] | None:
    lower = [max(first[index], second[index]) for index in range(3)]
    upper = [min(first[index + 3], second[index + 3]) for index in range(3)]
    if any(low > high for low, high in zip(lower, upper, strict=True)):
        return None
    return [(low + high) / 2.0 for low, high in zip(lower, upper, strict=True)]


class FixtureCandidateProvider:
    """Deterministic plumbing provider; it is not a weld-recognition algorithm."""

    def analyze(self, selection: Mapping[str, Any]) -> dict[str, Any]:
        component_ids = [item["id"] for item in selection["components"]]
        center = _intersection_center(
            selection["components"][0]["summary"]["bbox"],
            selection["components"][1]["summary"]["bbox"],
        )
        base = {
            "schema_version": "1.0",
            "run_id": selection["run_id"],
            "provider": "fixture-test-only",
            "algorithm_version": "fixture-1",
            "component_refs": component_ids,
            "parameters": dict(selection["parameters"]),
            "elapsed_ms": 0,
        }
        if center is None:
            return {
                **base,
                "status": "failure",
                "has_candidate_regions": False,
                "regions": [],
                "warnings": [],
                "errors": [
                    {
                        "code": "NO_PROXIMITY",
                        "message": "fixture bounding boxes do not overlap",
                    }
                ],
            }
        return {
            **base,
            "status": "success",
            "has_candidate_regions": True,
            "regions": [
                {
                    "id": "fixture-region-1",
                    "risk_flags": ["TEST_PROVIDER_ONLY"],
                    "candidates": [
                        {
                            "id": "fixture-candidate-1",
                            "position": center,
                            "direction": [0.0, 0.0, 1.0],
                            "component_refs": component_ids,
                            "confidence": 0.0,
                            "evidence": {"source": "bounding-box-intersection-center"},
                            "status": "pending_review",
                        }
                    ],
                }
            ],
            "warnings": ["TEST_PROVIDER_ONLY: result is not a real weld analysis"],
            "errors": [],
        }
