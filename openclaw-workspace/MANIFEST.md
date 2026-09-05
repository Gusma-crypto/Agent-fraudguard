# FraudGuard OpenClaw Runtime Manifest

Managed root files:

- `AGENTS.md`
- `SOUL.md`
- `IDENTITY.md`
- `TOOLS.md`
- `MANIFEST.md`
- `USER.md`
- `HEARTBEAT.md`

Managed production skills:

- `skills/fraud-detection/SKILL.md`
- `skills/safety-payment/SKILL.md`
- `skills/realtime-intervention/SKILL.md`
- `skills/social-engineering/SKILL.md`
- `skills/intelligence-search/SKILL.md`

Managed executable:

- `tools/fraudguard-agent`

Managed demo runbook:

- `docs/demo-telegram-intervention-flow.md`

`malicious-url` is not an active runtime skill. Suspicious URL journeys belong to
`fraud-detection`; explicit URL/domain reputation lookup belongs to
`intelligence-search`.

The installer never manages `MEMORY.md`, `memory/`, OpenClaw credentials, provider keys,
Gateway configuration, or user-created files.
