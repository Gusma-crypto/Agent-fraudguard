# FraudGuard AI Agent

FraudGuard AI Agent adalah layer **Reasoning + Orchestration + Conversation** untuk
FraudGuard Core di repository `Fraudguard-core`.

Boundary final:

```text
User / OpenClaw / Application
              ↓
FraudGuard AI Agent
conversation, context, planner, guardrails, typed tools
              ↓ HTTPS REST
FraudGuard Core
risk, policy, protected decision, incident, learning, audit, PostgreSQL
```

Agent tidak memiliki database, risk engine, policy engine, atau authoritative audit.
Reasoning V1 menggunakan provider `deterministic`; tidak membutuhkan API key model.
Fraud decision `REVIEW`, `STEP_UP_VERIFY`, atau `TEMPORARY_HOLD` memicu satu intervensi
protektif idempotent di Core. Agent tidak melakukan enforcement pada akun, pembayaran,
atau sistem eksternal.

## API

- `POST /agent/v1/sessions`
- `GET /agent/v1/sessions/{id}`
- `DELETE /agent/v1/sessions/{id}`
- `POST /agent/v1/chat`
- `GET /agent/v1/tools`
- `GET /health`
- `GET /ready`

`/ready` hanya sukses ketika agent dapat mencapai endpoint ready milik Core.

Runtime mendukung respons `en` (English), `id` (Indonesian), dan `ms` (Malay). Bahasa
dideteksi dari pesan atau dapat diberikan melalui `context.language`/`context.locale`.
English digunakan sebagai fallback. Decision, severity, reason code, action, dan trace
ID authoritative dari Core tidak diterjemahkan.

## Local run

Jalankan Core terlebih dahulu di `http://localhost:8080`, kemudian:

```bash
cp .env.example .env
chmod +x deploy.sh
./deploy.sh deploy
curl http://127.0.0.1:3000/health
curl http://127.0.0.1:3000/ready
```

Contoh percakapan:

```bash
curl -X POST http://127.0.0.1:3000/agent/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Petugas bank meminta saya transfer sekarang ke rekening aman"}'
```

Jika `AGENT_ACCESS_KEY` diisi, tambahkan header `X-Agent-Key`. Core credential hanya
disimpan di service agent dan tidak pernah dikirim ke browser/model.

## Deploy Agent setelah Core aktif

Agent dibangun hanya dari repository ini dan tidak membutuhkan path tetap seperti
`/opt/Agent-fraudguard`. Compose menghubungkannya ke Core melalui network Docker bersama
`fraudguard-network`. Deploy Core lebih dahulu, lalu:

```bash
cp .env.example .env
# Isi scoped Core API key dan samakan AGENT_ACCESS_KEY dengan konfigurasi Core.
chmod +x deploy.sh
./deploy.sh deploy
curl http://127.0.0.1:3000/health
curl http://127.0.0.1:3000/ready
```

Perintah operasional tersedia dari root repository:

```bash
./deploy.sh deploy    # build dan deploy source saat ini
./deploy.sh update    # git pull --ff-only, rebuild, dan recreate
./deploy.sh restart   # restart lalu validasi koneksi Core
./deploy.sh status
./deploy.sh logs
./deploy.sh stop
./deploy.sh check
```

Untuk memakai `.env.production`, jalankan
`ENV_FILE=.env.production ./deploy.sh deploy`. Gunakan `NO_CACHE=1` bersama `deploy`
atau `update` jika image harus dibangun ulang tanpa cache.

Agent dipublish hanya pada loopback `127.0.0.1:3000`. OpenClaw yang berjalan langsung
di host dapat memakai URL tersebut. Jika OpenClaw berada dalam container lain, gunakan
shared network atau proxy terautentikasi karena loopback container bukan loopback host.

### Session persistence dan scaling

Deployment saat ini sengaja memakai satu replica dengan session store in-memory. Ini
menjaga instalasi VPS sederhana dan session otomatis hilang setelah restart (tidak ada
credential atau keputusan authoritative yang disimpan di session Agent). Jangan menjalankan
lebih dari satu replica dengan konfigurasi ini. Jika Agent perlu di-scale, gunakan Redis
sebagai shared session store dengan TTL, namespaced session key, dan locking/version check;
sticky session saja tidak cukup untuk menjamin konsistensi saat failover.

## OpenClaw: install dan penggunaan cepat

Setelah agent `/health` dan `/ready` berhasil, pasang tiga skill beserta CLI komunikasi:

```bash
chmod +x scripts/install_openclaw.sh scripts/fraudguard_agent_cli.py
./scripts/install_openclaw.sh
openclaw skills info fraud-detection
openclaw skills info safety-payment
openclaw skills info realtime-intervention
```

