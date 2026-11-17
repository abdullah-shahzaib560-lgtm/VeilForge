"""
Attack session system for multi-turn attacks.
"""

import time
import uuid
from typing import Any

from veilforge.core.interfaces.connector import BaseConnector
from veilforge.core.models.message import Message
from veilforge.core.models.result import TurnResult
from veilforge.core.models.session import Budget, SessionState


class Transcript:
    """Conversation transcript for an attack session."""

    def __init__(self) -> None:
        self.turns: list[TurnResult] = []

    def append(self, turn: TurnResult) -> None:
        """Append a turn to the transcript."""
        self.turns.append(turn)

    def slice(self, from_turn: int = 0) -> "Transcript":
        """Create a sliced copy of the transcript."""
        sliced = Transcript()
        sliced.turns = list(self.turns[from_turn:])
        return sliced

    def messages(self) -> list[Message]:
        """Flatten transcript to a list of messages for connector consumption."""
        messages: list[Message] = []
        for turn in self.turns:
            messages.append(turn.user_message)
            if turn.assistant_message:
                messages.append(turn.assistant_message)
        return messages

    def clear(self) -> None:
        """Clear all turns."""
        self.turns = []

    def __len__(self) -> int:
        return len(self.turns)

    def __iter__(self):
        return iter(self.turns)


class AttackSession:
    """Session for executing multi-turn attacks against a target."""

    def __init__(
        self,
        connector: BaseConnector,
        session_id: str | None = None,
        budget: Budget | None = None,
        history_limit: int = 50,
        parent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.id = session_id or str(uuid.uuid4())
        self.connector = connector
        self.transcript = Transcript()
        self.state = SessionState(
            session_id=self.id,
            target=getattr(connector, "name", None),
            parent_id=parent_id,
            history_limit=history_limit,
            metadata=metadata or {},
        )
        self.budget = budget or Budget()
        self.parent_id = parent_id
        self._start_time = time.time()

    async def send_user(self, content: str, **kwargs: Any) -> TurnResult:
        """Send a user message and get the assistant response."""
        if not self.can_continue():
            raise RuntimeError("Session budget exceeded or cannot continue")

        turn_id = str(uuid.uuid4())
        user_msg = Message(role="user", content=content)

        start = time.perf_counter()
        try:
            # Build messages from transcript + new user message
            messages = self.transcript.messages() + [user_msg]
            resp = await self.connector.generate(messages, **kwargs)

            latency = time.perf_counter() - start
            assistant_msg = None
            if resp.text or resp.tool_calls:
                assistant_msg = Message(role="assistant", content=resp.text, tool_calls=resp.tool_calls)

            turn = TurnResult(
                turn_id=turn_id,
                user_message=user_msg,
                assistant_message=assistant_msg,
                response_text=resp.text,
                tool_calls=[tc.model_dump() if hasattr(tc, "model_dump") else tc for tc in resp.tool_calls],
                latency_seconds=latency,
                error=resp.error,
                metadata={"finish_reason": resp.finish_reason},
            )
        except Exception as e:
            latency = time.perf_counter() - start
            turn = TurnResult(
                turn_id=turn_id,
                user_message=user_msg,
                assistant_message=None,
                response_text="",
                error=str(e),
                latency_seconds=latency,
            )

        self.transcript.append(turn)
        self.state.increment_turn()
        self.budget.consume_turn(1)
        self.budget.consume_time(latency)

        return turn

    async def fork(self, label: str = "fork") -> "AttackSession":
        """Fork this session for branching attacks."""
        forked_connector = await self.connector.fork()

        forked_budget = self.budget.clone()
        forked_session = AttackSession(
            connector=forked_connector,
            session_id=f"{self.id}:{label}:{uuid.uuid4().hex[:8]}",
            budget=forked_budget,
            history_limit=self.state.history_limit,
            parent_id=self.id,
            metadata={"fork_label": label, **self.state.metadata},
        )

        # Copy transcript
        forked_session.transcript.turns = []
        for turn in self.transcript.turns:
            forked_session.transcript.turns.append(turn.model_copy(deep=True))

        forked_session.state.turn_count = self.state.turn_count
        return forked_session

    def can_continue(self) -> bool:
        """Check if the session can continue execution."""
        if not self.budget.can_continue():
            return False
        if self.state.history_limit > 0 and len(self.transcript) >= self.state.history_limit:
            return False
        # Check time budget
        elapsed = time.time() - self._start_time
        if self.budget.seconds_used + elapsed > self.budget.seconds and self.budget.seconds >= 0:
            # More accurate check - update seconds used
            if elapsed > self.budget.seconds and self.budget.seconds > 0:
                return False
        return True

    def get_messages(self) -> list[Message]:
        """Get all messages from the transcript."""
        return self.transcript.messages()

    def reset(self) -> None:
        """Reset the session state."""
        self.transcript.clear()
        self.state.turn_count = 0
        self.state.updated_at = self.state.updated_at
        self.connector.reset()
        self.budget.turns_used = 0
        self.budget.seconds_used = 0.0
        self.budget.tokens_used = 0
        self._start_time = time.time()

    async def close(self) -> None:
        """Close the session and underlying connector."""
        await self.connector.close()
