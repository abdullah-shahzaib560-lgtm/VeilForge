"""
Session state and budget models for VeilForge.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class Budget(BaseModel):
    """Resource budget for a campaign or session."""

    turns: int = Field(default=200, ge=0)
    seconds: float = Field(default=600.0, ge=0.0)
    tokens: int | None = Field(default=None, ge=0)

    turns_used: int = Field(default=0, ge=0)
    seconds_used: float = Field(default=0.0, ge=0.0)
    tokens_used: int = Field(default=0, ge=0)

    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def can_continue(self) -> bool:
        """Check if budget allows more execution."""
        if self.turns_used >= self.turns and self.turns >= 0:
            return False
        if self.tokens is not None and self.tokens_used >= self.tokens:
            return False
        return True

    def consume_turn(self, turns: int = 1) -> None:
        self.turns_used += turns

    def consume_time(self, seconds: float) -> None:
        self.seconds_used += seconds

    def consume_tokens(self, tokens: int) -> None:
        self.tokens_used += tokens

    def clone(self) -> "Budget":
        """Create a copy of the budget."""
        return Budget.model_validate(self.model_dump())


class SessionState(BaseModel):
    """Runtime state for an attack session."""

    session_id: str
    target: str | None = None
    parent_id: str | None = None
    history_limit: int = Field(default=50, ge=0)
    turn_count: int = Field(default=0, ge=0)
    state: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def increment_turn(self) -> None:
        self.turn_count += 1
        self.updated_at = datetime.now(timezone.utc)

    def update(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now(timezone.utc)
