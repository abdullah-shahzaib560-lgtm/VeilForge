"""
Connector interfaces for VeilForge.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from veilforge.core.models.message import Message, ToolCall


class ConnectorCapabilities(BaseModel):
    """Capabilities advertised by a connector/target."""

    supports_system: bool = True
    supports_tools: bool = False
    supports_multi_turn: bool = True
    supports_streaming: bool = False
    supports_vision: bool = False
    max_context_tokens: int | None = None


class ConnectorResponse(BaseModel):
    """Normalized response from a connector."""

    text: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    raw: Any = None
    usage: dict[str, int] | None = None
    latency_seconds: float | None = None
    finish_reason: str | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


class BaseConnector(ABC):
    """Abstract base class for all VeilForge target connectors."""

    name: str = "base"
    capabilities: ConnectorCapabilities = ConnectorCapabilities()

    def __init__(self, **config: Any) -> None:
        self.config = config
        self._history: list[Message] = []

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        *,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> ConnectorResponse:
        """Send a full conversation to the target and return its response."""
        raise NotImplementedError

    def reset(self) -> None:
        """Clear conversation state."""
        self._history = []

    async def fork(self) -> "BaseConnector":
        """Create a forked instance of the connector for branching attacks."""
        # Default implementation returns self; override in subclasses for true forking
        return self

    async def close(self) -> None:
        """Clean up connections/clients."""
        return None

    async def send(self, message: str, **kwargs: Any) -> ConnectorResponse:
        """Backward-compatible helper to send a single user message."""
        from veilforge.core.models.message import Message

        msgs = list(self._history) + [Message(role="user", content=message)]
        resp = await self.generate(msgs, **kwargs)
        self._record_exchange(message, resp)
        return resp

    def _record_exchange(self, user_message: str, resp: ConnectorResponse) -> None:
        """Record exchange in history (best-effort)."""
        try:
            from veilforge.core.models.message import Message

            self._history.append(Message(role="user", content=user_message))
            if resp.text:
                self._history.append(Message(role="assistant", content=resp.text))
        except Exception:
            pass

    @property
    def history(self) -> list[Message]:
        return list(self._history)
