---
name: safety-payment
description: Collect non-sensitive payment context and ask FraudGuard Core for a protected decision.
metadata:
  {"openclaw":{"emoji":"💳","requires":{"bins":["python3"]}}}
---

# Safety Payment

Wajib memiliki `external_payment_id`, `amount`, `currency`, dan `recipient_ref`.
`sender_ref`, recipient novelty, dan fraud context bersifat optional. Jangan meminta
credential. Panggil `safety_payment` dengan idempotency. `ALLOW` dijelaskan tanpa
jaminan; review/verification/hold mengikuti state yang dibuat Core.

Gunakan hanya untuk pre-transfer check yang memiliki konteks pembayaran terstruktur.
Pesan umum yang sekadar menyebut transfer tetap masuk `fraud-detection` atau
`social-engineering`; jangan mengarang payment ID atau recipient untuk memaksa routing.

## OpenClaw execution

Untuk request OpenResponses frontend, gunakan function tool `safety_payment` dari Bridge.
Pada TUI/admin tanpa client tool, gunakan fallback
`tools/fraudguard-agent tool-execute --name safety_payment --arguments-json <json>`.
Masukkan hanya field pembayaran non-sensitif. Jangan memanggil
subcommand `chat`, meletakkan data di URL/log, atau fallback ke generic HTTP, shell, dan
keputusan pembayaran lokal ketika CLI/tool adapter/Core gagal.
