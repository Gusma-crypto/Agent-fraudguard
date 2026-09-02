# FraudGuard Orchestrator

Satu orchestrator menangani loop:

```text
input guard → intent/context → plan → typed tool → Core decision
→ authorized protective action → explain/stop
```

Orchestrator menyimpan session context non-authoritative, membedakan `USER_CLAIM`,
`AGENT_INFERENCE`, dan `CORE_FACT`, meneruskan trace ID, membatasi turn/tool budget,
serta menghentikan hasil tool berulang. Untuk fraud decision selain `ALLOW`, orchestrator
mencatat tepat satu intervensi protektif di Core. Ia tidak menghitung score, mengubah
policy, atau mengeksekusi enforcement pada sistem eksternal.

Runtime awal adalah FastAPI/native deterministic dan portable ke OpenClaw. OpenClaw
tetap hanya menerima typed tool allowlist; Core tetap final authority.
