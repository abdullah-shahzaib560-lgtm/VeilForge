import os
import time
from typing import Any, Optional

import httpx

from veilforge.connectors.base import Connector, ConnectorResponse


class GeminiConnector(Connector):
    """Talks to Google Gemini API."""

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        api_key: Optional[str] = None,
        timeout: float = 120.0,
    ):
        super().__init__(name=f"gemini:{model}")
        self.model = model
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Set it in .env or pass api_key="
            )
        self._client = httpx.AsyncClient(timeout=timeout)

    async def send(self, message: str, **kwargs: Any) -> ConnectorResponse:
        start = time.perf_counter()
        self.record("user", message)

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        params = {"key": self.api_key}
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": message}],
                }
            ]
        }

        try:
            reply = await self._client.post(url, params=params, json=payload)
            reply.raise_for_status()
            data = reply.json()

            text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

        except httpx.HTTPStatusError as e:
            return ConnectorResponse(
                text="",
                error=f"Gemini HTTP {e.response.status_code}: {e.response.text[:300]}",
                latency_seconds=time.perf_counter() - start,
            )
        except Exception as e:
            return ConnectorResponse(
                text="",
                error=f"{type(e).__name__}: {e}",
                latency_seconds=time.perf_counter() - start,
            )

        self.record("assistant", text)
        return ConnectorResponse(
            text=text,
            raw=data,
            latency_seconds=time.perf_counter() - start,
        )

    async def close(self) -> None:
        await self._client.aclose()
