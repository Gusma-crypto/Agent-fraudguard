import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
CLI = PROJECT / "scripts" / "fraudguard_agent_cli.py"
INSTALLER = PROJECT / "scripts" / "install_openclaw.sh"


class AgentHandler(BaseHTTPRequestHandler):
    requests: list[dict[str, Any]] = []

    def log_message(self, _format: str, *args: Any) -> None:
        pass

    def respond(self, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        self.requests.append({"method": "GET", "path": self.path})
        self.respond({"status": "healthy"})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length))
        self.requests.append(
            {
                "method": "POST",
                "path": self.path,
                "key": self.headers.get("X-Agent-Key"),
                "body": body,
            }
        )
        self.respond(
            {
                "selected_skill": "fraud-detection",
                "decision": "REVIEW",
                "trace_id": "00000000-0000-0000-0000-000000000001",
            }
        )


def run_cli(*args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_cli_sends_authenticated_structured_chat() -> None:
    AgentHandler.requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), AgentHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    env = {
        **os.environ,
        "FRAUDGUARD_AGENT_URL": f"http://127.0.0.1:{server.server_port}",
        "FRAUDGUARD_AGENT_ACCESS_KEY": "test-agent-key",
    }
    try:
        result = run_cli(
            "chat",
            "--message",
            "Periksa pesan ini",
            "--context-json",
            '{"urgent":true}',
            env=env,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["decision"] == "REVIEW"
    assert AgentHandler.requests == [
        {
            "method": "POST",
            "path": "/agent/v1/chat",
            "key": "test-agent-key",
            "body": {"message": "Periksa pesan ini", "context": {"urgent": True}},
        }
    ]


def test_cli_rejects_non_loopback_plain_http() -> None:
    env = {**os.environ, "FRAUDGUARD_AGENT_URL": "http://agent.example"}
    result = run_cli("health", env=env)
    assert result.returncode == 1
    assert "HTTP hanya diizinkan" in result.stderr


def test_installer_is_idempotent_and_preserves_conflicts(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    command = ["bash", str(INSTALLER), "--workspace", str(workspace)]
    first = subprocess.run(command, capture_output=True, text=True, check=False)
    assert first.returncode == 0, first.stderr
    assert (workspace / "skills/fraud-detection/SKILL.md").is_file()
    assert (workspace / "skills/intelligence-search/SKILL.md").is_file()
    assert (workspace / "skills/social-engineering/SKILL.md").is_file()
    assert (workspace / "skills/malicious-url/SKILL.md").is_file()
    assert not (workspace / "skills/skill-creator").exists()
    bridge = workspace / "tools/fraudguard-agent"
    assert bridge.is_file()
    assert bridge.stat().st_mode & 0o077 == 0

    second = subprocess.run(command, capture_output=True, text=True, check=False)
    assert second.returncode == 0, second.stderr
    assert "already current" in second.stdout

    target = workspace / "skills/fraud-detection/SKILL.md"
    target.write_text("local customization\n", encoding="utf-8")
    conflict = subprocess.run(command, capture_output=True, text=True, check=False)
    assert conflict.returncode == 1
    assert target.read_text(encoding="utf-8") == "local customization\n"

    forced = subprocess.run([*command, "--force"], capture_output=True, text=True, check=False)
    assert forced.returncode == 0, forced.stderr
    backups = list((workspace / ".fraudguard-backups").glob("*/skills/fraud-detection/SKILL.md"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "local customization\n"

    creator_workspace = tmp_path / "creator-workspace"
    creator = subprocess.run(
        [
            "bash",
            str(INSTALLER),
            "--workspace",
            str(creator_workspace),
            "--with-creator",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert creator.returncode == 0, creator.stderr
    assert (creator_workspace / "skills/skill-creator/SKILL.md").is_file()
