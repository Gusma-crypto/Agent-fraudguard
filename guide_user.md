# Panduan Pengguna FraudGuard AI Agent

FraudGuard menerima percakapan tentang pesan mencurigakan, keamanan pembayaran,
intervensi, insiden, dan audit trace. Agent memahami konteks dan memilih tool; hasil
risk/policy selalu berasal dari FraudGuard Core.

## Menjalankan

1. Deploy repository `Fraudguard-core` dan buat API key khusus agent.
2. Salin `.env.example` ke `.env`.
3. Isi `FRAUDGUARD_CORE_BASE_URL` dan `FRAUDGUARD_CORE_API_KEY`.
4. Jalankan `./deploy.sh deploy`.
5. Periksa `/health` dan `/ready`.

## Percakapan

Buat sesi atau kirim chat langsung. Jika `session_id` tidak diberikan, agent membuat
sesi baru. Agent dapat meminta klarifikasi non-sensitif sebelum memanggil Core.

Jangan pernah mengirim password, PIN, OTP, CVV, seed phrase, recovery phrase, token,
atau API key. Prompt yang mencoba membuka rahasia, memilih tool terlarang, atau
menyetujui transaksi akan diblokir.

Decision `ALLOW` bukan jaminan mutlak. `REVIEW` dan `STEP_UP_VERIFY` memerlukan
verifikasi. `TEMPORARY_HOLD` tidak boleh dibypass dan harus dieskalasikan.

Runtime dapat menjawab dalam English (`en`), Indonesian (`id`), atau Malay (`ms`).
Gunakan bahasa tersebut secara natural atau kirim hint non-sensitif `language`/`locale`
pada context. English menjadi fallback untuk bahasa yang belum didukung.

Respons chat dapat memuat `actions`. Nilai ini berarti intervensi protektif telah dicatat
di FraudGuard Core; bukan berarti bank, wallet, akun, atau transaksi eksternal sudah
diblokir atau dibatalkan.

## Bukti demo dan submission

Sebelum merekam atau mengirim submission, ikuti `docs/SUBMISSION-CHECKLIST.md`. Jangan
menampilkan `.env`, API key, Authorization header, data personal, atau transaksi nyata.
Gunakan hanya skenario sintetis dan pastikan trace dari respons agent dapat dibaca pada
audit Core yang sama.

## OpenClaw dan CLI

Operator dapat memasang integrasi dengan `./scripts/install_openclaw.sh`. Setelah itu,
OpenClaw menggunakan tiga skill workspace dan CLI `<workspace>/tools/fraudguard-agent`
untuk berkomunikasi dengan API agent. Instruksi instalasi, key file mode `600`, contoh
chat, payment, dan intervention tersedia di `docs/OPENCLAW-INSTALL.md`.

Untuk belajar membuat skill, jalankan installer dengan `--with-creator`, buka session
OpenClaw baru, lalu tulis misalnya `Buat skill dari capability fraud-detection v1`.
`skill-creator` hanya untuk development: ia memeriksa kontrak Core, mencegah duplikasi,
dan tidak boleh membuat score, policy, endpoint, atau permission sendiri.

Agent tetap harus dideploy walaupun Core sudah aktif karena tanggung jawab keduanya
berbeda. Gunakan root `deploy.sh`; jalankan `update` untuk pull + rebuild atau `restart`
untuk restart tanpa build. Pastikan `/health` dan `/ready` berhasil sebelum menghubungkan
OpenClaw.

Production saat ini harus memakai satu replica karena session conversation disimpan
in-memory dengan TTL. Untuk horizontal scaling, tambahkan shared Redis session store
dengan TTL dan locking/version check; sticky session saja tidak cukup saat failover.

Routing fraud/payment juga mengenali indikator dasar English, Indonesian, Malay, Spanish,
French, dan German. Untuk bahasa lain, respons akan fallback ke English sampai provider
multilingual terstruktur diaktifkan.
