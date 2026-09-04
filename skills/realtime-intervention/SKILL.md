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

Skill ini bukan deteksi awal dan bukan payment check. Tanpa `intervention_id` terpercaya,
kembali ke skill yang sesuai atau minta pengguna memulai analisis/pemeriksaan pembayaran.

## OpenClaw execution

Untuk request OpenResponses frontend, gunakan function tool
`submit_intervention_response` dari Bridge. Pada TUI/admin tanpa client tool, gunakan
`tools/fraudguard-agent tool-execute --name submit_intervention_response`
dengan `--arguments-json <json>` yang memuat `intervention_id`, `result`, dan `status`. Jangan memanggil
subcommand `chat`. Hanya gunakan ID dari workflow aktif. Stop dan eskalasi bila CLI, tool
adapter, atau Core menolak respons; jangan mengulang final response dengan ID baru.
