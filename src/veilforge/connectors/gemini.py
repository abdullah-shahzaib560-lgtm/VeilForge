"""
Gemini connector for VeilForge.

Talks to Google's Gemini API (generativelanguage.googleapis.com).
Supports multi-turn conversations, system instructions, proxies,
and a small request delay to reduce free-tier rate limiting.
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Optional

import httpx

from veilforge.connectors.base import Connector, ConnectorResponse
from veilforge.core.interfaces.connector import BaseConnector
from veilforge.core.models.message import Message
from veilforge.network.proxy import ProxyConfig, ProxyManager


class GeminiConnector(Connector, BaseConnector):
    """Talks to the Google Gemini API."""

    DEFAULT_MODEL = "gemini-2.0-flash"
    API_BASE = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        timeout: float = 120.0,
        proxy_url: Optional[str] = None,
        use_tor: bool = False,
        request_delay: float = 0.6,
        **kwargs: Any,
    ):
        """
        Args:
            model: Gemini model id (e.g. gemini-2.0-flash, gemini-1.5-pro).
            api_key: API key. Falls back to GEMINI_API_KEY env var / .env.
            system_prompt: Optional system instruction sent on every request.
            timeout: HTTP timeout in seconds.
            proxy_url: Optional HTTP/SOCKS proxy (e.g. socks5://127.0.0.1:9050).
            use_tor: Shortcut to use the default local Tor SOCKS port.
            request_delay: Seconds to sleep before each request (helps free-tier limits).
        """
        Connector.__init__(self, **kwargs)
        self.name = f"gemini:{model}"
        self.model = model
        self.system_prompt = system_prompt
        self.request_delay = max(0.0, float(request_delay))
        self._timeout = timeout

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Set it in the environment, a .env file, "
                "or pass api_key= to GeminiConnector."
            )

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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def send(self, message: str, **kwargs: Any) -> ConnectorResponse:
        """Send a single user message (legacy path used by the old Campaign engine)."""
        start = time.perf_counter()
        self.record("user", message)

        # Build contents from recorded history so multi-turn probes work.
        contents = self._history_to_contents()
        if not contents or contents[-1].get("role") != "user":
            # Fallback if history was empty / out of sync
            contents = [{"role": "user", "parts": [{"text": message}]}]

        resp = await self._generate_content(contents, start=start, **kwargs)
        if resp.ok and resp.text:
            self.record("assistant", resp.text)
        return resp

    async def generate(
        self,
        messages: list[Any],
        *,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> ConnectorResponse:
        """
        New-style generate used by AttackSession / CampaignRunner.
        Accepts a full message list and maps it to Gemini's contents format.
        """
        start = time.perf_counter()
        contents = self._messages_to_contents(messages)
        if not contents:
            return ConnectorResponse(
                text="",
                error="No user message found to send to Gemini",
                latency_seconds=time.perf_counter() - start,
            )

        return await self._generate_content(
            contents,
            start=start,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop,
            **kwargs,
        )

    async def fork(self) -> "GeminiConnector":
        forked = GeminiConnector(
            model=self.model,
            api_key=self.api_key,
            system_prompt=self.system_prompt,
            timeout=self._timeout,
            proxy_url=self.proxy_manager.config.proxy_url,
            use_tor=self.proxy_manager.config.use_tor,
            request_delay=self.request_delay,
        )
        forked.name = self.name
        return forked

    async def close(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _generate_content(
        self,
        contents: list[dict[str, Any]],
        *,
        start: float,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> ConnectorResponse:
        if self.request_delay > 0:
            await asyncio.sleep(self.request_delay)

        url = f"{self.API_BASE}/models/{self.model}:generateContent"
        params = {"key": self.api_key}

        payload: dict[str, Any] = {"contents": contents}

        if self.system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": self.system_prompt}]
            }

        generation_config: dict[str, Any] = {}
        if temperature is not None:
            generation_config["temperature"] = temperature
        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens
        if stop:
            generation_config["stopSequences"] = stop
        if generation_config:
            payload["generationConfig"] = generation_config

        try:
            reply = await self._client.post(url, params=params, json=payload)
            reply.raise_for_status()
            data = reply.json()
        except httpx.HTTPStatusError as e:
            body = (e.response.text or "")[:400]
            return ConnectorResponse(
                text="",
                error=f"Gemini HTTP {e.response.status_code}: {body}",
                latency_seconds=time.perf_counter() - start,
            )
        except httpx.TimeoutException:
            return ConnectorResponse(
                text="",
                error=f"Gemini request timed out after {self._timeout}s",
                latency_seconds=time.perf_counter() - start,
            )
        except Exception as e:
            return ConnectorResponse(
                text="",
                error=f"{type(e).__name__}: {e}",
                latency_seconds=time.perf_counter() - start,
            )

        text, finish_reason, error = self._extract_text(data)
        usage = self._extract_usage(data)

        return ConnectorResponse(
            text=text,
            raw=data,
            error=error,
            latency_seconds=time.perf_counter() - start,
            usage=usage,
            finish_reason=finish_reason,
        )

    def _extract_text(
        self, data: dict[str, Any]
    ) -> tuple[str, Optional[str], Optional[str]]:
        """
        Parse Gemini response.
        Returns (text, finish_reason, error).
        Handles empty candidates and safety blocks cleanly.
        """
        candidates = data.get("candidates") or []
        if not candidates:
            # Often happens when the prompt is blocked by promptFeedback
            feedback = data.get("promptFeedback") or {}
            block_reason = feedback.get("blockReason")
            if block_reason:
                return "", "SAFETY", f"Prompt blocked by Gemini safety filters ({block_reason})"
            return "", None, "Gemini returned no candidates"

        candidate = candidates[0]
        finish_reason = candidate.get("finishReason")
        content = candidate.get("content") or {}
        parts = content.get("parts") or []

        text_parts = []
        for part in parts:
            if isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
        text = "".join(text_parts)

        if finish_reason in ("SAFETY", "RECITATION", "OTHER") and not text:
            return "", finish_reason, f"Response blocked or empty (finishReason={finish_reason})"

        return text, finish_reason, None

    def _extract_usage(self, data: dict[str, Any]) -> Optional[dict[str, int]]:
        meta = data.get("usageMetadata")
        if not meta:
            return None
        return {
            "prompt_tokens": int(meta.get("promptTokenCount") or 0),
            "completion_tokens": int(meta.get("candidatesTokenCount") or 0),
            "total_tokens": int(meta.get("totalTokenCount") or 0),
        }

    def _history_to_contents(self) -> list[dict[str, Any]]:
        """Convert the legacy self._history into Gemini contents."""
        contents: list[dict[str, Any]] = []
        for turn in self._history:
            role = turn.get("role", "user")
            # Gemini uses "user" and "model" (not "assistant")
            gemini_role = "model" if role in ("assistant", "model") else "user"
            content = turn.get("content", "")
            if not content:
                continue
            contents.append({"role": gemini_role, "parts": [{"text": content}]})
        return contents

    def _messages_to_contents(self, messages: list[Any]) -> list[dict[str, Any]]:
        """Convert a list of Message / dict into Gemini contents."""
        contents: list[dict[str, Any]] = []
        for m in messages:
            if isinstance(m, Message):
                role = m.role
                content = m.content
                if isinstance(content, list):
                    text = " ".join(
                        getattr(p, "text", "") or ""
                        for p in content
                        if getattr(p, "text", None)
                    )
                else:
                    text = content or ""
            elif isinstance(m, dict):
                role = m.get("role", "user")
                text = m.get("content", "") or ""
            else:
                continue

            if not text:
                continue
            if role == "system":
                # System messages are handled via systemInstruction; skip here.
                continue
            gemini_role = "model" if role in ("assistant", "model") else "user"
            contents.append({"role": gemini_role, "parts": [{"text": text}]})
        return contents
