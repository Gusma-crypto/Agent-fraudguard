# FraudGuard AI Agent

FraudGuard AI Agent adalah layer **Reasoning + Orchestration + Conversation** untuk
FraudGuard Core di repository `Fraudguard-core`.

Boundary production OpenClaw:

```text
Frontend / Application
        ↓ HTTPS
FraudGuard OpenClaw Bridge
        ↓ private OpenResponses API
OpenClaw Gateway (sole orchestrator + skills)
        ↓ typed function-call response
FraudGuard OpenClaw Bridge
        ↓ HTTPS REST
FraudGuard Core
risk, policy, protected decision, incident, learning, audit, PostgreSQL
```

UI menampilkan `OpenClaw Orchestrator` berdasarkan `GET /agent/v1/tools`. Nama provider
tidak ditampilkan di panel progress utama; detail evidence/audit tetap berasal dari Core.
Session OpenClaw disimpan di `sessionStorage`, sehingga `New Chat` membuat konteks baru.

Bridge dan tool adapter tidak memiliki database, risk engine, policy engine, atau authoritative audit.
Reasoning V1 menggunakan provider `deterministic`; tidak membutuhkan API key model.
Fraud decision `REVIEW`, `STEP_UP_VERIFY`, atau `TEMPORARY_HOLD` memicu satu intervensi
protektif idempotent di Core. Agent tidak melakukan enforcement pada akun, pembayaran,
atau sistem eksternal.

Untuk intelligence satu identifier, kirim `context.intelligence_query`. Untuk satu pesan
yang memuat beberapa indikator, kirim `context.intelligence_input` berisi `text` dan field
opsional `phone`, `url`, `bank_account`, `email`, serta `transaction_context`. Agent
meneruskan payload ini ke Core; Core melakukan extraction, routing provider, evidence,
claim, risk, dan policy. Frontend/Agent harus membedakan observation, claim, dan decision.

## API

- `POST /agent/v1/sessions`
- `GET /agent/v1/sessions/{id}`
- `DELETE /agent/v1/sessions/{id}`
- `POST /agent/v1/chat`
- `GET /agent/v1/tools`
- `GET /health`
- `GET /ready`
- `POST /agent/v1/tools/{tool_name}/execute` (private tool adapter)

Frontend memakai service bridge pada alias Docker `fraudguard-agent`. Untuk browser,
Bridge menyediakan typed client tools pada OpenResponses dan mengeksekusi tool pilihan
OpenClaw ke Core. Tool adapter loopback port `3000` tetap tersedia hanya sebagai fallback
TUI/admin. Aktifkan endpoint Gateway terlebih dahulu:

```bash
openclaw config set gateway.http.endpoints.responses.enabled true
DOCKER_HOST_GATEWAY="$(docker network inspect bridge --format '{{(index .IPAM.Config 0).Gateway}}')"
openclaw config set gateway.bind custom
openclaw config set gateway.customBindHost "$DOCKER_HOST_GATEWAY"
openclaw gateway restart
```

`customBindHost` membuat Gateway dapat dicapai Bridge melalui `host.docker.internal`
tanpa bind publik `0.0.0.0`. Pastikan firewall/cloud security group tidak membuka TCP 18789.

Set environment Agent tanpa menaruh token di frontend:

```env
AGENT_RUNTIME=openclaw
OPENCLAW_GATEWAY_URL=http://host.docker.internal:18789
OPENCLAW_GATEWAY_TOKEN=<gateway-token>
OPENCLAW_AGENT_ID=fraudguard
OPENCLAW_BRIDGE_PORT=3100
```

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

Setelah agent `/health` dan `/ready` berhasil, pasang root contract, lima skill produksi,
dan CLI komunikasi ke workspace khusus FraudGuard:

```bash
chmod +x scripts/install_openclaw.sh scripts/fraudguard_agent_cli.py
./scripts/install_openclaw.sh \
  --workspace /root/.openclaw/workspace-fraudguard \
  --force
openclaw skills info fraud-detection
openclaw skills info safety-payment
openclaw skills info realtime-intervention
openclaw skills info social-engineering
openclaw skills info intelligence-search
```

