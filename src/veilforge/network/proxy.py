from typing import Optional
from dataclasses import dataclass, field


@dataclass
class ProxyConfig:
    """Configuration for proxy usage."""
    enabled: bool = False
    proxy_url: Optional[str] = None          # e.g. socks5://127.0.0.1:9050
    chain: list[str] = field(default_factory=list)
    use_tor: bool = False
    timeout: float = 30.0


class ProxyManager:
    """
    Manages proxy configuration for outbound requests.
    Compatible with httpx.
    """

    def __init__(self, config: Optional[ProxyConfig] = None):
        self.config = config or ProxyConfig()

    def get_httpx_proxy(self) -> Optional[str]:
        """Return a single proxy URL for httpx, or None."""
        if not self.config.enabled:
            return None

        if self.config.use_tor:
            return "socks5://127.0.0.1:9050"

        if self.config.proxy_url:
            return self.config.proxy_url

        return None

    def is_enabled(self) -> bool:
        return self.config.enabled and (
            self.config.use_tor or bool(self.config.proxy_url)
        )
