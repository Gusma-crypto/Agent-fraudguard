from __future__ import annotations

import asyncio
import hashlib
import hmac
import html
import logging
import re
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from .config import Settings
from .core_client import CoreClient, CoreError

logger = logging.getLogger(__name__)

Analyze = Callable[[str, uuid.UUID, dict[str, Any]], Awaitable[dict[str, Any]]]

SKILL_COMMANDS = {
    "/cek": "fraud-detection:v1",
    "/analisis": "fraud-detection:v1",
    "/bayar": "safety-payment:v1",
    "/intervensi": "realtime-intervention:v1",
    "/sosial": "social-engineering:v1",
    "/intelijen": "intelligence-search:v1",
    "/cek_nomor": "intelligence-search:v1",
    "/cek_domain": "intelligence-search:v1",
    "/safety": "safety-payment:v1",
}

COMMAND_INPUT_TYPES = {
    "/bayar": "TRANSACTION",
    "/safety": "TRANSACTION",
    "/cek_nomor": "PHONE",
    "/cek_domain": "DOMAIN",
}

SKILL_PROGRESS_LABELS = {
    "fraud-detection:v1": "memeriksa indikasi fraud",
    "safety-payment:v1": "memeriksa keamanan pembayaran",
    "realtime-intervention:v1": "menilai kebutuhan intervensi",
    "social-engineering:v1": "memeriksa pola manipulasi",
    "intelligence-search:v1": "mencari dan memverifikasi intelligence",
}

RISK_LABELS = {
    "LOW": "Rendah",
    "MEDIUM": "Sedang",
    "HIGH": "Tinggi",
    "CRITICAL": "Kritis",
    "UNKNOWN": "Belum dapat ditentukan",
}

DECISION_LABELS = {
    "ALLOW": "Tidak ada pembatasan dari policy",
    "REVIEW": "Perlu ditinjau",
    "STEP_UP_VERIFY": "Perlu verifikasi tambahan",
    "TEMPORARY_HOLD": "Jeda sementara",
    "PENDING": "Belum ada keputusan final",
}

ACTION_MESSAGES = {
    "ALLOW": "Tidak ada pemblokiran otomatis. Tetap periksa melalui kanal resmi sebelum bertindak.",
    "PROCEED_WITH_CAUTION": "Lanjutkan hanya setelah melakukan pemeriksaan biasa.",
    "REVIEW_REQUIRED": "Tunda tindakan dan periksa kembali melalui kanal resmi.",
    "VERIFY_OFFICIAL_CHANNEL": (
        "Verifikasi melalui kanal resmi yang Anda cari sendiri sebelum melanjutkan."
    ),
    "DO_NOT_PROCEED": "Jangan lanjutkan transaksi sampai risikonya terverifikasi.",
}