Setelah repository diperbarui, deploy Agent dan sinkronkan ulang skill ke workspace:

```bash
cd ~/Agent-fraudguard
./deploy.sh update
./scripts/install_openclaw.sh \
  --workspace /root/.openclaw/workspace-fraudguard \
  --force
openclaw skills check
openclaw agent --agent fraudguard --session-key fraudguard-demo-v2 \
  --message "Periksa pesan mencurigakan ini ..."
```

Installer membuat backup versi sebelumnya di
`<workspace>/.fraudguard-backups/<timestamp>/`. Buka session baru agar OpenClaw memuat
snapshot skill terbaru. Panduan lima-skill, profile production, verifikasi CLI, dan
troubleshooting tersedia di [docs/OPENCLAW-INSTALL.md](docs/OPENCLAW-INSTALL.md).

`openclaw-workspace/AGENTS.md` membatasi satu primary assessment per turn, mencegah
duplikasi skill/provider call, menjaga nilai Core apa adanya, mengisolasi session dan
memory, serta membuat file runtime read-only selama penanganan kasus. CLI fallback hanya
untuk data sintetis/masked karena argument command dapat terlihat di process list.

Bridge harus memakai `OPENCLAW_AGENT_ID=fraudguard`; nilai `main` akan mengarahkan
frontend ke agent utama beserta katalog skill globalnya. Batasi `agents.list[INDEX].skills`
untuk agent `fraudguard` ke lima slug produksi sebagaimana dijelaskan pada panduan install.

Jika installer melaporkan `Missing runtime source: openclaw-workspace/USER.md`, checkout
VPS belum memuat seluruh template runtime. Pastikan commit terbaru berisi file tersebut
dengan `git ls-files openclaw-workspace/USER.md`, lalu pull ulang sebelum instalasi.

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

Agent juga mengenali dua journey berisiko tinggi: link/form + OTP/credential, serta
impersonation marketplace/bank + hadiah + permintaan transfer/remote guidance. Journey
pertama memakai `fraud-detection`, sedangkan journey kedua dapat memakai
`social-engineering`; keputusan tetap berasal dari Core. Untuk lookup eksplisit gunakan context `intelligence_query`, optional
`entity_type`, dan `deep_search`; skill `intelligence-search` tidak mengarang evidence
ketika public discovery belum dikonfigurasi.

Setiap lookup mengembalikan blok terstruktur `intelligence.sources`,
`intelligence.evidence`, dan `intelligence.claims`. Jika bukti ditemukan, OpenClaw/UI
menampilkan nama dan URL HTTPS sumber, metode akses, waktu, ringkasan evidence,
confidence, serta status verifikasi. Jika tidak ditemukan, array kosong dan pesan
“no supporting source/evidence” harus ditampilkan secara eksplisit. Status `UNVERIFIED`
tetap bukan vonis fraud.
Jika tersedia, dashboard juga menampilkan thumbnail HTTPS dan `archived_excerpt` beserta
content hash. Snapshot adalah cadangan provenance ketika sumber asli mati, tetapi tidak
mengubah evidence `UNVERIFIED` menjadi fakta terkonfirmasi.

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

## Telegram demo (explicit consent)

Telegram is served by the OpenClaw Bridge at
`POST /telegram/v1/webhook`. The endpoint verifies Telegram's
`X-Telegram-Bot-Api-Secret-Token`; it does not accept the public browser Agent key.
Private messages require explicit consent. Group messages are ignored unless they use
`/cek`, `/analisis`, mention the configured bot, or reply to the bot. Before consent,
case content is neither sent to OpenClaw/Core nor persisted; the user must resend it
after choosing **Setuju**.

Core stores only an HMAC-pseudonymous channel subject, consent state/version/expiry,
and an audit event. Raw Telegram user/chat IDs and the pre-consent message are not sent
to Core. The same generic Core contract already reserves `WHATSAPP` as a future adapter;
no WhatsApp transport is implemented yet.

