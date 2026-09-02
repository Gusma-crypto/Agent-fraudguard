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

## OpenClaw execution

Gunakan `tools/fraudguard-agent chat` dan masukkan field pembayaran ke
`--context-json`; jangan meletakkannya di URL atau log. Pertahankan `session_id` jika
percakapan berlanjut. Jangan fallback ke generic HTTP, shell, atau keputusan pembayaran
lokal ketika CLI/Agent/Core gagal.