SIGNAL_LABELS = {
    "IMPERSONATION": "Mengaku sebagai pihak atau merek tertentu",
    "PRIZE_SCAM": "Iming-iming hadiah",
    "PAYMENT_REQUEST": "Meminta pembayaran atau transfer",
    "URGENCY": "Mendesak agar segera bertindak",
    "CREDENTIAL_REQUEST": "Meminta informasi rahasia",
    "OTP_REQUEST": "Meminta kode OTP",
    "NEW_RECIPIENT": "Penerima pembayaran baru",
    "THIRD_PARTY_INSTRUCTION": "Instruksi pembayaran dari pihak lain",
    "GOVERNMENT_AID_LURE": "Iming-iming bantuan sosial atau program pemerintah",
    "URL_SHORTENER": "Tautan pendek menyembunyikan alamat tujuan",
    "OFF_PLATFORM_REDIRECT": "Diarahkan ke Telegram/WhatsApp di luar kanal resmi",
    "LINK_CLICK_INSTRUCTION": "Diminta membuka atau mendaftar melalui tautan",
    "SUSPICIOUS_URL": "Tautan mendapat indikator mencurigakan",
    "URL_UNREACHABLE": "Provider terakhir mencatat tautan tidak dapat diakses",
}


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
    ) -> int | None: ...

    async def edit_message(self, chat_id: int, message_id: int, text: str) -> None: ...

    async def send_chat_action(self, chat_id: int, action: str = "typing") -> None: ...

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

    async def _call(self, method: str, payload: dict[str, Any]) -> Any:
        try:
            response = await self.client.post(f"/{method}", json=payload)
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise TelegramError("Telegram Bot API tidak dapat dihubungi") from exc
        if response.is_error or not isinstance(body, dict) or body.get("ok") is not True:
            raise TelegramError("Telegram Bot API menolak respons bot")
        return body.get("result")

    async def send_message(
        self,
        chat_id: int,
        text: str,
        *,
        reply_to: int | None = None,
        reply_markup: dict[str, Any] | None = None,
    ) -> int | None:
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
        result = await self._call("sendMessage", payload)
        if isinstance(result, dict):
            message_id = result.get("message_id")
            if isinstance(message_id, int) and not isinstance(message_id, bool):
                return message_id
        return None

    async def edit_message(self, chat_id: int, message_id: int, text: str) -> None:
        await self._call(
            "editMessageText",
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text[:4096],
                "parse_mode": "HTML",
                "link_preview_options": {"is_disabled": True},
            },
        )

    async def send_chat_action(self, chat_id: int, action: str = "typing") -> None:
        await self._call("sendChatAction", {"chat_id": chat_id, "action": action})

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
    result_status = str(result.get("status") or "").lower()
    trace_id = result.get("trace_id")
    if result_status in {"failed", "error"} or (
        trace_id is None and level == "UNKNOWN" and decision == "PENDING"
    ):
        return (
            "🛡️ <b>Pemeriksaan belum berhasil</b>\n\n"
            "Saya belum memperoleh hasil yang dapat dipercaya dari FraudGuard Core. "
            "Ini <b>bukan</b> berarti target tersebut aman atau berbahaya.\n\n"
            "Silakan coba kembali sebentar lagi. Sambil menunggu, jangan kirim uang atau "
            "informasi rahasia dan lakukan verifikasi melalui kanal resmi yang Anda cari sendiri."
        )
    action = result.get("recommended_action")
    action_code = str(action.get("code") or "") if isinstance(action, dict) else ""
    recommendation = ACTION_MESSAGES.get(action_code)
    if recommendation is None and isinstance(action, dict):
        recommendation = action.get("message")
    if not isinstance(recommendation, str):
        recommendation = "Jeda tindakan dan verifikasi melalui kanal resmi yang Anda cari sendiri."
    signals = result.get("signals")
    signal_lines: list[str] = []
    if isinstance(signals, list):
        for item in signals[:6]:
            code = item.get("code") if isinstance(item, dict) else item
            if code:
                raw_code = str(code).upper()
                label = SIGNAL_LABELS.get(raw_code, raw_code.replace("_", " ").title())
                signal_lines.append(f"• {html.escape(label)}")
    risk_label = RISK_LABELS.get(level, level.replace("_", " ").title())
    risk_text = (
        f"{risk_label} ({level})"
        if score is None
        else f"{risk_label} ({level}) — {html.escape(str(score))}/100"
    )
    decision_label = DECISION_LABELS.get(decision, decision.replace("_", " ").title())
    parts = [
        "🛡️ <b>Hasil pemeriksaan FraudGuard</b>",
        "",
        f"<b>Tingkat risiko:</b> {html.escape(risk_text)}",
        f"<b>Keputusan:</b> {html.escape(decision_label)} "
        f"(<code>{html.escape(decision)}</code>)",
    ]
    if signal_lines:
        parts.extend(["", "<b>Red flags:</b>", *signal_lines])
    raw_signal_codes = {
        str(item.get("code") if isinstance(item, dict) else item).upper()
        for item in signals
    } if isinstance(signals, list) else set()
    if "URL_UNREACHABLE" in raw_signal_codes:
        parts.extend(
            [
                "",
                "<b>Status tautan:</b> Provider terakhir mencatat respons gagal. "
                "Status ini bukan bukti tunggal penipuan dan dapat berubah.",
            ]
        )
    elif "URL_SHORTENER" in raw_signal_codes:
        parts.extend(
            [
                "",
                "<b>Status tautan:</b> Shortlink menyembunyikan alamat tujuan. "
                "Tujuan akhir dan status aksesnya belum dapat dipastikan dari shortlink ini.",
            ]
        )
    parts.extend(["", "<b>Rekomendasi:</b>", html.escape(recommendation)])
    explanation = result.get("message")
    if isinstance(explanation, str) and explanation.strip():
        compact_explanation = " ".join(explanation.split())[:900]
        parts.extend(
            [
                "",
                "<b>Penjelasan OpenClaw berdasarkan hasil Core:</b>",
                html.escape(compact_explanation),
            ]
        )
    summary = result.get("summary")
    if isinstance(summary, dict):
        evidence_found = summary.get("evidence_found")
        sources_successful = summary.get("sources_successful")
        if evidence_found is not None or sources_successful is not None:
            parts.extend(["", "<b>Ringkasan intelligence:</b>"])
            if evidence_found is not None:
                parts.append(f"• Bukti ditemukan: {html.escape(str(evidence_found))}")
            if sources_successful is not None:
                parts.append(f"• Sumber berhasil: {html.escape(str(sources_successful))}")
    if trace_id:
        parts.extend(["", f"<code>Trace: {html.escape(str(trace_id))}</code>"])
    intervention_id = result.get("intervention_id")
    if intervention_id:
        parts.append(f"<code>Intervention: {html.escape(str(intervention_id))}</code>")
    return "\n".join(parts)[:4000]


