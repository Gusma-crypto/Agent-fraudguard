#!/usr/bin/env python3
"""Bounded CLI bridge from OpenClaw to FraudGuard Agent."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

DEFAULT_URL = "http://127.0.0.1:3000"
DEFAULT_KEY_FILE = Path.home() / ".config" / "fraudguard-agent" / "access.key"
MAX_RESPONSE_BYTES = 1_048_576


class CliError(RuntimeError):
    pass


def agent_url() -> str:
    value = os.environ.get("FRAUDGUARD_AGENT_URL", DEFAULT_URL).rstrip("/")
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise CliError("FRAUDGUARD_AGENT_URL harus berupa URL HTTP(S) yang valid")
    loopback = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    if parsed.scheme == "http" and not loopback:
        raise CliError("HTTP hanya diizinkan untuk endpoint loopback; gunakan HTTPS")
    if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
        raise CliError("FRAUDGUARD_AGENT_URL hanya boleh berisi origin tanpa path/query")
    return value


def access_key() -> str | None:
    from_env = os.environ.get("FRAUDGUARD_AGENT_ACCESS_KEY")
    if from_env:
        return from_env.strip()
    configured = os.environ.get("FRAUDGUARD_AGENT_KEY_FILE")
    path = Path(configured).expanduser() if configured else DEFAULT_KEY_FILE
    if not path.exists():
        return None
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise CliError(f"permission key file harus 600 atau lebih ketat: {path}")
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise CliError(f"key file kosong: {path}")
    return value


def parse_json_object(raw: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CliError(f"{label} bukan JSON valid: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise CliError(f"{label} harus berupa JSON object")
    return value


def request(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout: float,
) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    key = access_key()
    if key:
        headers["X-Agent-Key"] = key
    body = None
    if payload is not None:
        body = json.dumps(payload, separators=(",", ":")).encode()
        headers["Content-Type"] = "application/json"
    target = f"{agent_url()}{path}"
    req = urllib.request.Request(target, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raw = exc.read(MAX_RESPONSE_BYTES + 1)
        detail = decode_response(raw).get("detail", exc.reason)
        raise CliError(f"FraudGuard Agent menolak request ({exc.code}): {detail}") from exc
    except urllib.error.URLError as exc:
        raise CliError(f"FraudGuard Agent tidak dapat dihubungi: {exc.reason}") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise CliError("respons FraudGuard Agent melewati batas 1 MiB")
    return decode_response(raw)


def decode_response(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CliError("respons FraudGuard Agent bukan JSON valid") from exc
    if not isinstance(value, dict):
        raise CliError("respons FraudGuard Agent harus berupa JSON object")
    return value


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="fraudguard-agent",
        description="CLI komunikasi terikat untuk FraudGuard AI Agent",
    )
    root.add_argument("--timeout", type=float, default=15, help="timeout request (default: 15s)")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("health", help="periksa proses agent")
    commands.add_parser("ready", help="periksa koneksi agent ke Core")
    commands.add_parser("tools", help="lihat typed tool allowlist")

    session = commands.add_parser("session-create", help="buat conversation session")
    session.add_argument(
        "--channel",
        default="openclaw",
        choices=("web", "api", "openclaw", "mobile", "whatsapp"),
    )

    chat = commands.add_parser("chat", help="kirim turn ke agent")
    chat.add_argument("--message", required=True, help="pesan pengguna")
    chat.add_argument("--session-id", help="UUID session dari respons sebelumnya")
    chat.add_argument("--context-json", default="{}", help="context non-sensitif")
    return root


def run(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.timeout <= 0 or args.timeout > 60:
        raise CliError("timeout harus lebih dari 0 dan maksimal 60 detik")
    if args.command in {"health", "ready"}:
        result = request("GET", f"/{args.command}", timeout=args.timeout)
    elif args.command == "tools":
        result = request("GET", "/agent/v1/tools", timeout=args.timeout)
    elif args.command == "session-create":
        result = request(
            "POST",
            "/agent/v1/sessions",
            {"channel": args.channel},
            timeout=args.timeout,
        )
    else:
        context = parse_json_object(args.context_json, "--context-json")
        payload: dict[str, Any] = {"message": args.message, "context": context}
        if args.session_id:
            try:
                payload["session_id"] = str(uuid.UUID(args.session_id))
            except ValueError as exc:
                raise CliError("--session-id harus berupa UUID valid") from exc
        result = request("POST", "/agent/v1/chat", payload, timeout=args.timeout)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    try:
        return run()
    except (CliError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
