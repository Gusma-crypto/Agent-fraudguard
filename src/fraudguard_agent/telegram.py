from __future__ import annotations

import hashlib
import hmac
import html
import re
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from .config import Settings
from .core_client import CoreClient, CoreError

Analyze = Callable[[str, uuid.UUID, dict[str, Any]], Awaitable[dict[str, Any]]]


class TelegramError(RuntimeError):
    pass


class TelegramApi(Protocol):
    async def send_message(
        self,
        chat_id: int,
        text: str,
        *,
        reply_to: int | None = None,
        reply_markup: dict[str, Any] | None = None,
    ) -> None: ...

    async def answer_callback(self, callback_id: str, text: str) -> None: ...


class HttpTelegramApi:
    def __init__(self, token: str, timeout: float = 10) -> None:
        self.client = httpx.AsyncClient(
            base_url=f"https://api.telegram.org/bot{token}",
            timeout=timeout,
            follow_redirects=False,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def _call(self, method: str, payload: dict[str, Any]) -> None:
        try:
            response = await self.client.post(f"/{method}", json=payload)
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise TelegramError("Telegram Bot API tidak dapat dihubungi") from exc
        if response.is_error or not isinstance(body, dict) or body.get("ok") is not True:
            raise TelegramError("Telegram Bot API menolak respons bot")

    async def send_message(
        self,
        chat_id: int,
        text: str,
        *,
        reply_to: int | None = None,
        reply_markup: dict[str, Any] | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text[:4096],
            "parse_mode": "HTML",
            "link_preview_options": {"is_disabled": True},
        }
        if reply_to is not None:
            payload["reply_parameters"] = {"message_id": reply_to}
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        await self._call("sendMessage", payload)

    async def answer_callback(self, callback_id: str, text: str) -> None:
        await self._call(
            "answerCallbackQuery",
            {"callback_query_id": callback_id, "text": text[:200]},
        )


@dataclass(frozen=True, slots=True)
class InboundMessage:
    update_id: int
    chat_id: int
    chat_type: str
    user_id: int
    message_id: int
    text: str
    reply_text: str | None
    reply_from_bot: bool
    from_bot: bool


@dataclass(frozen=True, slots=True)
class ConsentCallback:
    update_id: int
    callback_id: str
    chat_id: int
    chat_type: str
    user_id: int
    message_id: int | None
    action: str


def _integer(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def parse_update(payload: dict[str, Any]) -> InboundMessage | ConsentCallback | None:
    update_id = _integer(payload.get("update_id"))
    if update_id is None:
        return None
    callback = payload.get("callback_query")
    if isinstance(callback, dict):
        sender = callback.get("from")
        message = callback.get("message")
        data = callback.get("data")
        callback_id = callback.get("id")
        if not isinstance(sender, dict) or not isinstance(message, dict):
            return None
        chat = message.get("chat")
        if not isinstance(chat, dict) or data not in {"consent:grant:v1", "consent:deny:v1"}:
            return None
        user_id = _integer(sender.get("id"))
        chat_id = _integer(chat.get("id"))
        if user_id is None or chat_id is None or not isinstance(callback_id, str):
            return None
        return ConsentCallback(
            update_id=update_id,
            callback_id=callback_id,
            chat_id=chat_id,
            chat_type=str(chat.get("type", "private")).upper(),
            user_id=user_id,
            message_id=_integer(message.get("message_id")),
            action="GRANT" if data == "consent:grant:v1" else "DENY",
        )

    message = payload.get("message")
    if not isinstance(message, dict):
        return None
    sender = message.get("from")
    chat = message.get("chat")
    if not isinstance(sender, dict) or not isinstance(chat, dict):
        return None
    text = message.get("text") or message.get("caption")
    user_id = _integer(sender.get("id"))
    chat_id = _integer(chat.get("id"))
    message_id = _integer(message.get("message_id"))
    if (
        not isinstance(text, str)
        or user_id is None
        or chat_id is None
        or message_id is None
    ):
        return None
    replied = message.get("reply_to_message")
    reply_text = None
    reply_from_bot = False
    if isinstance(replied, dict):
        candidate = replied.get("text") or replied.get("caption")
        reply_text = candidate if isinstance(candidate, str) else None
        reply_sender = replied.get("from")
        reply_from_bot = isinstance(reply_sender, dict) and reply_sender.get("is_bot") is True
    return InboundMessage(
        update_id=update_id,
        chat_id=chat_id,
        chat_type=str(chat.get("type", "private")).upper(),
        user_id=user_id,
        message_id=message_id,
        text=text[:10_000],
        reply_text=reply_text[:10_000] if reply_text else None,
        reply_from_bot=reply_from_bot,
        from_bot=sender.get("is_bot") is True,
    )


def format_result(result: dict[str, Any]) -> str:
    risk = result.get("risk") if isinstance(result.get("risk"), dict) else {}
    policy = result.get("policy") if isinstance(result.get("policy"), dict) else {}
    score = risk.get("score", result.get("score"))
    level = str(risk.get("level") or result.get("severity") or "UNKNOWN").upper()
    decision = str(policy.get("decision") or result.get("decision") or "PENDING").upper()
    action = result.get("recommended_action")
    recommendation = action.get("message") if isinstance(action, dict) else None
    if not isinstance(recommendation, str):
        recommendation = "Jeda tindakan dan verifikasi melalui kanal resmi yang Anda cari sendiri."
    signals = result.get("signals")
    signal_lines: list[str] = []
    if isinstance(signals, list):
        for item in signals[:6]:
            code = item.get("code") if isinstance(item, dict) else item
            if code:
                signal_lines.append(f"• {html.escape(str(code))}")
    score_text = "tidak tersedia" if score is None else f"{html.escape(str(score))}/100"
    parts = [
        "🛡️ <b>FraudGuard Analysis</b>",
        "",
        f"<b>Risiko:</b> {html.escape(level)} ({score_text})",
        f"<b>Keputusan:</b> {html.escape(decision)}",
    ]
    if signal_lines:
        parts.extend(["", "<b>Red flags:</b>", *signal_lines])
    parts.extend(["", "<b>Rekomendasi:</b>", html.escape(recommendation)])
    trace_id = result.get("trace_id")
    if trace_id:
        parts.extend(["", f"<code>Trace: {html.escape(str(trace_id))}</code>"])
    return "\n".join(parts)[:4000]


class TelegramProcessor:
    def __init__(
        self,
        settings: Settings,
        core: CoreClient,
        api: TelegramApi,
        analyze: Analyze,
    ) -> None:
        self.settings = settings
        self.core = core
        self.api = api
        self.analyze = analyze
        self.windows: dict[str, deque[float]] = defaultdict(deque)
        self.completed: dict[int, float] = {}
        self.pending_delivery: dict[int, tuple[int, str, int | None]] = {}

    def _digest(self, purpose: str, value: object, prefix: str) -> str:
        key = self.settings.telegram_subject_hmac_key.get_secret_value().encode()
        digest = hmac.new(key, f"telegram:{purpose}:{value}".encode(), hashlib.sha256)
        return f"{prefix}_{digest.hexdigest()}"

    def _subject(self, user_id: int) -> str:
        return self._digest("user", user_id, "ch")

    def _event(self, value: object) -> str:
        return self._digest("event", value, "evt")

    def _session(self, subject_ref: str, chat_id: int) -> uuid.UUID:
        chat_ref = self._digest("chat", chat_id, "chat")
        return uuid.uuid5(uuid.NAMESPACE_URL, f"fraudguard:telegram:{subject_ref}:{chat_ref}")

    def _allowed(self, subject_ref: str) -> bool:
        now = time.monotonic()
        window = self.windows[subject_ref]
        while window and window[0] < now - 60:
            window.popleft()
        if len(window) >= self.settings.telegram_rate_limit_per_minute:
            return False
        window.append(now)
        return True

    def _triggered_text(self, message: InboundMessage) -> str | None:
        text = message.text.strip()
        if message.chat_type == "PRIVATE":
            return text
        if message.chat_type not in {"GROUP", "SUPERGROUP"}:
            return None
        username = self.settings.telegram_bot_username.lstrip("@").lower()
        lowered = text.lower()
        command = lowered.startswith(("/cek", "/analisis"))
        mentioned = bool(username) and f"@{username}" in lowered
        if not command and not mentioned and not message.reply_from_bot:
            return None
        if command and message.reply_text:
            return message.reply_text.strip()
        for prefix in ("/cek", "/analisis"):
            if lowered.startswith(prefix):
                text = text[len(prefix) :].lstrip()
                break
        if username:
            text = re.sub(rf"@{re.escape(username)}\b", "", text, flags=re.IGNORECASE)
        return text.strip() or None

    async def _consent_status(self, subject_ref: str) -> str:
        result = await self.core.get_channel_consent("TELEGRAM", subject_ref)
        return str(result["data"].get("status", "UNKNOWN"))

    async def _prompt(self, chat_id: int, reply_to: int | None) -> None:
        await self.api.send_message(
            chat_id,
            (
                "🛡️ <b>Persetujuan FraudGuard</b>\n\n"
                "Saya hanya menganalisis pesan yang Anda kirim atau teruskan secara "
                "sengaja. Saya tidak membaca chat lain. ID Telegram diubah menjadi "
                "referensi pseudonim; jangan kirim OTP, PIN, CVV, password, atau key.\n\n"
                "Setelah setuju, kirim ulang pesan yang ingin dianalisis."
            ),
            reply_to=reply_to,
            reply_markup={
                "inline_keyboard": [
                    [
                        {"text": "✅ Setuju", "callback_data": "consent:grant:v1"},
                        {"text": "❌ Tolak", "callback_data": "consent:deny:v1"},
                    ]
                ]
            },
        )

    async def _update_consent(
        self,
        *,
        subject_ref: str,
        action: str,
        event_value: object,
        chat_type: str,
    ) -> None:
        await self.core.update_channel_consent(
            {
                "channel": "TELEGRAM",
                "subject_ref": subject_ref,
                "action": action,
                "policy_version": self.settings.telegram_consent_policy_version,
                "event_ref": self._event(event_value),
                "chat_type": chat_type,
            }
        )

    async def handle(self, payload: dict[str, Any]) -> dict[str, str]:
        event = parse_update(payload)
        if event is None:
            return {"status": "ignored"}
        now = time.monotonic()
        self.completed = {key: expiry for key, expiry in self.completed.items() if expiry > now}
        if event.update_id in self.completed:
            return {"status": "duplicate"}
        pending = self.pending_delivery.get(event.update_id)
        if pending is not None:
            chat_id, response_text, reply_to = pending
            await self.api.send_message(chat_id, response_text, reply_to=reply_to)
            self.pending_delivery.pop(event.update_id, None)
            self.completed[event.update_id] = now + 3600
            return {"status": "delivery_retried"}
        subject_ref = self._subject(event.user_id)

        if isinstance(event, ConsentCallback):
            await self._update_consent(
                subject_ref=subject_ref,
                action=event.action,
                event_value=event.callback_id,
                chat_type=event.chat_type,
            )
            accepted = event.action == "GRANT"
            await self.api.answer_callback(
                event.callback_id,
                "Persetujuan tersimpan" if accepted else "Analisis dibatalkan",
            )
            await self.api.send_message(
                event.chat_id,
                (
                    "✅ Persetujuan aktif. Kirim ulang pesan mencurigakan untuk dianalisis."
                    if accepted
                    else "Persetujuan ditolak. Tidak ada pesan yang dianalisis."
                ),
                reply_to=event.message_id,
            )
            self.completed[event.update_id] = now + 3600
            return {"status": "consent_updated"}

        if event.from_bot:
            return {"status": "ignored"}
        text = self._triggered_text(event)
        if text is None:
            return {"status": "ignored"}
        command = event.text.strip().lower().split(maxsplit=1)[0].split("@", 1)[0]
        if command == "/privacy":
            await self.api.send_message(
                event.chat_id,
                (
                    "🔐 Bot hanya memproses pesan yang sengaja dikirim, diteruskan, "
                    "atau dipanggil dengan /cek. Raw Telegram ID tidak disimpan di Core."
                ),
                reply_to=event.message_id,
            )
        elif command == "/help":
            await self.api.send_message(
                event.chat_id,
                (
                    "🛡️ <b>Cara memakai FraudGuard</b>\n\n"
                    "Private chat: kirim atau teruskan pesan mencurigakan.\n"
                    "Grup: gunakan <code>/cek pesan</code>, balas pesan dengan "
                    "<code>/cek</code>, atau mention bot.\n"
                    "Perintah: /consent, /privacy, dan /revoke.\n\n"
                    "Jangan kirim OTP, PIN, CVV, password, atau private key."
                ),
                reply_to=event.message_id,
            )
        elif command == "/revoke":
            await self._update_consent(
                subject_ref=subject_ref,
                action="REVOKE",
                event_value=event.update_id,
                chat_type=event.chat_type,
            )
            await self.api.send_message(
                event.chat_id,
                (
                    "Persetujuan dicabut. Pesan berikutnya tidak akan dianalisis "
                    "sebelum Anda setuju lagi."
                ),
                reply_to=event.message_id,
            )
        elif command in {"/start", "/consent"}:
            await self._prompt(event.chat_id, event.message_id)
        else:
            if not self._allowed(subject_ref):
                await self.api.send_message(
                    event.chat_id,
                    "Terlalu banyak permintaan. Tunggu sebentar lalu coba lagi.",
                    reply_to=event.message_id,
                )
                self.completed[event.update_id] = now + 60
                return {"status": "rate_limited"}
            try:
                status = await self._consent_status(subject_ref)
            except CoreError:
                await self.api.send_message(
                    event.chat_id,
                    (
                        "FraudGuard Core belum tersedia. Pesan tidak dianalisis; "
                        "jangan lanjutkan transaksi sampai dapat diverifikasi."
                    ),
                    reply_to=event.message_id,
                )
                return {"status": "core_unavailable"}
            if status != "GRANTED":
                await self._prompt(event.chat_id, event.message_id)
                self.completed[event.update_id] = now + 3600
                return {"status": "consent_required"}
            result = await self.analyze(
                text,
                self._session(subject_ref, event.chat_id),
                {
                    "requested_skill": "fraud-detection:v1",
                    "input_type": "MESSAGE",
                    "channel": "telegram",
                    "consent_policy_version": self.settings.telegram_consent_policy_version,
                },
            )
            response_text = format_result(result)
            self.pending_delivery[event.update_id] = (
                event.chat_id,
                response_text,
                event.message_id,
            )
            await self.api.send_message(event.chat_id, response_text, reply_to=event.message_id)
            self.pending_delivery.pop(event.update_id, None)
        self.completed[event.update_id] = now + 3600
        return {"status": "processed"}
