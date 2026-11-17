"""
Result and finding models for VeilForge.
"""

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from veilforge.core.models.message import Message


class TurnResult(BaseModel):
    """Result of a single turn in a multi-turn probe."""

    turn_id: str
    user_message: Message
    assistant_message: Message | None = None
    response_text: str = ""
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    latency_seconds: float | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Finding(BaseModel):
    """A detected vulnerability finding from a probe."""

    probe_id: str
    probe_name: str | None = None
    category: str
    severity: Literal["low", "medium", "high", "critical"]
    attack_succeeded: bool
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    reason: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    owasp_llm: list[str] = Field(default_factory=list)
    nist_rmf: list[str] = Field(default_factory=list)
    turn_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProbeResult(BaseModel):
    """Aggregated result of running a probe against a target."""

    probe_id: str
    probe_name: str
    category: str
    severity: Literal["low", "medium", "high", "critical"]
    turns: list[TurnResult] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    success_count: int = 0
    error: str | None = None
    artifacts: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def attack_succeeded(self) -> bool:
        """True if any finding indicates a successful attack."""
        if self.error:
            return False
        return any(f.attack_succeeded for f in self.findings) or self.success_count > 0


class CampaignResult(BaseModel):
    """Aggregated result of a full campaign run."""

    campaign_id: str | None = None
    target: str
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    results: list[ProbeResult] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def succeeded(self) -> int:
        return sum(1 for r in self.results if r.attack_succeeded)

    @property
    def errors(self) -> int:
        return sum(1 for r in self.results if r.error)

    def by_severity(self) -> dict[str, int]:
        """Count successful attacks per severity level."""
        counts: dict[str, int] = {}
        for r in self.results:
            if r.attack_succeeded:
                counts[r.severity] = counts.get(r.severity, 0) + 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        """Plain-dictionary version, easy to save as JSON."""
        return self.model_dump()
