# Demo Telegram sampai Realtime Intervention

Dokumen ini adalah runbook demo sintetis FraudGuard. Transport Telegram dimiliki
FraudGuard OpenClaw Bridge; jangan aktifkan `channels.telegram` native OpenClaw dengan
bot token yang sama. OpenClaw tetap menjadi satu-satunya orchestrator melalui private
`/v1/responses`, sedangkan FraudGuard Core menentukan evidence, risk, policy, keputusan,
intervention ID, persistence, dan audit.

## Prasyarat operator

1. Core API, worker, database, frontend, Caddy, Agent tool adapter, Bridge, dan OpenClaw
   Gateway sehat.
2. Core migration terbaru sudah diterapkan.
3. Agent `.env` memuat credential Telegram, Core, dan OpenClaw hanya di server.
4. `GET /v1/models`, `POST /v1/responses`, serta Bridge `/ready` berhasil.
5. Webhook mengarah ke `https://fraudguard.my.id/telegram/v1/webhook`.

Daftarkan webhook dan command menu dari container Bridge:

```bash
docker compose --env-file .env -f Docker/compose.yml exec bridge \
  python -m fraudguard_agent.telegram_setup set \
  --url https://fraudguard.my.id/telegram/v1/webhook

docker compose --env-file .env -f Docker/compose.yml exec bridge \
  python -m fraudguard_agent.telegram_setup info

docker compose --env-file .env -f Docker/compose.yml exec bridge \
  python -m fraudguard_agent.telegram_setup commands-info
```

Jangan menampilkan `.env`, token, Authorization header, raw Telegram ID, atau data nyata
dalam rekaman demo.

## Skenario sintetis

Gunakan teks ini sebagai data demonstrasi, bukan laporan terhadap pihak nyata:

```text
[SIMULASI] Selamat, Anda menang hadiah undian toko online senilai Rp10 juta.
Klaim dalam 10 menit dengan memberikan OTP dan transfer biaya administrasi Rp500 ribu
ke rekening BCA sintetis 1234567890. Hubungi nomor sintetis 081234567890.
Jangan beri tahu siapa pun.
```

## Alur lima fase

### 1. Consent

Kirim `/start`, baca pemberitahuan, lalu tekan **Setuju**. Pesan yang memicu consent
tidak dianalisis; kirim ulang pesan setelah consent aktif.

### 2. Fraud detection

Forward skenario sintetis atau kirim:

```text
/cek [SIMULASI] Selamat, Anda menang hadiah ...
```

Bot menampilkan satu pesan loading lalu mengeditnya menjadi hasil Core. Jangan menjanjikan
nilai score atau policy tertentu. Tunjukkan signal, rekomendasi, dan trace ID yang benar-benar
dikembalikan saat demo.
Selama analisis, indikator mengetik berupa titik-titik muncul di bagian atas chat dan
diperbarui berkala sampai hasil atau fallback tersedia.

### 3. Intelligence

Gunakan salah satu command berikut:

```text
/cek_nomor 081234567890
/cek_domain example.invalid
/intelijen Periksa nomor sintetis 081234567890 dan domain example.invalid
```

Hasil kosong bukan bukti aman. Provider error, evidence, claim, corroboration, dan status
verifikasi harus disampaikan sesuai respons Core; jangan memakai angka laporan buatan.
Untuk demo shortlink, jelaskan bahwa shortlink menyembunyikan tujuan akhir dan status
aksesnya tidak dapat dipastikan dari shortlink itu sendiri. Bot hanya boleh menyebut
provider mencatat respons gagal jika Core mengembalikan observation `URL_UNREACHABLE`.

### 4. Safety payment

```text
/bayar [SIMULASI] Rp500 ribu ke rekening BCA sintetis 1234567890, penerima baru, diminta segera
```

Alias `/safety` juga tersedia. Jika Core membuat intervention, bot menampilkan
`Intervention: <uuid>` dan menyimpannya sementara selama 30 menit untuk sesi chat tersebut.
Bridge membuat external payment ID pseudonim secara otomatis dari update Telegram sehingga
pengguna tidak perlu mengetik ID teknis dan retry tetap idempotent.

### 5. Realtime intervention

Sesudah fase payment menghasilkan intervention ID, kirim jawaban kontekstual tanpa data
rahasia, misalnya:

```text
/intervensi Tidak sedang menelepon; ya, diminta transfer sekarang; ya, penerima baru.
```

Bridge hanya meneruskan command ini jika intervention ID berasal dari hasil Core pada sesi
Telegram yang sama. Tanpa ID aktif, bot meminta pengguna menjalankan `/bayar` lebih dahulu.
Keputusan reassessment ditampilkan apa adanya. `TEMPORARY_HOLD` adalah state protektif
internal FraudGuard, bukan bukti bank atau transaksi eksternal benar-benar diblokir.

## Command demo

- `/cek`, `/analisis` — `fraud-detection:v1`
- `/cek_nomor`, `/cek_domain`, `/intelijen` — `intelligence-search:v1`
- `/bayar`, `/safety` — `safety-payment:v1`
- `/intervensi` — `realtime-intervention:v1`
- `/sosial` — `social-engineering:v1`
- `/consent`, `/privacy`, `/revoke`, `/help` — consent dan bantuan

Di grup, gunakan command dengan isi, mention bot, atau reply pesan target. Percakapan grup
biasa diabaikan. Biarkan privacy mode BotFather tetap aktif.

## Bukti keberhasilan

Demo selesai hanya jika tersedia:

- consent `GRANTED` tanpa menyimpan isi pre-consent;
- loading yang diedit menjadi hasil, bukan pesan progress bertumpuk;
- skill route yang sesuai command;
- risk/policy dan intervention ID dari Core;
- reassessment dari intervention aktif;
- trace ID yang dapat ditemukan pada audit Core;
- tidak ada credential atau identifier personal di layar/log demo.

Jika dependency gagal, tampilkan fallback `UNKNOWN/PENDING`, hentikan transaksi simulasi,
dan periksa log. Jangan mengganti kegagalan dengan mock verdict tersembunyi.
