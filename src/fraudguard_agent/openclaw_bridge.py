"""Public FraudGuard bridge to the private OpenClaw Gateway.

OpenClaw owns orchestration and skill selection on this path. FraudGuard Core remains
the only authority for evidence, risk, policy, and protected decisions.
"""

from __future__ import annotations

import json
import re
import secrets
import uuid
from contextlib import asynccontextmanager
from typing import Annotated, Any

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, status

from .config import get_settings
from .core_client import CoreClient, CoreError
from .models import ChatRequest
from .telegram import HttpTelegramApi, TelegramError, TelegramProcessor
from .tools import ToolRegistry

settings = get_settings()

ALLOWED_SKILLS = {
    "fraud-detection:v1",
    "intelligence-search:v1",
    "realtime-intervention:v1",
    "safety-payment:v1",
    "social-engineering:v1",
}
ALLOWED_INPUT_TYPES = {
    "BANK_ACCOUNT",
    "DOMAIN",
    "EMAIL",
    "IP_ADDRESS",
    "MESSAGE",
    "PHONE",
    "TRANSACTION",
    "URL",
}
SKILL_TOOLS = {
    "fraud-detection:v1": ("fraud_analyze", "intelligence_lookup"),
    "intelligence-search:v1": ("intelligence_lookup",),
    "realtime-intervention:v1": ("submit_intervention_response",),
    "safety-payment:v1": ("safety_payment",),
    "social-engineering:v1": ("fraud_analyze", "intelligence_lookup"),
}
DEFAULT_TOOLS = (
    "fraud_analyze",
    "intelligence_lookup",
    "safety_payment",
    "submit_intervention_response",
)
CORE_AUTHORITY_FIELDS = (
    "actions",
    "evidence",
    "graph",
    "input",
    "intelligence",
    "intelligence_health",
    "intervention_id",
    "policy",
    "providers",
    "recommended_action",
    "risk",
    "signals",
    "summary",
    "trace",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.gateway = httpx.AsyncClient(
        base_url=settings.openclaw_gateway_url.rstrip("/"),
        timeout=settings.openclaw_timeout_seconds,
        follow_redirects=False,
    )
    app.state.core = CoreClient(settings)
    app.state.tools = ToolRegistry(app.state.core)
    app.state.telegram_api = None
    app.state.telegram = None
    if settings.telegram_enabled:
        app.state.telegram_api = HttpTelegramApi(
            settings.telegram_bot_token.get_secret_value()
        )
        app.state.telegram = TelegramProcessor(
            settings,
            app.state.core,
            app.state.telegram_api,
            telegram_analysis,
        )
    yield
    if app.state.telegram_api is not None:
        await app.state.telegram_api.close()
    await app.state.gateway.aclose()
    await app.state.core.close()


app = FastAPI(
    title="FraudGuard OpenClaw Bridge",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)


async def authenticate_bridge(
    x_agent_key: Annotated[str | None, Header(alias="X-Agent-Key")] = None,
) -> None:
    if settings.agent_access_key and not secrets.compare_digest(
        x_agent_key or "", settings.agent_access_key
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid agent access key")


BridgeAuth = Annotated[None, Depends(authenticate_bridge)]


def gateway_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x-openclaw-agent-id": settings.openclaw_agent_id,
        "x-openclaw-message-channel": "web",
    }
    if settings.openclaw_gateway_token:
        headers["Authorization"] = f"Bearer {settings.openclaw_gateway_token}"
    return headers


def extract_output_text(body: dict[str, Any]) -> str:
    direct = body.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    parts: list[str] = []
    output = body.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                value = block.get("text") or block.get("output_text")
                if isinstance(value, str):
                    parts.append(value)
    return "\n".join(parts).strip()


def structured_output(text: str) -> dict[str, Any] | None:
    candidates = [text]
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        candidates.insert(0, fenced.group(1))
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def instructions(
    skill: str | None,
    input_type: str | None,
    trusted_intervention_id: str | None = None,
    trusted_external_payment_id: str | None = None,
) -> str:
    selected = skill or "automatic skill selection"
    kind = input_type or "MESSAGE"
    intervention_context = (
        "\nA prior Core-authoritative workflow supplied intervention_id "
        f"{trusted_intervention_id}. Use it only for submit_intervention_response."
        if trusted_intervention_id is not None
        else ""
    )
    payment_context = (
        "\nThe Telegram transport supplied idempotent external_payment_id "
        f"{trusted_external_payment_id}. Use it only for safety_payment."
        if trusted_external_payment_id is not None
        else ""
    )
    return f"""You are the only orchestration and skill-selection layer for FraudGuard.
Use the installed FraudGuard workspace skills and the provided typed function tools.
For browser requests, prefer provided function tools; do not invoke shell, exec, curl,
or generic HTTP.
Requested skill: {selected}. Input type: {kind}.
FraudGuard Core is the sole authority for evidence, risk, policy, and decisions.
Never invent provider results, evidence, scores, policy, incidents, or trace IDs.
Return exactly one JSON object with these fields when available:
message, status, selected_skill, trace_id, risk, policy, recommended_action, signals,
providers, summary, evidence, graph, trace, actions, intervention_id.
Use null, empty arrays, or empty objects when Core did not return a field.
Do not wrap the JSON in Markdown.{intervention_context}{payment_context}"""


def normalized_context(context: dict[str, Any]) -> tuple[str | None, str]:
    """Reduce browser-supplied routing hints to fixed, non-instruction values."""

    requested_skill = str(context.get("requested_skill") or "").strip().lower()
    selected_skill = requested_skill if requested_skill in ALLOWED_SKILLS else None
    requested_type = str(context.get("input_type") or "MESSAGE").strip().upper()
    input_type = requested_type if requested_type in ALLOWED_INPUT_TYPES else "MESSAGE"
    return selected_skill, input_type


def client_tools(selected_skill: str | None) -> list[dict[str, Any]]:
    registry: ToolRegistry = app.state.tools
    names = SKILL_TOOLS.get(selected_skill, DEFAULT_TOOLS)
    return [
        {
            "type": "function",
            "name": name,
            "description": registry.tools[name].description,
            "parameters": registry.tools[name].input_model.model_json_schema(),
        }
        for name in names
    ]


def function_calls(body: dict[str, Any]) -> list[dict[str, Any]]:
    output = body.get("output")
    if not isinstance(output, list):
        return []
    return [
        item
        for item in output
        if isinstance(item, dict)
        and item.get("type") == "function_call"
        and isinstance(item.get("name"), str)
        and isinstance(item.get("call_id"), str)
    ]


def authoritative_response(
    normalized: dict[str, Any],
    tool_results: list[dict[str, Any]],
    selected_skill: str | None,
) -> dict[str, Any]:
    """Overwrite protected fields only with values returned by FraudGuard Core."""

    for field in (*CORE_AUTHORITY_FIELDS, "decision", "score", "severity", "trace_id"):
        normalized.pop(field, None)
    merged: dict[str, Any] = {}
    trace_id: str | None = None
    for result in tool_results:
        data = result.get("data")
        if not isinstance(data, dict):
            continue
        merged.update(data)
        for field in CORE_AUTHORITY_FIELDS:
            if field in data:
                normalized[field] = data[field]
        if result.get("trace_id"):
            trace_id = str(result["trace_id"])
    if not merged:
        normalized.update(
            {
                "message": "OpenClaw did not obtain an authoritative result from FraudGuard Core.",
                "status": "failed",
                "trace_id": None,
                "risk": {"score": None, "level": "UNKNOWN"},
                "policy": {"decision": "PENDING"},
                "recommended_action": {
                    "code": "REVIEW_REQUIRED",
                    "message": (
                        "Do not treat this result as a safety decision; "
                        "retry or verify manually."
                    ),
                },
                "signals": [],
                "providers": [],
                "summary": {},
                "evidence": [],
                "graph": {"nodes": [], "edges": []},
                "trace": [],
                "skills_used": [],
            }
        )
        return normalized

    existing_risk = merged.get("risk") if isinstance(merged.get("risk"), dict) else {}
    score = existing_risk.get("score", merged.get("score"))
    level = existing_risk.get("level", existing_risk.get("severity", merged.get("severity")))
    signals = merged.get("signals", existing_risk.get("signals", []))
    policy = merged.get("policy") if isinstance(merged.get("policy"), dict) else {}
    decision = str(policy.get("decision") or "PENDING").upper()
    action_by_decision = {
        "ALLOW": (
            "PROCEED_WITH_CAUTION",
            "No blocking policy matched, but continue only after normal verification.",
        ),
        "REVIEW": (
            "REVIEW_REQUIRED",
            "Review the evidence and verify through an official channel before proceeding.",
        ),
        "STEP_UP_VERIFY": (
            "VERIFY_OFFICIAL_CHANNEL",
            "Complete additional verification through an official channel before proceeding.",
        ),
        "TEMPORARY_HOLD": (
            "DO_NOT_PROCEED",
            "Pause the transaction until the flagged risk has been independently verified.",
        ),
    }
    action_code, action_message = action_by_decision.get(
        decision, ("REVIEW_REQUIRED", "No final Core policy decision is available.")
    )
    recommended_action = merged.get("recommended_action")
    if not isinstance(recommended_action, dict):
        recommended_action = {"code": action_code, "message": action_message}
    normalized.update(
        {
            "message": (
                f"OpenClaw completed {selected_skill or 'automatic skill routing'}. "
                f"FraudGuard Core returned risk {str(level or 'UNKNOWN').upper()}"
                f"{'' if score is None else f' ({score}/100)'} and policy {decision}."
            ),
            "status": "completed",
            "trace_id": trace_id,
            "risk": {**existing_risk, "score": score, "level": str(level or "UNKNOWN").upper()},
            "policy": policy or {"decision": decision},
            "recommended_action": recommended_action,
            "signals": signals if isinstance(signals, list) else [],
            "decision": decision,
            "score": score,
            "severity": str(level or "UNKNOWN").upper(),
            "skills_used": [selected_skill] if selected_skill else [],
        }
    )
    provider_status = merged.get("provider_status")
    if "providers" not in normalized and isinstance(provider_status, dict):
        normalized["providers"] = provider_status.get("items", [])
    return normalized


async def gateway_request(path: str, *, payload: dict[str, Any] | None = None) -> httpx.Response:
    client: httpx.AsyncClient = app.state.gateway
    try:
        return await client.request(
            "POST" if payload is not None else "GET",
            path,
            headers=gateway_headers(),
            json=payload,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "OpenClaw Gateway is unavailable",
        ) from exc


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "fraudguard-openclaw-bridge", "runtime": "openclaw"}


