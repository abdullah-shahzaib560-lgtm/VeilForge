"""
Message and content models for VeilForge.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """Represents a tool/function call from an assistant."""

    id: str | None = None
    type: Literal["function"] = "function"
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ContentPart(BaseModel):
    """A part of multi-modal or structured content."""

    type: Literal["text", "image", "thought"] = "text"
    text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Message(BaseModel):
    """A single message in a conversation."""

    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[ContentPart]
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
