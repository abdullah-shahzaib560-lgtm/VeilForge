"""
Probe interfaces for VeilForge.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ProbeCategory(str, Enum):
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK = "jailbreak"
    TOOL_ABUSE = "tool_abuse"
    MEMORY_POISONING = "memory_poisoning"
    GOAL_HIJACKING = "goal_hijacking"
    DATA_EXTRACTION = "data_extraction"
    MULTI_AGENT = "multi_agent"
    UNCATEGORIZED = "uncategorized"


class ProbeSpec(BaseModel):
    """Specification/metadata for a probe."""

    id: str
    name: str
    category: ProbeCategory
    severity: Literal["low", "medium", "high", "critical"]
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    supports_multi_turn: bool = False
    min_turns: int = Field(default=1, ge=1)
    max_turns: int = Field(default=1, ge=1)
    required_capabilities: set[str] = Field(default_factory=set)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AttackPlanStep(BaseModel):
    """A single step in an attack plan."""

    turn_id: str
    action: str
    content: str | None = None
    fork: bool = False
    fork_label: str | None = None
    delay: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class AttackPlan(BaseModel):
    """Structured plan for executing a probe."""

    probe_id: str
    steps: list[AttackPlanStep] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseProbe(ABC):
    """Abstract base class for all VeilForge probes."""

    spec: ProbeSpec

    @abstractmethod
    async def plan(self, session: Any) -> AttackPlan:
        """Return a structured plan (turns, goals, success criteria)."""
        raise NotImplementedError

    @abstractmethod
    async def execute(self, session: Any, plan: AttackPlan) -> list[Any]:
        """Execute the plan against the session."""
        raise NotImplementedError

    @abstractmethod
    def classify(self, transcript: Any) -> list[Any]:
        """Map transcript to findings."""
        raise NotImplementedError

    async def run(self, session: Any) -> list[Any]:
        """Run the full probe lifecycle: plan -> execute -> classify."""
        plan = await self.plan(session)
        turns = await self.execute(session, plan)
        findings = self.classify(getattr(session, "transcript", None))
        return self._to_probe_results(turns, findings)

    def _to_probe_results(self, turns: list[Any], findings: list[Any]) -> list[Any]:
        """Convert turns and findings to probe results."""
        # Default implementation - subclasses can override
        from veilforge.core.models.result import ProbeResult

        return [
            ProbeResult(
                probe_id=self.spec.id,
                probe_name=self.spec.name,
                category=self.spec.category.value,
                severity=self.spec.severity,
                turns=turns or [],
                findings=findings or [],
                success_count=sum(1 for f in (findings or []) if getattr(f, "attack_succeeded", False)),
            )
        ]
