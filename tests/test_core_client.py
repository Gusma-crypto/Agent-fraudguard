import json

import httpx
import pytest

from fraudguard_agent.config import Settings
from fraudguard_agent.core_client import CoreClient, CoreError


@pytest.mark.asyncio
async def test_payment_contract_uses_core_auth_trace_and_idempotency() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["api_key"] = request.headers["X-API-Key"]
        captured["trace"] = request.headers["X-Trace-ID"]
        captured["idempotency"] = request.headers["Idempotency-Key"]
        body = json.loads(request.content)
        assert body["external_payment_id"] == "pay-001"
        return httpx.Response(
            201,
            json={
                "data": {"decision": "ALLOW", "risk": {"score": 10, "severity": "low"}},
                "meta": {"trace_id": captured["trace"]},
            },
        )

    settings = Settings(
        fraudguard_core_base_url="https://core.example/api/v1",
        fraudguard_core_api_key="scoped-test-key",
    )
    core = CoreClient(settings)
    await core.client.aclose()
    core.client = httpx.AsyncClient(
        base_url="https://core.example", transport=httpx.MockTransport(handler)
    )
    result = await core.safety_payment(
        {
            "external_payment_id": "pay-001",
            "amount": "10000.00",
            "currency": "IDR",
            "sender_ref": None,
            "recipient_ref": "recipient-masked",
            "recipient_is_new": False,
            "context": {},
        },
        None,
    )
    await core.close()
    assert captured["path"] == "/api/v1/payments/check"
    assert captured["api_key"] == "scoped-test-key"
    assert captured["idempotency"].startswith("agent-payment:")
    assert result["data"]["decision"] == "ALLOW"


@pytest.mark.asyncio
async def test_intervention_contract_is_idempotent() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["idempotency"] = request.headers["Idempotency-Key"]
        return httpx.Response(
            201,
            json={
                "data": {"id": "intervention-1", "status": "PENDING"},
                "meta": {"trace_id": request.headers["X-Trace-ID"]},
            },
        )

    settings = Settings(
        fraudguard_core_base_url="https://core.example/api/v1",
        fraudguard_core_api_key="scoped-test-key",
    )
    core = CoreClient(settings)
    await core.client.aclose()
    core.client = httpx.AsyncClient(
        base_url="https://core.example", transport=httpx.MockTransport(handler)
    )
    await core.create_intervention(
        {
            "payment_check_id": None,
            "type": "FRAUD_MANUAL_REVIEW",
            "channel": "API",
            "verification_context": {"assessment_id": "assessment-1"},
        },
        None,
    )
    await core.close()
    assert captured["path"] == "/api/v1/interventions"
    assert captured["idempotency"].startswith("agent-intervention:")


@pytest.mark.asyncio
async def test_intelligence_lookup_uses_bounded_core_endpoint() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            201,
            json={
                "data": {
                    "status": "INSUFFICIENT_INTELLIGENCE",
                    "entity": {"type": "PHONE", "display_value": "+628****7890"},
                },
                "meta": {"trace_id": request.headers["X-Trace-ID"]},
            },
        )

    core = CoreClient(
        Settings(
            fraudguard_core_base_url="https://core.example/api/v1",
            fraudguard_core_api_key="scoped-test-key",
        )
    )
    await core.client.aclose()
    core.client = httpx.AsyncClient(
        base_url="https://core.example", transport=httpx.MockTransport(handler)
    )
    await core.intelligence_lookup(
        {
            "query": "0812-3456-7890",
            "entity_type": "PHONE",
            "deep_search": False,
            "context": {},
        },
        None,
    )
    await core.close()

    assert captured["path"] == "/api/v1/intelligence/search"
    assert captured["body"] == {
        "query": "0812-3456-7890",
        "entity_type": "PHONE",
        "deep_search": False,
        "context": {},
    }


def test_production_requires_https_and_credentials() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        Settings(app_env="production", fraudguard_core_base_url="http://core/api/v1")


@pytest.mark.asyncio
async def test_malformed_error_envelope_fails_as_core_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "not-an-object", "meta": []})

    core = CoreClient(Settings(fraudguard_core_api_key="test-key"))
    await core.client.aclose()
    core.client = httpx.AsyncClient(
        base_url="https://core.example", transport=httpx.MockTransport(handler)
    )
    with pytest.raises(CoreError) as raised:
        await core.request("POST", "/api/v1/fraud/analyze", {})
    await core.close()
    assert "menolak" in str(raised.value)


@pytest.mark.asyncio
async def test_malformed_success_data_fails_closed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"data": [], "meta": {"trace_id": request.headers["X-Trace-ID"]}},
        )

    core = CoreClient(Settings(fraudguard_core_api_key="test-key"))
    await core.client.aclose()
    core.client = httpx.AsyncClient(
        base_url="https://core.example", transport=httpx.MockTransport(handler)
    )
    with pytest.raises(CoreError):
        await core.request("POST", "/api/v1/fraud/analyze", {})
    await core.close()