CLI dipasang sebagai `<workspace>/tools/fraudguard-agent` dan hanya mengakses endpoint
agent yang telah dibatasi. Siapkan path CLI dan periksa komunikasi:

```bash
OPENCLAW_WORKSPACE="$(openclaw config get agents.defaults.workspace)"
FRAUDGUARD_CLI="$OPENCLAW_WORKSPACE/tools/fraudguard-agent"

"$FRAUDGUARD_CLI" health
"$FRAUDGUARD_CLI" ready
"$FRAUDGUARD_CLI" tools
```

Jika agent memakai `AGENT_ACCESS_KEY`, simpan key yang sama pada
`~/.config/fraudguard-agent/access.key` dengan permission `600`. Jangan menyimpan key
di workspace, prompt, atau Git.

Buat conversation session:

```bash
"$FRAUDGUARD_CLI" session-create --channel openclaw
```

Salin `session_id` dari respons, kemudian analisis fraud:

```bash
"$FRAUDGUARD_CLI" chat \
  --session-id SESSION_UUID \
  --message 'Petugas bank meminta saya segera transfer ke rekening aman'
```

Periksa pembayaran sintetis dalam session yang sama:

```bash
"$FRAUDGUARD_CLI" chat \
  --session-id SESSION_UUID \
  --message 'Periksa pembayaran ini' \
  --context-json '{
    "external_payment_id":"demo-pay-001",
    "amount":"250000.00",
    "currency":"IDR",
    "recipient_ref":"recipient-masked-001",
    "recipient_is_new":true,
    "fraud_context":{"third_party_instruction":true,"urgent":true}
  }'
```

Untuk menggunakan dari percakapan OpenClaw, buka session baru setelah instalasi dan
gunakan prompt natural language:

```text
Periksa apakah pesan ini penipuan: petugas bank meminta saya transfer ke rekening aman.
Periksa pembayaran sintetis ID demo-pay-001 senilai IDR 250000 ke penerima baru.
Lanjutkan verifikasi intervention <UUID> dengan hasil instruksi pihak ketiga terkonfirmasi.
Tampilkan audit untuk trace <UUID>.
```

OpenClaw memilih skill, lalu menjalankan CLI komunikasi. Score, policy decision,
intervention, dan trace tetap berasal dari FraudGuard Core. Panduan credential, profile,
intervention JSON, dan troubleshooting lengkap ada di
[docs/OPENCLAW-INSTALL.md](docs/OPENCLAW-INSTALL.md).

`intervention_result` dan `intervention_status` adalah context sekali-pakai. Setelah
hasil tersebut dikirim ke Core, permintaan audit pada session yang sama diarahkan ke
`get_trace_audit` dan tidak mengulang submission intervensi non-idempotent.

Narasi yang meminta OTP, password, PIN, atau CVV menghasilkan indikator boolean
`credential_request`; nilai credential tidak diterima atau diteruskan. Core memberi
bobot risiko pada indikator tersebut. OpenClaw wajib mempertahankan decision/score Core
dan tidak boleh mengubah `ALLOW` menjadi klaim fraud atau kepastian "100% penipuan".

### Membuat skill baru untuk pengguna awam

`skill-creator` adalah helper development opsional, bukan skill pemeriksaan fraud
produksi. Pasang ke workspace development:

```bash
./scripts/install_openclaw.sh --with-creator
openclaw skills info skill-creator
```

Buka session OpenClaw baru, lalu gunakan permintaan sederhana:

```text
Buat skill dari capability fraud-detection v1.
Perbarui skill safety-payment agar protected action selalu fail closed.
Validasi skill realtime-intervention dan jelaskan hasilnya dengan bahasa sederhana.
```

Skill creator akan memeriksa capability dan tool yang sudah terdaftar, mencegah skill
ganda, lalu membuat atau memperbarui file hanya jika workspace mengizinkan. Ia tidak
boleh menciptakan endpoint, score, policy, atau permission baru. Instruksi lengkap ada
di [skills/skill-creator/SKILL.md](skills/skill-creator/SKILL.md).

## Quality

```bash
docker build --target test -f Docker/Dockerfile -t agent-fraudguard:test .
docker run --rm agent-fraudguard:test pytest -q
docker run --rm agent-fraudguard:test ruff check src tests scripts
```

Struktur runtime aktif hanya berada di `src/fraudguard_agent`. Aset `skills/`,
`agents/`, dan `commands/` adalah kontrak OpenClaw yang harus memanggil API agent/Core
melalui allowlist, bukan menjalankan logic authority sendiri.

Status kesiapan HackFest, bukti yang wajib direkam, dan blocker sebelum submit tersedia
di [docs/SUBMISSION-CHECKLIST.md](docs/SUBMISSION-CHECKLIST.md).
