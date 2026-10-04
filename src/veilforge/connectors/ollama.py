"""
Ollama connector for VeilForge.
"""

import time
from typing import Any, Optional

import httpx

from veilforge.connectors.base import Connector, ConnectorResponse
from veilforge.network.proxy import ProxyManager, ProxyConfig


class OllamaConnector(Connector):
    """Talks to a local or remote Ollama instance."""

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://127.0.0.1:11434",
        system_prompt: Optional[str] = None,
        timeout: float = 60.0,
        proxy_url: Optional[str] = None,
        use_tor: bool = False,
    ):
        super().__init__(name=f"ollama:{model}")
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.system_prompt = system_prompt

        # Proxy setup
        proxy_config = ProxyConfig(
            enabled=bool(proxy_url) or use_tor,
            proxy_url=proxy_url,
            use_tor=use_tor,
        )
        self.proxy_manager = ProxyManager(proxy_config)
        proxy = self.proxy_manager.get_httpx_proxy()

        self._client = httpx.AsyncClient(
            timeout=timeout,
            proxy=proxy,
        )

    async def send(self, message: str, **kwargs: Any) -> ConnectorResponse:
        start = time.perf_counter()
        self.record("user", message)

        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.extend(self._history)

        payload = {"model": self.model, "messages": messages, "stream": False}

        try:
            reply = await self._client.post(f"{self.base_url}/api/chat", json=payload)
            reply.raise_for_status()
            data = reply.json()
            text = data["message"]["content"]

        except httpx.ConnectError:
            return ConnectorResponse(
                text="",
                error=f"Cannot reach Ollama at {self.base_url}. Is it running?",
                latency_seconds=time.perf_counter() - start,
            )
        except httpx.HTTPStatusError as e:
            return ConnectorResponse(
                text="",
                error=f"Ollama returned HTTP {e.response.status_code}: {e.response.text[:200]}",
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
