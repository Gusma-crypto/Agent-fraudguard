# Agent Commands

Command templates send natural-language turns to `/agent/v1/chat`. They never call Core
with arbitrary URLs and never supply risk scores, policy decisions, or tenant IDs.
Pada OpenClaw, turn dikirim melalui `tools/fraudguard-agent`; lihat
`../docs/OPENCLAW-INSTALL.md`.

- `fraud-check.md`: suspected scam narrative
- `payment-check.md`: structured non-sensitive payment context
- `incident-review.md`: trusted incident ID lookup
- `golden-demo.md`: synthetic end-to-end scenario
