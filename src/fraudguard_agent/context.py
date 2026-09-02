import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .models import ConversationState, SessionView


class FactSource(StrEnum):
    USER_CLAIM = "USER_CLAIM"
    CORE_FACT = "CORE_FACT"
    AGENT_INFERENCE = "AGENT_INFERENCE"
    UNKNOWN = "UNKNOWN"


class CaseFact(BaseModel):
    value: Any
    source: FactSource


class ToolRecord(BaseModel):
    name: str
    trace_id: str | None
    outcome: str
    result_digest: str


class SessionContext(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    session_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    channel: str = "web"
    language: str = "en"
    state: ConversationState = ConversationState.NEW
    intent: str = "unknown"
    trace_id: str | None = None
    known_facts: dict[str, CaseFact] = Field(default_factory=dict)
    missing_facts: list[str] = Field(default_factory=list)
    tool_history: list[ToolRecord] = Field(default_factory=list)
    last_core_decision: dict[str, Any] | None = None
    turn_count: int = 0
    tool_step_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def view(self) -> SessionView:
        return SessionView(
            session_id=self.session_id,
            state=self.state,
            intent=self.intent,
            trace_id=self.trace_id,
            language=self.language,
            turn_count=self.turn_count,
            tool_step_count=self.tool_step_count,
            created_at=self.created_at.isoformat(),
            updated_at=self.updated_at.isoformat(),
        )


class SessionNotFound(KeyError):
    pass


class SessionStore:
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl = timedelta(seconds=ttl_seconds)
        self.sessions: dict[uuid.UUID, SessionContext] = {}
        self.lock = asyncio.Lock()

    async def create(self, channel: str = "web") -> SessionContext:
        async with self.lock:
            self._purge()
            session = SessionContext(channel=channel)
            self.sessions[session.session_id] = session
            return session

    async def get(self, session_id: uuid.UUID) -> SessionContext:
        async with self.lock:
            self._purge()
            session = self.sessions.get(session_id)
            if session is None:
                raise SessionNotFound(str(session_id))
            session.updated_at = datetime.now(UTC)
            return session

    async def delete(self, session_id: uuid.UUID) -> None:
        async with self.lock:
            if self.sessions.pop(session_id, None) is None:
                raise SessionNotFound(str(session_id))

    def _purge(self) -> None:
        cutoff = datetime.now(UTC) - self.ttl
        for session_id in [
            key for key, value in self.sessions.items() if value.updated_at < cutoff
        ]:
            del self.sessions[session_id]