Generate different server-side secrets (do not commit their output):

```bash
openssl rand -hex 32
openssl rand -hex 32
```

Set the first value as `TELEGRAM_WEBHOOK_SECRET`, the second as
`TELEGRAM_SUBJECT_HMAC_KEY`, and set `TELEGRAM_BOT_TOKEN`,
`TELEGRAM_BOT_USERNAME`, and `TELEGRAM_ENABLED=true` in the Agent `.env`. The Agent's
Core key must be present in `FRAUDGUARD_CORE_API_KEY`; the current root provisioning key
already satisfies the required `consents:read` and `consents:write` scopes. Never expose
any of these values through `NEXT_PUBLIC_*`.

After rebuilding/restarting the `bridge`, register the public webhook from inside the
container so the bot token stays in its environment:

```bash
docker compose --env-file .env -f Docker/compose.yml up -d --build bridge
docker compose --env-file .env -f Docker/compose.yml exec bridge python -m fraudguard_agent.telegram_setup set --url https://fraudguard.my.id/telegram/v1/webhook
docker compose --env-file .env -f Docker/compose.yml exec bridge python -m fraudguard_agent.telegram_setup info
docker compose --env-file .env -f Docker/compose.yml exec bridge python -m fraudguard_agent.telegram_setup commands-info
```

Perintah `set` mendaftarkan webhook sekaligus menu bot. Untuk memperbarui menu tanpa
mengubah webhook, jalankan:

```bash
docker compose --env-file .env -f Docker/compose.yml exec bridge \
  python -m fraudguard_agent.telegram_setup commands-set
```

Menu memuat `/cek` (`fraud-detection`), `/bayar` (`safety-payment`), `/intervensi`
(`realtime-intervention`), `/sosial` (`social-engineering`), dan `/intelijen`
(`intelligence-search`). `/analisis` tetap menjadi alias `/cek`; `/start`, `/consent`,
`/privacy`, `/revoke`, dan `/help` menangani onboarding dan privasi. Telegram dapat
menyimpan cache menu beberapa saat; tutup lalu buka kembali chat bot jika tombol menu
belum langsung berubah.

Alias demo `/cek_nomor`, `/cek_domain`, dan `/safety` tersedia. Ketika hasil Core
mengandung `intervention_id`, Bridge menyimpannya maksimal 30 menit dalam memory sesi
Telegram. `/intervensi` hanya memakai ID authoritative tersebut; tanpa ID aktif bot
meminta payment check lebih dahulu. Runbook lengkap dipasang ke
`<workspace>/docs/demo-telegram-intervention-flow.md` oleh installer OpenClaw.
Untuk payment check, Bridge menghasilkan `external_payment_id` pseudonim dan idempotent
dari update Telegram; pengguna tidak perlu membuat atau mengetik ID teknis tersebut.

Setelah consent valid, bot segera mengirim satu pesan progres sesuai skill, misalnya
`FraudGuard sedang memeriksa keamanan pembayaran`. Setelah OpenClaw/Core selesai, pesan
yang sama diedit menjadi hasil akhir. Ini menjaga progres tetap terlihat tanpa membuat
deretan pesan status. Bila model/dependency gagal, pesan progres diganti dengan fallback
`UNKNOWN/PENDING`, bukan dibiarkan sebagai hasil palsu.
Selama proses berlangsung, Bridge juga memperbarui native Telegram `typing` chat action
setiap empat detik. Pengguna akan melihat indikator titik-titik di bagian atas chat;
indikator berhenti otomatis ketika analisis selesai atau dibatalkan.

Keep BotFather privacy mode enabled for groups. Test `/start`, choose **Setuju**, resend
a synthetic suspicious message, then test `/revoke`. A valid Core result includes a real
trace ID; if OpenClaw/Core is unavailable the bot returns a conservative review message
without inventing a risk score.

`/cek` and `/analisis` require content, for example `/cek pesan mencurigakan`, or must be
sent as a reply to the target message. An empty command returns usage guidance and does
not call OpenClaw/Core.

