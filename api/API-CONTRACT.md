# FraudGuard Agent API Contract

Base path: `/agent/v1`. Ini berbeda dari Core `/api/v1`.

## Conversation

- Public frontend traffic terminates at the OpenClaw Bridge on port `3100`.
- `POST /chat` forwards the turn to private OpenClaw `POST /v1/responses`; OpenClaw is
  the only runtime that selects and sequences skills on this route.
- `POST /sessions` dengan `{ "channel": "web" }`
- `GET /sessions/{session_id}`
- `DELETE /sessions/{session_id}`
- `POST /chat` dengan `session_id`, `message`, dan optional non-sensitive `context`
- `GET /tools` untuk inventory metadata allowlisted tools

The public response includes `orchestrator: "openclaw"` and a stable `session_id`.
The browser may send only allowlisted `requested_skill` and `input_type` routing hints;
unknown values are reduced to automatic routing and `MESSAGE`.

Jika `AGENT_ACCESS_KEY` dikonfigurasi, semua endpoint agent memerlukan `X-Agent-Key`.
`tenant_id` dan `application_id` tidak diterima dari chat context.

## Core boundary

Typed tools memetakan ke endpoint `logic-backend-server`:

- `fraud_analyze` → `POST /api/v1/fraud/analyze`
- `create_assessment` → `POST /api/v1/assessments`
- `ingest_event` → `POST /api/v1/events`
- `safety_payment` → `POST /api/v1/payments/check`
- `create_intervention` → `POST /api/v1/interventions` dengan `Idempotency-Key`
- `submit_intervention_response` → intervention response endpoint
- incident, trace, audit, dan capability read tools

OpenClaw workspace skills invoke one typed operation through:

```text
fraudguard-agent tool-execute --name <allowlisted-tool> --arguments-json '<object>'
```

For frontend OpenResponses sessions, Bridge supplies the same schemas as client function
tools and executes returned function calls against Core. This works without sandbox
network access and keeps OpenClaw as the planner. The loopback tool adapter on port `3000`
is a TUI/admin fallback; its legacy `/agent/v1/chat` route is not exposed by Caddy and
must not be used by OpenClaw skills, preventing a second planner.

Core success envelope wajib memiliki `data` dan `meta.trace_id`. Protected workflow
fail closed pada timeout, response malformed, atau Core rejection.

Respons chat menyertakan `actions[]` (`action`, `status`, `resource_id`) agar client dapat
membedakan hasil analisis dari side effect protektif yang benar-benar tercatat di Core.
Respons juga menyertakan `language`. Runtime mendeteksi `en`, `id`, atau `ms`, menerima
optional hint `context.language`/`context.locale`, dan memakai English sebagai fallback.
Nilai decision, severity, reason code, action, dan trace Core tidak diterjemahkan.