@app.get("/ready")
async def ready(_: BridgeAuth) -> dict[str, str]:
    response = await gateway_request("/v1/models")
    if response.is_error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "OpenClaw Gateway is not ready")
    return {"status": "ready", "orchestrator": "openclaw"}


@app.get("/agent/v1/tools")
async def tools(_: BridgeAuth) -> dict[str, Any]:
    response = await gateway_request("/v1/models")
    if response.is_error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "OpenClaw Gateway is not ready",
        )
    return {
        "status": "SUCCESS",
        "orchestrator": "openclaw",
        "skills": [
            "fraud-detection:v1",
            "safety-payment:v1",
            "realtime-intervention:v1",
            "social-engineering:v1",
            "intelligence-search:v1",
        ],
    }


async def run_openclaw(
    payload: ChatRequest,
    *,
    accept_trusted_context: bool = False,
) -> dict[str, Any]:
    session_id = payload.session_id or uuid.uuid4()
    requested_skill, input_type = normalized_context(payload.context)
    trusted_intervention_id = None
    trusted_external_payment_id = None
    if accept_trusted_context:
        candidate = payload.context.get("trusted_intervention_id")
        try:
            trusted_intervention_id = str(uuid.UUID(str(candidate)))
        except (ValueError, TypeError, AttributeError):
            pass
        payment_candidate = payload.context.get("trusted_external_payment_id")
        if isinstance(payment_candidate, str) and re.fullmatch(
            r"evt_[0-9a-f]{64}", payment_candidate
        ):
            trusted_external_payment_id = payment_candidate
    request_body = {
        "model": f"openclaw/{settings.openclaw_agent_id}",
        "input": payload.message,
        "instructions": instructions(
            requested_skill,
            input_type,
            trusted_intervention_id,
            trusted_external_payment_id,
        ),
        "user": f"fraudguard-web-{session_id}",
        "stream": False,
        "max_output_tokens": 4096,
        "metadata": {"source": "fraudguard-web", "requested_skill": requested_skill or "auto"},
        "tools": client_tools(requested_skill),
        "tool_choice": "auto",
    }
    body: dict[str, Any] = {}
    tool_results: list[dict[str, Any]] = []
    call_cache: dict[str, dict[str, Any]] = {}
    for _ in range(settings.agent_max_tool_steps + 1):
        response = await gateway_request("/v1/responses", payload=request_body)
        try:
            body = response.json()
        except ValueError as exc:
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY, "OpenClaw returned an invalid response"
            ) from exc
        if response.is_error:
            detail = body.get("error", {}).get("message") if isinstance(body, dict) else None
            raise HTTPException(response.status_code, detail or "OpenClaw rejected the analysis")
        calls = function_calls(body)
        if not calls:
            break
        outputs: list[dict[str, str]] = []
        registry: ToolRegistry = app.state.tools
        permitted = set(SKILL_TOOLS.get(requested_skill, DEFAULT_TOOLS))
        for call in calls:
            name = str(call["name"])
            raw_arguments = call.get("arguments", "{}")
            try:
                arguments = (
                    json.loads(raw_arguments)
                    if isinstance(raw_arguments, str)
                    else raw_arguments
                )
                if not isinstance(arguments, dict):
                    raise ValueError("tool arguments must be an object")
                if name not in permitted:
                    raise ValueError(f"Tool is not allowed for this skill: {name}")
                cache_key = json.dumps([name, arguments], sort_keys=True, separators=(",", ":"))
                result = call_cache.get(cache_key)
                if result is None:
                    result = await registry.execute(name, arguments, None)
                    call_cache[cache_key] = result
                    tool_results.append(result)
                output = result
            except (json.JSONDecodeError, ValueError, CoreError) as exc:
                output = {"error": {"message": str(exc), "type": "tool_error"}}
            outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": str(call["call_id"]),
                    "output": json.dumps(output, ensure_ascii=False, separators=(",", ":")),
                }
            )
        response_id = body.get("id")
        if not isinstance(response_id, str) or not response_id:
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                "OpenClaw omitted the response id required for tool continuation",
            )
        request_body = {
            **request_body,
            "input": outputs,
            "previous_response_id": response_id,
        }
    else:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "OpenClaw exceeded the maximum tool steps",
        )
    text = extract_output_text(body)
    normalized = structured_output(text)
    if normalized is None:
        normalized = {
            "message": text or "OpenClaw completed without a textual response.",
            "status": "completed",
            "selected_skill": requested_skill,
            "trace_id": None,
            "risk": {"score": None, "level": "UNKNOWN"},
            "policy": {"decision": "PENDING"},
            "recommended_action": {},
            "signals": [],
            "providers": [],
            "summary": {},
            "evidence": [],
            "graph": {"nodes": [], "edges": []},
            "trace": [],
        }
    normalized = authoritative_response(normalized, tool_results, requested_skill)
    normalized["session_id"] = str(session_id)
    normalized["orchestrator"] = "openclaw"
    normalized.setdefault("message", text)
    normalized.setdefault("status", "completed")
    normalized.setdefault("selected_skill", requested_skill)
    return normalized


