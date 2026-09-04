import secrets
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .context import SessionNotFound, SessionStore
from .core_client import CoreClient, CoreError
from .models import ChatRequest, ChatResponse, SessionCreate, SessionView, ToolExecutionRequest
from .runtime import AgentRuntime

settings = get_settings()
core = CoreClient(settings)
sessions = SessionStore(settings.agent_session_ttl_seconds)
runtime = AgentRuntime(settings, sessions, core)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await core.close()


app = FastAPI(
    title="FraudGuard Backend Agent",
    version="0.2.0",
    lifespan=lifespan,
    docs_url=None if settings.production else "/docs",
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-Agent-Key"],
)


async def authenticate_agent(
    x_agent_key: Annotated[str | None, Header(alias="X-Agent-Key")] = None,
) -> None:
    if settings.agent_access_key and not secrets.compare_digest(
        x_agent_key or "", settings.agent_access_key
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid agent access key")


AgentAuth = Annotated[None, Depends(authenticate_agent)]


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "fraudguard-agent",
        "provider": settings.agent_model_provider,
    }


@app.get("/ready")
async def ready() -> dict[str, str]:
    if not await core.ready():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "FraudGuard Core is not ready")
    return {"status": "ready", "core": "ready"}


@app.post("/agent/v1/sessions", status_code=201)
async def create_session(payload: SessionCreate, _: AgentAuth) -> SessionView:
    return (await sessions.create(payload.channel)).view()


@app.get("/agent/v1/sessions/{session_id}")
async def get_session(session_id: uuid.UUID, _: AgentAuth) -> SessionView:
    try:
        return (await sessions.get(session_id)).view()
    except SessionNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found") from exc


@app.delete("/agent/v1/sessions/{session_id}", status_code=204)
async def delete_session(session_id: uuid.UUID, _: AgentAuth) -> Response:
    try:
        await sessions.delete(session_id)
    except SessionNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found") from exc
    return Response(status_code=204)


@app.post("/agent/v1/chat")
async def chat(payload: ChatRequest, _: AgentAuth) -> ChatResponse:
    try:
        session = (
            await sessions.get(payload.session_id)
            if payload.session_id
            else await sessions.create("api")
        )
    except SessionNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found") from exc
    return await runtime.chat(session, payload.message, payload.context)


@app.get("/agent/v1/tools")
async def list_tools(_: AgentAuth) -> dict[str, Any]:
    return {
        "data": [
            {
                "name": tool.name,
                "description": tool.description,
                "required_scope": tool.required_scope,
                "side_effect": tool.side_effect,
                "protected_action": tool.protected_action,
                "idempotency_required": tool.idempotency_required,
            }
            for tool in runtime.tools.tools.values()
        ]
    }


@app.post("/agent/v1/tools/{tool_name}/execute")
async def execute_tool(
    tool_name: str,
    payload: ToolExecutionRequest,
    _: AgentAuth,
    x_trace_id: Annotated[str | None, Header(alias="X-Trace-ID")] = None,
) -> dict[str, Any]:
    """Execute one allowlisted typed tool without invoking the native planner."""
    try:
        return await runtime.tools.execute(tool_name, payload.arguments, x_trace_id)
    except CoreError as exc:
        headers = {"X-Trace-ID": exc.trace_id} if exc.trace_id else None
        raise HTTPException(exc.status_code, str(exc), headers=headers) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
