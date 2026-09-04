# TOOLS.md - Runtime Boundary

## Preferred browser path

The FraudGuard OpenClaw Bridge supplies typed client function tools. Use only tools
allowed by the selected skill:

- `fraud_analyze`: Core fraud assessment for typed non-sensitive context.
- `intelligence_lookup`: local-first entity lookup and bounded provider discovery.
- `safety_payment`: idempotent payment safety check.
- `submit_intervention_response`: continue a trusted active intervention.

Core may expose additional internal operations, but they are unavailable unless the
Bridge and selected skill explicitly allow them.

## TUI/admin fallback

When client function tools are absent, invoke only:

```text
tools/fraudguard-agent tool-execute --name <allowlisted-name> --arguments-json <object>
```

Do not call the CLI `chat` subcommand from a skill; that would create a second planner.
Do not fall back to `curl`, generic HTTP, provider APIs, arbitrary shell, SQL, or direct
database access. Credentials are injected outside the workspace through environment or
a permission-600 key file and must never enter prompts or responses.

