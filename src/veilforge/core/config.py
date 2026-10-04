"""
Basic configuration handling for VeilForge.
"""

from pydantic import BaseModel
from typing import Optional


class VeilConfig(BaseModel):
    """Main configuration model."""

    # Target
    target_url: Optional[str] = None
    target_type: str = "ollama"          # ollama, dummy, openai, etc.

    # Privacy
    proxy_enabled: bool = False
    proxy_url: Optional[str] = None
    use_tor: bool = False

    # Output
    output_dir: str = "reports"
    report_format: str = "json"          # json, pdf, both

    # General
    verbose: bool = False
    timeout: float = 30.0


def load_config() -> VeilConfig:
    """Load configuration (placeholder for now)."""
    return VeilConfig()