Untuk command fraud, social engineering, dan intelligence, Bridge mewajibkan OpenClaw
memanggil typed `intelligence_lookup`. Bridge mempertahankan pesan asli sebagai input
ingestion dan mengaktifkan deep search. Dengan demikian, narasi model tanpa hasil Core
tidak dapat berubah menjadi verdict Telegram.

Hasil Telegram memakai Bahasa Indonesia dan tetap menampilkan code Core agar audit dapat
dicocokkan. Untuk shortlink, bot menjelaskan bahwa alamat tujuan dan status akses akhirnya
belum dapat dipastikan dari shortlink itu sendiri—bukan berarti link aman, mati, atau
terbukti berbahaya. Bot hanya menulis bahwa provider mencatat respons gagal jika Core mengembalikan signal
`URL_UNREACHABLE`; status tersebut tetap merupakan observation yang dapat berubah.

### VPS runbook: OpenClaw Gateway dan Telegram

`openclaw config get gateway.auth.token` sengaja mengembalikan
`OPENCLAW_REDACTED`. Jangan menyalin nilai redacted itu ke `.env`. Token pada Gateway
dan `OPENCLAW_GATEWAY_TOKEN` di Agent harus identik, tetapi tetap server-side. Setelah
mengubah `.env`, gunakan `--force-recreate`; `docker compose restart` saja tidak memuat
ulang environment container.

Verifikasi dilakukan berurutan. Keberhasilan satu tahap tidak membuktikan tahap setelahnya:

1. `GET /v1/models` dengan Bearer token harus menghasilkan HTTP `200`. Ini hanya
   membuktikan jaringan Bridge → Gateway dan autentikasi.
2. `POST /v1/responses` dengan model `openclaw/fraudguard` harus menghasilkan HTTP
   `200`. Ini membuktikan provider/model dapat menjalankan turn.
3. `GET http://127.0.0.1:3100/ready` harus menghasilkan HTTP `200` dan
   `orchestrator=openclaw`.
4. `telegram_setup info` harus menunjukkan URL webhook yang benar, tidak ada pending
   update yang terus bertambah, dan tidak ada error baru.
5. Baru setelah itu uji pesan sintetis Telegram dan pastikan respons memiliki trace ID
   authoritative dari Core.

Tes model dari dalam Bridge tanpa mencetak token:

```bash
docker compose --env-file .env -f Docker/compose.yml exec bridge \
  python -c 'import os,httpx; u=os.environ["OPENCLAW_GATEWAY_URL"].rstrip("/")+"/v1/responses"; h={"Authorization":"Bearer "+os.environ["OPENCLAW_GATEWAY_TOKEN"]}; p={"model":"openclaw/fraudguard","input":"Jawab singkat: runtime aktif.","stream":False,"max_output_tokens":128}; r=httpx.post(u,headers=h,json=p,timeout=120); print("STATUS",r.status_code); print(r.text[:2000])'
```

Jika `/v1/models` sudah `200` tetapi Telegram diam, periksa `/v1/responses`, log Bridge,
dan status webhook secara bersamaan:

```bash
docker compose --env-file .env -f Docker/compose.yml logs --tail=200 bridge
docker compose --env-file .env -f Docker/compose.yml exec bridge \
  python -m fraudguard_agent.telegram_setup info
```

`401` pada `/v1/models` berarti token berbeda. Timeout koneksi berarti bind/firewall
private Gateway belum benar. `429`, `503`, `overloaded`, atau timeout pada
`/v1/responses` berarti provider/model belum siap meskipun token valid. Respons Telegram
`UNKNOWN/PENDING` adalah fallback fail-closed; tidak boleh dipresentasikan sebagai hasil
analisis berhasil. HTTP `405` HTML dari Nginx berarti `/telegram/*` jatuh ke frontend,
sedangkan HTTP `401` JSON pada POST manual tanpa secret berarti route sudah mencapai
Bridge dan autentikasi webhook bekerja.

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
