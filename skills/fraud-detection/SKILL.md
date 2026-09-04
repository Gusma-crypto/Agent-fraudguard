---
name: fraud-detection
description: Analyze suspicious narratives through FraudGuard Core and explain the reversible protection authorized by Core policy.
metadata:
  {"openclaw":{"emoji":"🛡️","requires":{"bins":["python3"]}}}
---

# Fraud Detection

Gunakan untuk impersonation, urgency, safe-account narrative, suspicious URL, phishing,
permintaan OTP/password/PIN/CVV, dan scam. Candidate facts adalah inference agent, bukan
fakta authoritative. Jangan meminta atau meneruskan nilai credential; hanya teruskan
indikator boolean `credential_request` yang diekstrak Agent.

Ini adalah jalur umum untuk pesan dengan indikator campuran dan seluruh journey URL
mencurigakan (klik, login, formulir, OTP). Jika permintaan hanya berupa lookup reputasi
entity, gunakan `intelligence-search`. Jika narasi utamanya coercion/impersonation/prize,
gunakan `social-engineering`. Pilih satu skill utama; jangan menjalankan ketiganya untuk
input yang sama tanpa kebutuhan tool berbeda yang eksplisit.

Panggil `fraud_analyze`; jangan menghitung score, memilih policy, atau menuduh entity.
Setelah respons valid, jelaskan decision Core:

- `ALLOW`: jelaskan hasil; jangan membuat tindakan protektif.
- `REVIEW`: sarankan review sesuai output Core.
- `STEP_UP_VERIFY`: tampilkan verifikasi tambahan sesuai output Core.
- `TEMPORARY_HOLD`: minta pengguna menjeda transaksi sesuai output Core.

Keputusan, score, severity, dan status dari Core harus ditampilkan tanpa diubah. Jangan
mengganti `ALLOW` menjadi vonis fraud/scam, jangan menyatakan kepastian seperti "100%
penipuan", dan jangan menciptakan score sendiri. Saran universal seperti tidak membagikan
OTP boleh diberikan sebagai pencegahan, tetapi harus jelas terpisah dari keputusan Core.
Jika keputusan Core tampak tidak konsisten dengan narasi credential, pertahankan hasil
Core, sarankan pengguna tidak membagikan credential, dan eskalasi untuk review—jangan
membuat keputusan pengganti.

Jangan memanggil `create_intervention` secara langsung dari skill ini. Pembentukan
protected state adalah guard deterministik Core/adapter, bukan keputusan model. Jika
respons Core memuat intervention ID atau action, pertahankan nilainya tanpa perubahan.
Itu bukan izin untuk memindahkan dana, memblokir akun, mengirim pesan, atau mengubah
sistem eksternal.

Jika konteks kurang, minta klarifikasi non-sensitif. Jika tindakan yang direkomendasikan
Core belum tercatat, nyatakan status tersebut secara jujur dan eskalasi manual. Stop
setelah hasil Core dijelaskan, dependency gagal, atau budget habis.

## OpenClaw execution

Pada request OpenResponses frontend, gunakan function tool `fraud_analyze` yang disediakan
Bridge. Pada TUI/admin tanpa client tool, fallback ke
`tools/fraudguard-agent tool-execute --name fraud_analyze --arguments-json <json>`.
OpenClaw sendiri mengekstrak context non-sensitif dan mengorkestrasi tool; jangan memanggil
subcommand `chat` karena itu akan mengaktifkan planner kedua. Terima keputusan hanya dari
JSON Core yang memuat `trace_id`. Jangan fallback ke `curl`, URL arbitrer, protected
action langsung, atau keputusan lokal.
