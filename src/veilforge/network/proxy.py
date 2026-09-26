"""
Network / Privacy Layer - Proxy support for AegisAgent.

This module will handle HTTP, HTTPS, SOCKS5 proxies,
proxy chaining, and optional Tor routing.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class ProxyConfig:
    """Configuration for proxy usage."""
    enabled: bool = False
    proxy_url: Optional[str] = None          # e.g. socks5://127.0.0.1:9050
    chain: Optional[list[str]] = None        # list of proxy URLs for chaining
    use_tor: bool = False
    timeout: float = 30.0


class ProxyManager:
    """
    Manages proxy configuration for outbound requests.
    """

    def __init__(self, config: Optional[ProxyConfig] = None):
        self.config = config or ProxyConfig()

    def get_proxy_settings(self) -> dict:
        """Return proxy settings compatible with httpx / aiohttp."""
        if not self.config.enabled:
            return {}

        if self.config.use_tor:
            # Default Tor SOCKS port
            return {"proxy": "socks5://127.0.0.1:9050"}

        if self.config.proxy_url:
            return {"proxy": self.config.proxy_url}

        return {}

    def is_enabled(self) -> bool:
        return self.config.enabled