async def telegram_analysis(
    message: str,
    session_id: uuid.UUID,
    context: dict[str, Any],
) -> dict[str, Any]:
    try:
        return await run_openclaw(
            ChatRequest(session_id=session_id, message=message, context=context),
            accept_trusted_context=True,
        )
    except HTTPException:
        return {
            "status": "failed",
            "trace_id": None,
            "risk": {"score": None, "level": "UNKNOWN"},
            "policy": {"decision": "PENDING"},
            "recommended_action": {
                "code": "REVIEW_REQUIRED",
                "message": (
                    "Analisis authoritative belum tersedia. Jangan lanjutkan transaksi "
                    "dan verifikasi melalui kanal resmi."
                ),
            },
            "signals": [],
        }


@app.post("/agent/v1/chat")
async def chat(payload: ChatRequest, _: BridgeAuth) -> dict[str, Any]:
    return await run_openclaw(payload)


@app.post("/telegram/v1/webhook", include_in_schema=False)
async def telegram_webhook(
    payload: dict[str, Any],
    x_telegram_secret: Annotated[
        str | None, Header(alias="X-Telegram-Bot-Api-Secret-Token")
    ] = None,
) -> dict[str, bool]:
    if not settings.telegram_enabled or app.state.telegram is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Telegram integration is disabled")
    expected = settings.telegram_webhook_secret.get_secret_value()
    if not secrets.compare_digest(x_telegram_secret or "", expected):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Telegram webhook secret")
    try:
        await app.state.telegram.handle(payload)
    except TelegramError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Telegram delivery failed"
        ) from exc
    return {"ok": True}
