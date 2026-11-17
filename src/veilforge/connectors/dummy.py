"""
Dummy connector - echoes canned or pattern-based responses.

Useful for testing the orchestration engine without hitting a real API.
"""

import time
from typing import Any, Optional

from veilforge.core.interfaces.connector import BaseConnector, ConnectorCapabilities, ConnectorResponse
from veilforge.core.models.message import Message


class DummyConnector(BaseConnector):
    """
    A fake target that returns a fixed or callback-generated response.
    Uses the new BaseConnector interface with generate().
    """

    name = "dummy"
    capabilities = ConnectorCapabilities(
        supports_system=True,
        supports_tools=False,
        supports_multi_turn=True,
        supports_streaming=False,
        supports_vision=False,
    )

    def __init__(
        self,
        response: str = "This is a dummy response.",
        responder: Optional[Any] = None,
        **config: Any,
    ):
        super().__init__(**config)
        self.name = "dummy"
        self.response = response
        self.responder = responder
        # Keep old-style history for backward compat
        self._history_dict: list[dict[str, str]] = []

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
        start = time.perf_counter()
        # Use last user message
        last_msg = messages[-1] if messages else None
        message_text = ""
        if last_msg:
            if isinstance(last_msg, Message):
                if isinstance(last_msg.content, str):
                    message_text = last_msg.content
                elif isinstance(last_msg.content, list):
                    message_text = " ".join(p.text for p in last_msg.content if hasattr(p, "text") and p.text)
            elif isinstance(last_msg, dict):
                message_text = last_msg.get("content", "")

        if self.responder:
            text = self.responder(message_text)
        else:
            text = self.response

        latency = time.perf_counter() - start
        # Update histories
        self._history_dict.append({"role": "user", "content": message_text})
        self._history_dict.append({"role": "assistant", "content": text})
        self._history.append(Message(role="user", content=message_text))
        self._history.append(Message(role="assistant", content=text))

        return ConnectorResponse(
            text=text,
            raw={"messages": [m.model_dump() if hasattr(m, "model_dump") else m for m in messages]},
            latency_seconds=latency,
        )

    async def send(self, message: str, **kwargs: Any) -> ConnectorResponse:
        """Backward compatible send method."""
        start = time.perf_counter()
        self._history_dict.append({"role": "user", "content": message})

        if self.responder:
            text = self.responder(message)
        else:
            text = self.response

        self._history_dict.append({"role": "assistant", "content": text})
        latency = time.perf_counter() - start
        return ConnectorResponse(
            text=text,
            raw={"message": message},
            latency_seconds=latency,
        )

    def reset(self) -> None:
        super().reset()
        self._history_dict = []

    def record(self, role: str, content: str) -> None:
        self._history_dict.append({"role": role, "content": content})

    @property
    def history(self) -> list[dict[str, str]]:
        return list(self._history_dict)

    async def fork(self) -> "DummyConnector":
        forked = DummyConnector(response=self.response, responder=self.responder)
        forked.name = self.name
        return forked
