"""
Dummy connector - echoes canned or pattern-based responses.

Useful for testing the orchestration engine without hitting a real API.
"""

import time
from typing import Any, Optional

from veilforge.connectors.base import Connector, ConnectorResponse


class DummyConnector(Connector):
    """
    A fake target that returns a fixed or callback-generated response.
    """

    name = "dummy"

    def __init__(
        self,
        response: str = "This is a dummy response.",
        responder: Optional[Any] = None,
        **config: Any,
    ):
        super().__init__(**config)
        self.response = response
        self.responder = responder

    async def send(self, message: str, **kwargs: Any) -> ConnectorResponse:
        start = time.perf_counter()
        self.record("user", message)

        text = self.responder(message) if self.responder else self.response

        self.record("assistant", text)
        return ConnectorResponse(
            text=text,
            raw={"message": message},
            latency_seconds=time.perf_counter() - start,
        )
