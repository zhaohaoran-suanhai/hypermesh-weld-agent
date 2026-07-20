from collections.abc import Mapping
from typing import Any, Protocol


class CandidateProvider(Protocol):
    def analyze(self, selection: Mapping[str, Any]) -> dict[str, Any]: ...
