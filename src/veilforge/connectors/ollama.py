"""
Ollama connector for VeilForge.
"""

import time
from typing import Any, Optional

import httpx

from veilforge.connectors.base import Connector, ConnectorResponse
from veilforge.core.interfaces.connector import BaseConnector
from veilforge.core.models.message import Message
from veilforge.network.proxy import ProxyManager, ProxyConfig


class OllamaConnector(Connector, BaseConnector):
    """Talks to a local or remote Ollama instance."""

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://127.0.0.1:11434",
        system_prompt: Optional[str] = None,
        timeout: float = 120.0,
        proxy_url: Optional[str] = None,
        use_tor: bool = False,
        **kwargs: Any,
    ):
        Connector.__init__(self, name=f"ollama:{model}", **kwargs)
        self.name = f"ollama:{model}"
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

        # Convert Message objects to dicts
        msg_dicts = []
        for m in messages:
            if isinstance(m, Message):
                content = m.content
                if isinstance(content, list):
                    # Extract text from content parts
                    text = " ".join(p.text for p in content if hasattr(p, "text") and p.text)
                    msg_dicts.append({"role": m.role, "content": text})
                else:
                    msg_dicts.append({"role": m.role, "content": content})
            elif isinstance(m, dict):
                msg_dicts.append(m)

        payload = {"model": self.model, "messages": msg_dicts, "stream": False}
        if temperature is not None:
            payload["options"] = payload.get("options", {})
            payload["options"]["temperature"] = temperature

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

        return ConnectorResponse(
            text=text,
            raw=data,
            latency_seconds=time.perf_counter() - start,
        )

    async def fork(self) -> "OllamaConnector":
        forked = OllamaConnector(
            model=self.model,
            base_url=self.base_url,
            system_prompt=self.system_prompt,
            proxy_url=self.proxy_manager.config.proxy_url if hasattr(self.proxy_manager, "config") else None,
            use_tor=self.proxy_manager.config.use_tor if hasattr(self.proxy_manager, "config") else False,
        )
        forked.name = self.name
        return forked

    async def close(self) -> None:
        await self._client.aclose()
