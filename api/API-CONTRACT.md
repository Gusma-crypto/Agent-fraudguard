# FraudGuard Agent API Contract

Base path: `/agent/v1`. Ini berbeda dari Core `/api/v1`.

## Conversation

- `POST /sessions` dengan `{ "channel": "web" }`
- `GET /sessions/{session_id}`
- `DELETE /sessions/{session_id}`
- `POST /chat` dengan `session_id`, `message`, dan optional non-sensitive `context`
- `GET /tools` untuk inventory metadata allowlisted tools

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

Core success envelope wajib memiliki `data` dan `meta.trace_id`. Protected workflow
fail closed pada timeout, response malformed, atau Core rejection.

Respons chat menyertakan `actions[]` (`action`, `status`, `resource_id`) agar client dapat
membedakan hasil analisis dari side effect protektif yang benar-benar tercatat di Core.
Respons juga menyertakan `language`. Runtime mendeteksi `en`, `id`, atau `ms`, menerima
optional hint `context.language`/`context.locale`, dan memakai English sebagai fallback.
Nilai decision, severity, reason code, action, dan trace Core tidak diterjemahkan.
