"""
Basic configuration handling for AegisAgent.
"""

from pydantic import BaseModel, Field
from typing import Optional


class AegisConfig(BaseModel):
    """Main configuration model."""
    
    # Target
    target_url: Optional[str] = None
    target_type: str = "openai"          # openai, anthropic, custom, etc.

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


def load_config() -> AegisConfig:
    """Load configuration (placeholder for now)."""
    return AegisConfig()
