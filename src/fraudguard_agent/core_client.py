import asyncio
import hashlib
import json
import uuid
from typing import Any

import httpx

from .config import Settings


class CoreError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 502,
        code: str = "CORE_UNAVAILABLE",
        trace_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.trace_id = trace_id


class CoreClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        base = settings.fraudguard_core_base_url.rstrip("/")
        self.api_prefix = "/api/v1"
        origin = base[: -len(self.api_prefix)] if base.endswith(self.api_prefix) else base
        self.client = httpx.AsyncClient(
            base_url=origin,
            timeout=settings.agent_core_timeout_seconds,
            follow_redirects=False,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        trace_id: str | None = None,
        idempotency_key: str | None = None,
        authenticated: bool = True,
    ) -> dict[str, Any]:
        correlation = trace_id or str(uuid.uuid4())
        headers = {"X-Trace-ID": correlation}
        if authenticated:
            headers["X-API-Key"] = self.settings.fraudguard_core_api_key
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        retryable = method == "GET" or idempotency_key is not None
        attempts = 2 if retryable else 1
        response: httpx.Response | None = None
        for attempt in range(attempts):
            try:
                response = await self.client.request(method, path, json=payload, headers=headers)
            except httpx.HTTPError as exc:
                if attempt + 1 == attempts:
                    raise CoreError(
                        "FraudGuard Core tidak dapat dihubungi", trace_id=correlation
                    ) from exc
                await asyncio.sleep(0.1)
                continue
            if response.status_code < 500 or attempt + 1 == attempts:
                break
            await asyncio.sleep(0.1)
        if response is None:
            raise CoreError("FraudGuard Core tidak memberikan respons", trace_id=correlation)
        try:
            body = response.json()
        except ValueError as exc:
            raise CoreError("Respons FraudGuard Core tidak valid", trace_id=correlation) from exc
        if response.is_error:
            error = body.get("error") if isinstance(body, dict) else None
            meta = body.get("meta") if isinstance(body, dict) else None
            if not isinstance(error, dict):
                error = {}
            if not isinstance(meta, dict):
                meta = {}
            raise CoreError(
                str(error.get("message", "FraudGuard Core menolak permintaan")),
                status_code=response.status_code,
                code=str(error.get("code", "CORE_REQUEST_ERROR")),
                trace_id=str(meta.get("trace_id", correlation)),
            )
        if path in {"/health", "/ready"}:
            if not isinstance(body, dict):
                raise CoreError("Respons health Core tidak valid", trace_id=correlation)
            return {"data": body, "trace_id": correlation}
        if not isinstance(body, dict) or "data" not in body:
            raise CoreError("Kontrak respons Core tidak valid", trace_id=correlation)
        meta = body.get("meta")
        if not isinstance(meta, dict) or not meta.get("trace_id"):
            raise CoreError("Core tidak mengembalikan trace_id", trace_id=correlation)
        if not isinstance(body["data"], dict):
            raise CoreError("Data respons Core tidak valid", trace_id=correlation)
        return {"data": body["data"], "trace_id": str(meta["trace_id"])}

    async def ready(self) -> bool:
        try:
            result = await self.request("GET", "/ready", authenticated=False)
        except CoreError:
            return False
        return result["data"].get("status") == "ready"

    async def fraud_analyze(
        self, arguments: dict[str, Any], trace_id: str | None
    ) -> dict[str, Any]:
        return await self.request(
            "POST", f"{self.api_prefix}/fraud/analyze", arguments, trace_id=trace_id
        )

    async def create_assessment(
        self, arguments: dict[str, Any], trace_id: str | None
    ) -> dict[str, Any]:
        return await self.request(
            "POST", f"{self.api_prefix}/assessments", arguments, trace_id=trace_id
        )

    async def ingest_event(
        self, arguments: dict[str, Any], trace_id: str | None
    ) -> dict[str, Any]:
        source = str(arguments.get("external_id") or uuid.uuid4()).encode()
        key = f"agent-event:{hashlib.sha256(source).hexdigest()}"
        return await self.request(
            "POST",
            f"{self.api_prefix}/events",
            arguments,
            trace_id=trace_id,
            idempotency_key=key,
        )

    async def safety_payment(
        self, arguments: dict[str, Any], trace_id: str | None
    ) -> dict[str, Any]:
        source = str(arguments["external_payment_id"]).encode()
        key = f"agent-payment:{hashlib.sha256(source).hexdigest()}"
        return await self.request(
            "POST",
            f"{self.api_prefix}/payments/check",
            arguments,
            trace_id=trace_id,
            idempotency_key=key,
        )

    async def create_intervention(
        self, arguments: dict[str, Any], trace_id: str | None
    ) -> dict[str, Any]:
        canonical = json.dumps(arguments, sort_keys=True, separators=(",", ":")).encode()
        key = f"agent-intervention:{hashlib.sha256(canonical).hexdigest()}"
        return await self.request(
            "POST",
            f"{self.api_prefix}/interventions",
            arguments,
            trace_id=trace_id,
            idempotency_key=key,
        )

    async def submit_intervention_response(
        self, arguments: dict[str, Any], trace_id: str | None
    ) -> dict[str, Any]:
        intervention_id = arguments.pop("intervention_id")
        return await self.request(
            "POST",
            f"{self.api_prefix}/interventions/{intervention_id}/responses",
            arguments,
            trace_id=trace_id,
        )

    async def get_incident(self, arguments: dict[str, Any], trace_id: str | None) -> dict[str, Any]:
        return await self.request(
            "GET",
            f"{self.api_prefix}/incidents/{arguments['incident_id']}",
            trace_id=trace_id,
        )

    async def get_trace(self, arguments: dict[str, Any], trace_id: str | None) -> dict[str, Any]:
        return await self.request(
            "GET", f"{self.api_prefix}/traces/{arguments['trace_id']}", trace_id=trace_id
        )

    async def get_trace_audit(
        self, arguments: dict[str, Any], trace_id: str | None
    ) -> dict[str, Any]:
        return await self.request(
            "GET",
            f"{self.api_prefix}/traces/{arguments['trace_id']}/audit",
            trace_id=trace_id,
        )

    async def get_capability(
        self, arguments: dict[str, Any], trace_id: str | None
    ) -> dict[str, Any]:
        return await self.request(
            "GET",
            f"{self.api_prefix}/capabilities/{arguments['name']}",
            trace_id=trace_id,
        )
