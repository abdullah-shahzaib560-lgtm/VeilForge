"""
Base Connector interface.

A Connector abstracts the differences between LLM providers and agent
frameworks so the Attack Engine can send messages, observe tool calls,
inject context, and reset state without knowing which backend it's
talking to.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ConnectorResponse:
    """Normalized result of sending a message to a target."""

    text: str
    raw: Any = None
    tool_calls: list[dict] = field(default_factory=list)
    error: Optional[str] = None
    latency_seconds: Optional[float] = None

    @property
    def ok(self) -> bool:
        return self.error is None


class Connector(ABC):
    """
    Abstract base class for all VeilForge target connectors.
    """

    name: str = "base"

    def __init__(self, **config: Any):
        self.config = config
        self._history: list[dict[str, str]] = []

    @abstractmethod
    async def send(self, message: str, **kwargs: Any) -> ConnectorResponse:
        """Send a message to the target and return its response."""
        raise NotImplementedError

    def reset(self) -> None:
        """Clear conversation state (for multi-turn probe isolation)."""
        self._history = []

    def record(self, role: str, content: str) -> None:
        """Track conversation history for multi-turn probes."""
        self._history.append({"role": role, "content": content})

    @property
    def history(self) -> list[dict[str, str]]:
        return list(self._history)

    async def close(self) -> None:
        """Override to clean up connections/clients. No-op by default."""
        return None