class TelegramProcessor:
    TYPING_REFRESH_SECONDS = 3.0

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
        self.active_interventions: dict[uuid.UUID, tuple[str, float]] = {}

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
        command = text.lower().split(maxsplit=1)[0].split("@", 1)[0]
        analysis_command = command in SKILL_COMMANDS
        if message.chat_type == "PRIVATE":
            if analysis_command:
                if message.reply_text:
                    return message.reply_text.strip() or None
                parts = text.split(maxsplit=1)
                return parts[1].strip() if len(parts) == 2 else None
            return text
        if message.chat_type not in {"GROUP", "SUPERGROUP"}:
            return None
        username = self.settings.telegram_bot_username.lstrip("@").lower()
        lowered = text.lower()
        mentioned = bool(username) and f"@{username}" in lowered
        if not analysis_command and not mentioned and not message.reply_from_bot:
            return None
        if analysis_command and message.reply_text:
            return message.reply_text.strip()
        if analysis_command:
            parts = text.split(maxsplit=1)
            text = parts[1] if len(parts) == 2 else ""
        if username:
            text = re.sub(rf"@{re.escape(username)}\b", "", text, flags=re.IGNORECASE)
        return text.strip() or None

    def _requested_skill(self, message: InboundMessage) -> str:
        command = message.text.strip().lower().split(maxsplit=1)[0].split("@", 1)[0]
        return SKILL_COMMANDS.get(command, "fraud-detection:v1")

    def _input_type(self, message: InboundMessage) -> str:
        command = message.text.strip().lower().split(maxsplit=1)[0].split("@", 1)[0]
        return COMMAND_INPUT_TYPES.get(command, "MESSAGE")

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

    async def _keep_typing(self, chat_id: int) -> None:
        while True:
            await asyncio.sleep(self.TYPING_REFRESH_SECONDS)
            try:
                await self.api.send_chat_action(chat_id)
            except TelegramError:
                # A short Telegram API/network failure must not permanently
                # disable the indicator for a long-running analysis.
                logger.warning("Telegram typing indicator refresh failed; retrying")

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
        command = event.text.strip().lower().split(maxsplit=1)[0].split("@", 1)[0]
        text = self._triggered_text(event)
        if text is None:
            if command in SKILL_COMMANDS:
                await self.api.send_message(
                    event.chat_id,
                    (
                        f"Kirim <code>{html.escape(command)} &lt;pesan/konteks&gt;</code> "
                        f"atau reply pesan target dengan <code>{html.escape(command)}</code>."
                    ),
                    reply_to=event.message_id,
                )
                self.completed[event.update_id] = now + 3600
                return {"status": "input_required"}
            return {"status": "ignored"}
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
                    "Skill: /cek, /bayar, /intervensi, /sosial, dan /intelijen.\n"
                    "Privasi: /consent, /privacy, dan /revoke.\n\n"
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
            requested_skill = self._requested_skill(event)
            session_id = self._session(subject_ref, event.chat_id)
            self.active_interventions = {
                key: value for key, value in self.active_interventions.items() if value[1] > now
            }
            active_intervention = self.active_interventions.get(session_id)
            if requested_skill == "realtime-intervention:v1" and active_intervention is None:
                await self.api.send_message(
                    event.chat_id,
                    (
                        "Belum ada intervention ID aktif dari FraudGuard Core. Jalankan "
                        "<code>/bayar &lt;jumlah, penerima, konteks&gt;</code> lebih dahulu, "
                        "lalu lanjutkan <code>/intervensi &lt;jawaban&gt;</code>."
                    ),
                    reply_to=event.message_id,
                )
                self.completed[event.update_id] = now + 3600
                return {"status": "intervention_required"}
            progress_message_id = await self.api.send_message(
                event.chat_id,
                (
                    "⏳ <b>Analisis sedang berlangsung</b>\n\n"
                    f"FraudGuard sedang {SKILL_PROGRESS_LABELS[requested_skill]}. "
                    "Mohon tunggu, hasil akan tampil di pesan ini."
                ),
                reply_to=event.message_id,
            )
            typing_task: asyncio.Task[None] | None = None
            try:
                await self.api.send_chat_action(event.chat_id)
            except TelegramError:
                logger.warning("Telegram typing indicator start failed; refresh will retry")
            typing_task = asyncio.create_task(self._keep_typing(event.chat_id))
            logger.info("Telegram typing indicator started")
            try:
                result = await self.analyze(
                    text,
                    session_id,
                    {
                        "requested_skill": requested_skill,
                        "input_type": self._input_type(event),
                        "channel": "telegram",
                        "consent_policy_version": self.settings.telegram_consent_policy_version,
                        "trusted_intervention_id": (
                            active_intervention[0] if active_intervention is not None else None
                        ),
                        "trusted_external_payment_id": (
                            self._event(event.update_id)
                            if requested_skill == "safety-payment:v1"
                            else None
                        ),
                    },
                )
            finally:
                if typing_task is not None:
                    typing_task.cancel()
                    with suppress(asyncio.CancelledError):
                        await typing_task
                    logger.info("Telegram typing indicator stopped")
            intervention_id = result.get("intervention_id")
            try:
                normalized_intervention_id = str(uuid.UUID(str(intervention_id)))
            except (ValueError, TypeError, AttributeError):
                normalized_intervention_id = None
            if normalized_intervention_id is not None:
                self.active_interventions[session_id] = (
                    normalized_intervention_id,
                    now + 1800,
                )
            response_text = format_result(result)
            self.pending_delivery[event.update_id] = (
                event.chat_id,
                response_text,
                event.message_id,
            )
            if progress_message_id is not None:
                await self.api.edit_message(event.chat_id, progress_message_id, response_text)
            else:
                await self.api.send_message(
                    event.chat_id,
                    response_text,
                    reply_to=event.message_id,
                )
            self.pending_delivery.pop(event.update_id, None)
        self.completed[event.update_id] = now + 3600
        return {"status": "processed"}
