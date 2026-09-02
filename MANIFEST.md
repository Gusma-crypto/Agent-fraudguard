# Active Manifest

- `src/fraudguard_agent/` — executable agent service
- `tests/` — runtime, Core contract, and security tests
- `Docker/` — development/production container definitions
- `agents/`, `skills/`, `commands/`, `hooks/` — OpenClaw-facing contracts
- `scripts/install_openclaw.sh` — idempotent workspace installer
- `scripts/fraudguard_agent_cli.py` — bounded OpenClaw/terminal communication client
- `skills/skill-creator/SKILL.md` — optional development helper for safe skill creation
- `docs/OPENCLAW-INSTALL.md` — install, credential, usage, and troubleshooting guide
- `api/`, `tools/`, `workflows/`, `evals/` — behavior and evaluation contracts
- `docs/`, `README.md`, `guide_user.md` — active documentation
- `reference/` — inactive historical material only

Risk, policy, database, migrations, incidents, learning, and authoritative audit are not
part of this manifest; they live in `logic-backend-server`.
