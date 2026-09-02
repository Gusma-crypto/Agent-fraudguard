# Architecture

```text
Channel / OpenClaw / Client
          │ X-Agent-Key
          ▼
FraudGuard Agent (single replica + in-memory sessions)
  input guard → planner → typed tool registry → output guard
          │ scoped Core API key + trace/idempotency
          ▼
FraudGuard Core (`logic-backend-server`)
  risk → policy → protected state → PostgreSQL → audit
```

`src/fraudguard_agent` adalah satu-satunya runtime package agent. Session facts memiliki
provenance `USER_CLAIM`, `AGENT_INFERENCE`, atau `CORE_FACT`. Hanya hasil Core boleh
dipresentasikan sebagai decision authoritative.

Fraud analysis memakai action matrix tetap: `ALLOW` berhenti tanpa side effect;
`REVIEW`, `STEP_UP_VERIFY`, dan `TEMPORARY_HOLD` membuat tepat satu intervensi idempotent
di Core. Tindakan eksternal tetap di luar tool allowlist.

Provider V1 adalah deterministic agar berjalan tanpa external model key. Kontrak planner
tetap provider-portable; provider baru tidak boleh memperoleh database, arbitrary HTTP,
shell, atau authority untuk memilih protected outcome.

Session persistence: the current production compose runs one Agent replica and keeps
conversation state in memory with a TTL. Scaling requires a shared Redis-backed store
with TTL and optimistic locking/version checks; sticky routing alone is not a persistence
strategy. Until that adapter exists, `replicas > 1` is unsupported.

The deterministic planner includes bounded fraud/payment indicators for English,
Indonesian, Malay, Spanish, French, and German. This improves routing only; unsupported
response languages fall back to English. Full international coverage requires a validated
language-model/provider adapter with structured output and Core-side authority unchanged.
