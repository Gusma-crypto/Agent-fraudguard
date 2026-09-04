from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.parse import urlparse

import httpx

from .config import Settings, get_settings


def webhook_payload(settings: Settings, url: str) -> dict[str, Any]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Telegram webhook URL must be an absolute HTTPS URL")
    return {
        "url": url.rstrip("/"),
        "secret_token": settings.telegram_webhook_secret.get_secret_value(),
        "allowed_updates": ["message", "callback_query"],
        "drop_pending_updates": False,
    }


def telegram_call(settings: Settings, method: str, payload: dict[str, Any]) -> Any:
    token = settings.telegram_bot_token.get_secret_value()
    try:
        response = httpx.post(
            f"https://api.telegram.org/bot{token}/{method}",
            json=payload,
            timeout=15,
            follow_redirects=False,
        )
        body = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise RuntimeError("Telegram Bot API is unavailable") from exc
    if response.is_error or not isinstance(body, dict) or body.get("ok") is not True:
        description = body.get("description") if isinstance(body, dict) else None
        raise RuntimeError(str(description or "Telegram Bot API rejected the request"))
    return body.get("result")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Manage the FraudGuard Telegram webhook")
    commands = root.add_subparsers(dest="command", required=True)
    set_command = commands.add_parser("set", help="Register the HTTPS webhook")
    set_command.add_argument("--url", required=True)
    commands.add_parser("info", help="Show Telegram webhook status")
    commands.add_parser("delete", help="Remove the registered webhook")
    return root


def main() -> int:
    args = parser().parse_args()
    settings = get_settings()
    if not settings.telegram_enabled:
        print("TELEGRAM_ENABLED must be true", file=sys.stderr)
        return 2
    try:
        if args.command == "set":
            result = telegram_call(
                settings,
                "setWebhook",
                webhook_payload(settings, args.url),
            )
        elif args.command == "delete":
            result = telegram_call(
                settings,
                "deleteWebhook",
                {"drop_pending_updates": False},
            )
        else:
            result = telegram_call(settings, "getWebhookInfo", {})
    except (RuntimeError, ValueError) as exc:
        print(f"Webhook operation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
