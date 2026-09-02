---
name: realtime-intervention
description: Continue only a Core-authorized verification or intervention workflow.
metadata:
  {"openclaw":{"emoji":"🚨","requires":{"bins":["python3"]}}}
---

# Realtime Intervention

Gunakan setelah Core mengembalikan intervention ID atau ketika client memberikan ID
terpercaya dari workflow aktif. Jangan membuat protected state berdasarkan inference
agent. Jangan meminta password, PIN, OTP, CVV, token, atau full account number.
Submit respons terstruktur ke Core dan tampilkan state authoritative yang dikembalikan.

## OpenClaw execution

Gunakan `tools/fraudguard-agent chat --session-id <uuid>` dengan `intervention_id`,
`intervention_result`, dan optional `intervention_status` pada `--context-json`. Hanya
gunakan ID dari workflow aktif. Stop dan eskalasi bila CLI, Agent, atau Core menolak
respons; jangan mengulang final response dengan ID baru.
