"""
Base Connector interface (compatibility layer).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

# Re-export from new interfaces for compatibility
from veilforge.core.interfaces.connector import BaseConnector as NewBaseConnector
from veilforge.core.interfaces.connector import ConnectorCapabilities, ConnectorResponse as NewConnectorResponse


@dataclass
class ConnectorResponse:
    """Normalized result of sending a message to a target."""

    text: str
    raw: Any = None
    tool_calls: list[dict] = field(default_factory=list)
    error: Optional[str] = None
    latency_seconds: Optional[float] = None
    usage: Optional[dict[str, int]] = None
    finish_reason: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def to_new(self) -> NewConnectorResponse:
        """Convert to new style response."""
        from veilforge.core.models.message import ToolCall

        tool_calls = []
        for tc in self.tool_calls:
            if isinstance(tc, dict):
                tool_calls.append(ToolCall(**tc))
            elif hasattr(tc, "name"):
                tool_calls.append(tc)
        return NewConnectorResponse(
            text=self.text,
            tool_calls=tool_calls,
            raw=self.raw,
            usage=self.usage,
            latency_seconds=self.latency_seconds,
            finish_reason=self.finish_reason,
            error=self.error,
        )

    @classmethod
    def from_new(cls, resp: NewConnectorResponse) -> "ConnectorResponse":
        """Convert from new style response."""
        tool_calls = []
        for tc in resp.tool_calls:
            if hasattr(tc, "model_dump"):
                tool_calls.append(tc.model_dump())
            elif isinstance(tc, dict):
                tool_calls.append(tc)
        return cls(
            text=resp.text,
            raw=resp.raw,
            tool_calls=tool_calls,
            error=resp.error,
            latency_seconds=resp.latency_seconds,
            usage=resp.usage,
            finish_reason=resp.finish_reason,
        )


class Connector(ABC):
    """
    Abstract base class for all VeilForge target connectors.
    Maintains backward compatibility with existing code.
    """

    name: str = "base"

    def __init__(self, **config: Any):
        self.config = config
        self._history: list[dict[str, str]] = []
        # Also support new style history
        try:
            from veilforge.core.models.message import Message

            self._message_history: list[Message] = []
        except Exception:
            self._message_history = []

    @abstractmethod
    async def send(self, message: str, **kwargs: Any) -> ConnectorResponse:
        """Send a message to the target and return its response."""
        raise NotImplementedError

    def reset(self) -> None:
        """Clear conversation state (for multi-turn probe isolation)."""
        self._history = []
        if hasattr(self, "_message_history"):
            self._message_history = []

    def record(self, role: str, content: str) -> None:
        """Track conversation history for multi-turn probes."""
        self._history.append({"role": role, "content": content})
        try:
            from veilforge.core.models.message import Message

            if hasattr(self, "_message_history"):
                self._message_history.append(Message(role=role, content=content))  # type: ignore
        except Exception:
            pass

    @property
    def history(self) -> list[dict[str, str]]:
        return list(self._history)

    async def close(self) -> None:
        """Override to clean up connections/clients. No-op by default."""
        return None

    async def fork(self) -> "Connector":
        """Create a fork for branching attacks."""
        return self

    async def generate(self, messages, **kwargs: Any) -> ConnectorResponse:
        """New-style generate method for compatibility."""
        # Default implementation tries to extract last user message
        try:
            from veilforge.core.models.message import Message

            if messages and isinstance(messages[-1], Message) and messages[-1].role == "user":
                content = messages[-1].content
                if isinstance(content, str):
                    return await self.send(content, **kwargs)
                elif isinstance(content, list):
                    # Extract text
                    text = " ".join(p.text for p in content if hasattr(p, "text") and p.text)
                    return await self.send(text, **kwargs)
        except Exception:
            pass
        # Fallback
        if messages:
            last = messages[-1]
            if isinstance(last, dict) and last.get("role") == "user":
                return await self.send(last.get("content", ""), **kwargs)
        raise NotImplementedError("Connector must implement send() or generate()")


# For new code that wants to use new interfaces
BaseConnector = NewBaseConnector
__all__ = ["Connector", "ConnectorResponse", "BaseConnector", "ConnectorCapabilities"]
