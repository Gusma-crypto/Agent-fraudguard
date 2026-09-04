import uuid
from typing import Any

import pytest

from fraudguard_agent.config import Settings
from fraudguard_agent.telegram import TelegramProcessor, format_result, parse_update
from fraudguard_agent.telegram_setup import webhook_payload


class FakeCore:
    def __init__(self, status: str = "UNKNOWN") -> None:
        self.status = status
        self.updates: list[dict[str, Any]] = []

    async def get_channel_consent(self, channel: str, subject_ref: str):
        return {"data": {"status": self.status}, "trace_id": "trace-consent"}

    async def update_channel_consent(self, payload: dict[str, Any], trace_id=None):
        self.updates.append(payload)
        self.status = {
            "GRANT": "GRANTED",
            "DENY": "DENIED",
            "REVOKE": "REVOKED",
        }[payload["action"]]
        return {"data": {"status": self.status}, "trace_id": "trace-consent"}


class FakeTelegramApi:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []
        self.callbacks: list[tuple[str, str]] = []

    async def send_message(self, chat_id, text, *, reply_to=None, reply_markup=None):
        self.messages.append(
            {
                "chat_id": chat_id,
                "text": text,
                "reply_to": reply_to,
                "reply_markup": reply_markup,
            }
        )

    async def answer_callback(self, callback_id: str, text: str) -> None:
        self.callbacks.append((callback_id, text))


def settings() -> Settings:
    return Settings(
        _env_file=None,
        telegram_enabled=True,
        telegram_bot_token="token",
        telegram_webhook_secret="w" * 32,
        telegram_subject_hmac_key="h" * 32,
        telegram_bot_username="FraudGuardBot",
    )


def message_update(text: str, *, update_id: int = 1, chat_type: str = "private"):
    return {
        "update_id": update_id,
        "message": {
            "message_id": 10,
            "from": {"id": 123456789, "is_bot": False},
            "chat": {"id": -100 if chat_type != "private" else 123456789, "type": chat_type},
            "text": text,
        },
    }


@pytest.mark.asyncio
async def test_private_message_requires_consent_without_analyzing() -> None:
    core = FakeCore()
    api = FakeTelegramApi()
    analyzed: list[str] = []

    async def analyze(text: str, session_id: uuid.UUID, context: dict[str, Any]):
        analyzed.append(text)
        return {}

    result = await TelegramProcessor(settings(), core, api, analyze).handle(
        message_update("Saya diminta transfer sekarang")
    )
    assert result["status"] == "consent_required"
    assert analyzed == []
    assert api.messages[0]["reply_markup"]["inline_keyboard"]


@pytest.mark.asyncio
async def test_consent_callback_uses_hmac_subject_not_telegram_id() -> None:
    core = FakeCore()
    api = FakeTelegramApi()

    async def analyze(*args: Any):
        return {}

    payload = {
        "update_id": 2,
        "callback_query": {
            "id": "callback-1",
            "from": {"id": 123456789},
            "data": "consent:grant:v1",
            "message": {
                "message_id": 11,
                "chat": {"id": 123456789, "type": "private"},
            },
        },
    }
    await TelegramProcessor(settings(), core, api, analyze).handle(payload)
    assert core.updates[0]["subject_ref"].startswith("ch_")
    assert "123456789" not in str(core.updates[0])
    assert core.updates[0]["action"] == "GRANT"


@pytest.mark.asyncio
async def test_consented_message_calls_openclaw_once() -> None:
    core = FakeCore("GRANTED")
    api = FakeTelegramApi()
    calls: list[tuple[str, uuid.UUID, dict[str, Any]]] = []

    async def analyze(text: str, session_id: uuid.UUID, context: dict[str, Any]):
        calls.append((text, session_id, context))
        return {
            "trace_id": "trace-1",
            "risk": {"score": 91, "level": "HIGH"},
            "policy": {"decision": "TEMPORARY_HOLD"},
            "signals": [{"code": "PAYMENT_REQUEST"}],
        }

    processor = TelegramProcessor(settings(), core, api, analyze)
    await processor.handle(message_update("Transfer hadiah ke BCA", update_id=3))
    await processor.handle(message_update("Transfer hadiah ke BCA", update_id=3))
    assert len(calls) == 1
    assert calls[0][2]["channel"] == "telegram"
    assert "HIGH" in api.messages[0]["text"]
    assert "TEMPORARY_HOLD" in api.messages[0]["text"]


@pytest.mark.asyncio
async def test_unmentioned_group_message_is_ignored_without_core_call() -> None:
    core = FakeCore("GRANTED")
    api = FakeTelegramApi()

    async def analyze(*args: Any):
        raise AssertionError("analysis must not run")

    result = await TelegramProcessor(settings(), core, api, analyze).handle(
        message_update("percakapan grup biasa", update_id=4, chat_type="supergroup")
    )
    assert result["status"] == "ignored"
    assert api.messages == []


def test_result_formatter_escapes_telegram_html() -> None:
    formatted = format_result(
        {
            "risk": {"score": 50, "level": "<HIGH>"},
            "policy": {"decision": "REVIEW"},
            "signals": ["<script>"],
        }
    )
    assert "<script>" not in formatted
    assert "&lt;script&gt;" in formatted


def test_parser_ignores_channel_posts_and_invalid_updates() -> None:
    assert parse_update({"update_id": 1, "channel_post": {"text": "ignore"}}) is None
    assert parse_update({"update_id": "not-an-int"}) is None


@pytest.mark.asyncio
async def test_help_does_not_require_consent_or_run_analysis() -> None:
    core = FakeCore()
    api = FakeTelegramApi()

    async def analyze(*args: Any):
        raise AssertionError("help must not run analysis")

    result = await TelegramProcessor(settings(), core, api, analyze).handle(
        message_update("/help", update_id=5)
    )
    assert result["status"] == "processed"
    assert "Cara memakai FraudGuard" in api.messages[0]["text"]


def test_webhook_payload_is_https_and_limits_update_types() -> None:
    payload = webhook_payload(settings(), "https://fraudguard.my.id/telegram/v1/webhook")
    assert payload["allowed_updates"] == ["message", "callback_query"]
    assert payload["secret_token"] == "w" * 32
    with pytest.raises(ValueError, match="HTTPS"):
        webhook_payload(settings(), "http://localhost/telegram/v1/webhook")
