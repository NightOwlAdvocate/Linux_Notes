"""Result types shared by checks and output formatters."""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


STATUS_ORDER = {"ok": 0, "skip": 0, "warning": 1, "critical": 2}


@dataclass
class CheckResult:
    """One health-check result with a stable machine-readable identifier."""

    check_id: str
    title: str
    status: str
    summary: str
    details: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)
