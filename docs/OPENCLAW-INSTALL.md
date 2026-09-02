# Instalasi dan Penggunaan FraudGuard di OpenClaw

Integrasi terdiri dari tiga workspace skill dan satu CLI komunikasi terikat:

```text
OpenClaw skill → tools/fraudguard-agent → FraudGuard Agent API → FraudGuard Core
```

CLI tidak menerima URL dari percakapan. Default hanya menuju
`http://127.0.0.1:3000`; HTTP non-loopback ditolak dan endpoint remote wajib HTTPS.

## Instalasi cepat

Pastikan container agent sudah sehat:

```bash
curl http://127.0.0.1:3000/health
curl http://127.0.0.1:3000/ready
```

Dari repository `fraudguard-ai-agent` di VPS:

```bash
chmod +x scripts/install_openclaw.sh scripts/fraudguard_agent_cli.py
./scripts/install_openclaw.sh
```

Installer membaca workspace dari:

```bash
openclaw config get agents.defaults.workspace
```

Untuk workspace atau profile tertentu:

```bash
./scripts/install_openclaw.sh --workspace /root/.openclaw/workspace
./scripts/install_openclaw.sh --profile production
./scripts/install_openclaw.sh --dev
```

Installer aman dijalankan ulang. File berbeda tidak ditimpa kecuali `--force`; mode
tersebut memindahkan versi lama ke `.fraudguard-backups/<timestamp>/` di workspace.

## Credential agent

Jika `AGENT_ACCESS_KEY` aktif pada service agent, simpan nilai yang sama di luar
workspace OpenClaw:

```bash
install -d -m 700 /root/.config/fraudguard-agent
umask 077
read -rsp 'FraudGuard Agent key: ' FRAUDGUARD_KEY_INPUT
printf '%s' "$FRAUDGUARD_KEY_INPUT" > /root/.config/fraudguard-agent/access.key
unset FRAUDGUARD_KEY_INPUT
chmod 600 /root/.config/fraudguard-agent/access.key
```

Jangan menulis key ke `SKILL.md`, `TOOLS.md`, Git, history command, atau prompt. Untuk
lokasi lain, set `FRAUDGUARD_AGENT_KEY_FILE` pada environment Gateway. Untuk endpoint
HTTPS non-default, set `FRAUDGUARD_AGENT_URL` pada environment Gateway dan restart
Gateway agar environment baru terbaca.

## Verifikasi OpenClaw

```bash
openclaw skills info fraud-detection
openclaw skills info safety-payment
openclaw skills info realtime-intervention
openclaw skills check
```

Jika skill baru belum muncul, buka session OpenClaw baru. Restart Gateway hanya jika
workspace watcher atau environment credential belum ter-refresh.

Jika OpenClaw meminta persetujuan eksekusi, izinkan hanya executable workspace
`tools/fraudguard-agent`. Jangan memberi allowlist shell, `curl`, atau generic HTTP
client karena skill FraudGuard tidak memerlukannya.

### Skill creator opsional

Untuk workspace development, pengguna awam dapat memasang helper pembuatan skill:

```bash
./scripts/install_openclaw.sh --with-creator
openclaw skills info skill-creator
```

Contoh chat: `Buat skill dari capability fraud-detection v1.` Helper ini memverifikasi
capability dan hanya membuat draft/file jika runtime mempunyai izin workspace. Jangan
pasang dengan `--with-creator` pada workspace produksi yang hanya membutuhkan tiga skill
operasional.

Uji CLI tanpa model dan simpan path untuk command berikutnya:

```bash
OPENCLAW_WORKSPACE="$(openclaw config get agents.defaults.workspace)"
FRAUDGUARD_CLI="$OPENCLAW_WORKSPACE/tools/fraudguard-agent"
"$FRAUDGUARD_CLI" health
"$FRAUDGUARD_CLI" ready
"$FRAUDGUARD_CLI" tools
```

## Komunikasi CLI

Buat session:

```bash
"$FRAUDGUARD_CLI" session-create --channel openclaw
```

Installer sengaja tidak mengubah system `PATH`; gunakan variabel `FRAUDGUARD_CLI` di
terminal. Skill OpenClaw memanggil path workspace `tools/fraudguard-agent`.

Analisis pesan mencurigakan:

```bash
"$FRAUDGUARD_CLI" chat \
  --message 'Petugas bank meminta saya segera transfer ke rekening aman'
```

Periksa pembayaran sintetis:

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

Kirim hasil intervensi:

```bash
"$FRAUDGUARD_CLI" chat \
  --session-id SESSION_UUID \
  --message 'Verifikasi selesai' \
  --context-json '{
    "intervention_id":"INTERVENTION_UUID",
    "intervention_result":{"third_party_instruction_confirmed":true},
    "intervention_status":"COMPLETED"
  }'
```

## Penggunaan dari chat OpenClaw

Setelah instalasi, gunakan bahasa natural:

- `Periksa apakah pesan ini penipuan: ...`
- `Periksa pembayaran sintetis ini: ID demo-pay-001, IDR 250000, penerima baru ...`
- `Lanjutkan verifikasi intervention <UUID> dengan hasil ...`
- `Tampilkan audit untuk trace <UUID>.`

OpenClaw memilih skill berdasarkan description, lalu skill menggunakan CLI. Respons
yang sah harus berasal dari JSON agent dan mempertahankan `trace_id`. OpenClaw tidak
boleh menghitung score, membuat policy decision, atau mengklaim rekening eksternal sudah
diblokir.

## Troubleshooting

- `skill not found`: pastikan folder berada di `<workspace>/skills/<name>/SKILL.md`, lalu
  buka session baru.
- `401 Invalid agent access key`: periksa key file mode `600` dan kesamaan key dengan
  `AGENT_ACCESS_KEY` pada container agent.
- `Agent tidak dapat dihubungi`: jalankan CLI `health`, periksa port loopback dan
  container agent.
- `/ready` gagal: agent hidup tetapi Core tidak dapat dijangkau atau menolak konfigurasi.
- CLI menolak URL HTTP: gunakan loopback atau HTTPS; jangan menonaktifkan guard ini.
