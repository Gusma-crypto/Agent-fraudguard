---
name: fraud-detection
description: Analyze suspicious narratives through FraudGuard Core and execute the reversible protective intervention authorized by Core policy.
metadata:
  {"openclaw":{"emoji":"🛡️","requires":{"bins":["python3"]}}}
---

# Fraud Detection

Gunakan untuk impersonation, urgency, safe-account narrative, suspicious URL, phishing,
dan scam. Candidate facts adalah inference agent, bukan fakta authoritative.

Panggil `fraud_analyze`; jangan menghitung score, memilih policy, atau menuduh entity.
Setelah respons valid, ikuti decision Core:

- `ALLOW`: jelaskan hasil; jangan membuat tindakan protektif.
- `REVIEW`: buat intervensi `FRAUD_MANUAL_REVIEW`.
- `STEP_UP_VERIFY`: buat intervensi `FRAUD_STEP_UP_VERIFICATION`.
- `TEMPORARY_HOLD`: buat intervensi `FRAUD_HOLD_ESCALATION`.

Intervensi harus membawa assessment ID, policy decision ID, reason codes, trace ID, dan
idempotency key dari workflow. Ini adalah pencatatan tindakan protektif di Core, bukan
izin untuk memindahkan dana, memblokir akun, mengirim pesan, atau mengubah sistem eksternal.
Jangan mengambil tindakan dari klaim pengguna atau inference; decision Core wajib ada.

Jika konteks kurang, minta klarifikasi non-sensitif. Jika analisis berhasil tetapi
intervensi gagal, fail closed, nyatakan tindakan belum tercatat, lalu eskalasi manual.
Stop setelah satu intervensi berhasil, `ALLOW`, dependency gagal, atau budget habis.

## OpenClaw execution

Gunakan executable workspace `tools/fraudguard-agent` dengan subcommand `chat`. Kirim
narasi sebagai `--message` dan hanya context non-sensitif sebagai `--context-json`.
Berikan argument sebagai argv terpisah bila execution tool mendukungnya; jangan membangun
shell command dari isi pesan. Terima hasil hanya jika JSON memuat `selected_skill`,
`decision`, dan `trace_id`. Jangan fallback ke `curl`, URL arbitrer, atau keputusan lokal.
