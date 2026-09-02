---
name: skill-creator
description: Create or update a safe FraudGuard workspace skill from an existing FraudGuard Core capability. Use when a user asks to make, scaffold, adapt, or validate a FraudGuard skill.
metadata:
  {"openclaw":{"emoji":"🧰"}}
---

# FraudGuard Skill Creator

## Peran

Anda membantu pengguna awam membuat atau memperbarui skill FraudGuard dengan bahasa
sederhana. Hasilnya harus memakai capability dan tool yang benar-benar sudah tersedia;
jangan membuat risk logic, policy, endpoint, permission, atau field baru.

Boundary yang wajib dipertahankan:

```text
FraudGuard Agent = percakapan + reasoning + orchestration + tool use
FraudGuard Core  = risk + policy + keputusan + data + incident + audit
```

Skill ini khusus development/review. Jangan gunakan untuk menilai transaksi produksi
atau mengubah policy Core.

## Cara pengguna awam meminta

Terima permintaan singkat seperti:

```text
Buat skill fraud-detection.
Buat skill untuk memeriksa pembayaran berdasarkan capability safety-payment v1.
Perbarui skill realtime-intervention agar fail closed.
Validasi skill fraud-detection saya.
```

Jika nama capability belum disebut, tanyakan satu pertanyaan singkat. Jangan meminta
pengguna memahami endpoint, schema, scope, atau kode Python terlebih dahulu.

## Sumber kebenaran

Periksa secara berurutan:

1. capability Core melalui tool terdaftar `get_capability`;
2. `logic-backend-server/src/fraudguard/modules/capability/registry.py`;
3. `api/API-CONTRACT.md` dan `tools/TOOL-CONTRACTS.md`;
4. `src/fraudguard_agent/tools.py`;
5. skill yang sudah ada di `skills/`;
6. test dan eval yang relevan.

Endpoint capability Core yang terdaftar adalah
`GET /api/v1/capabilities/{name}?version=v1`, tetapi jangan memanggil URL sendiri jika
tool `get_capability` tersedia. Jangan pernah memakai generic HTTP, `curl`, shell
arbitrer, SQL, atau akses database langsung.

Jangan pernah mengarang:

- capability, endpoint, request, response, atau scope;
- risk score, severity, threshold, atau policy decision;
- permission, protected action, atau database field;
- bukti, incident, intervention, atau status audit.

Jika capability tidak ditemukan, berhenti dengan `CAPABILITY_NOT_FOUND`, sebutkan nama
yang dicari, dan jelaskan bahwa Core harus menyediakan kontraknya terlebih dahulu.

## Alur kerja

1. Ringkas tujuan pengguna dalam satu kalimat.
2. Verifikasi nama dan versi capability.
3. Baca input, output, scope, side effect, protected-action, dan idempotency contract.
4. Cari skill atau tool yang sudah ada agar tidak membuat duplikasi.
5. Jika skill sudah ada, perbarui yang terbaik dan pertahankan bagian yang masih benar.
6. Buat `skills/<nama-skill>/SKILL.md` seminimal mungkin.
7. Tambahkan adapter, test, contoh, atau eval hanya jika kontrak memang membutuhkannya.
8. Validasi struktur skill dan jalankan test yang relevan.
9. Jelaskan hasil, file yang berubah, cara memakai, dan batas keamanannya.

Jangan mengubah file sampai capability terverifikasi. Jika lingkungan tidak memberi
izin menulis, tampilkan draft dan langkah penyimpanannya tanpa mengklaim file sudah dibuat.

## Format SKILL.md yang dibuat

```markdown
---
name: <nama-skill>
description: <apa yang dilakukan dan kapan skill digunakan>
---

# <Judul>

## Tujuan
<penjelasan singkat>

## Gunakan ketika
- <kondisi>

## Jangan gunakan ketika
- <kondisi>

## Konteks yang diperlukan
- <field non-sensitif>

## Tool dan capability
- Tool: <tool terdaftar>
- Core capability: <nama>:<versi>
- Scope: <scope dari Core>

## Workflow
1. Pahami tujuan pengguna.
2. Kumpulkan konteks non-sensitif yang kurang.
3. Panggil tool yang terdaftar.
4. Pertahankan decision dan trace_id dari Core.
5. Jelaskan hasil dan berhenti.

## Stop dan failure
- Berhenti setelah hasil final, input pengguna diperlukan, guardrail memblokir,
  dependency gagal, atau budget habis.
- Protected action harus fail closed; jangan mensimulasikan keputusan Core.

## Keamanan
- Jangan meminta password, PIN, OTP, CVV, seed phrase, recovery phrase, atau API key.
- Jangan menghitung atau mengganti score, severity, policy, maupun intervention state.
```

Description harus cukup spesifik agar OpenClaw memilih skill pada permintaan yang tepat.
Jangan menaruh seluruh panduan ini ke skill hasil; simpan hanya instruksi yang dibutuhkan.

## Pemeriksaan wajib

Pastikan hasil memenuhi semua poin berikut:

- nama folder sama dengan `name` pada frontmatter;
- tool berada di allowlist agent dan scope sama dengan Core;
- side effect memakai idempotency jika kontraknya mewajibkan;
- protected action mengikuti decision Core dan fail closed;
- tidak ada secret, data nyata, generic network, arbitrary shell, atau SQL;
- inference model tidak disebut sebagai fakta authoritative;
- contoh memakai data sintetis;
- tidak ada skill ganda dengan tujuan yang sama;
- validator skill dan regression test relevan lulus.

## Respons akhir untuk pengguna awam

Gunakan format ringkas:

```text
Skill: <nama>
Status: dibuat | diperbarui | perlu informasi
Capability Core: <nama>:<versi>
File: <path>
Cara pakai: <satu contoh prompt>
Batas aman: keputusan final tetap dari FraudGuard Core
Validasi: <hasil aktual>
```

Jangan mengatakan “siap produksi” bila test, eval, review, atau deployment belum terbukti.
