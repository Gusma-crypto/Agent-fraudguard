# FraudGuard AI — Active Product Master

FraudGuard adalah fraud-protection platform dengan dua runtime yang sengaja dipisahkan:

1. `Agent-fraudguard`: conversation, context, reasoning, orchestration, guardrails,
   skill/tool selection, dan user explanation.
2. `logic-backend-server`: identity, tenant scope, risk, policy, protected decisions,
   PostgreSQL persistence, incident/evidence, learning, webhook, dan authoritative audit.

Prinsip final:

> Agent understands and orchestrates. Core decides and records.

Agent tidak boleh memiliki database/risk/policy authority kedua. OpenClaw adalah runtime
portable untuk agent, bukan pengganti Core. V1 memakai satu orchestrator dan skills
fraud detection, payment safety, realtime intervention, serta case investigation.

P0 selesai ketika conversation API menjaga session context, meminta klarifikasi aman,
memilih typed allowlisted tool, mempertahankan trace ID, fail closed, menolak prompt
injection/secret, dan dapat mencapai Core yang deployed. Semua demo memakai data sintetis
atau dimasking.
