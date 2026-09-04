# Panduan Pengguna FraudGuard AI Agent

Pada deployment OpenClaw, percakapan frontend masuk melalui FraudGuard OpenClaw Bridge.
OpenClaw menjadi satu-satunya pemilih skill dan urutan tool. Tool adapter hanya
memvalidasi serta menjalankan satu tool yang dipilih OpenClaw; FraudGuard Core tetap
menentukan evidence, risk, policy, dan keputusan.

Di frontend, status harus tertulis **OpenClaw Orchestrator**. Saat analisis berlangsung,
panel ringkas hanya memperlihatkan tahapan seperti klasifikasi, ekstraksi, verifikasi,
normalisasi evidence, korelasi, risk, dan policy. Rincian sumber tersedia di Evidence/Audit.
Jalur browser memakai typed function tool dari Bridge; CLI hanya menjadi fallback untuk
session OpenClaw TUI/admin. Jika Core tidak memberi hasil, UI menampilkan status belum
terverifikasi dan tidak menerima score atau keputusan buatan model.

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

Hasil verifikasi intervensi hanya berlaku untuk satu turn. Setelah status selesai,
permintaan audit dengan `trace_id` pada session yang sama membaca audit Core dan tidak
mengirim ulang hasil verifikasi sebelumnya.

Permintaan OTP, password, PIN, atau CVV diperlakukan sebagai indikator risiko tanpa
mengumpulkan nilainya. Jangan pernah memasukkan nilai rahasia tersebut ke chat. Agent
harus membedakan saran keamanan umum dari keputusan Core dan tidak boleh membuat vonis
fraud sendiri ketika Core mengembalikan `ALLOW`.

Untuk kasus link yang meminta pengisian form/OTP, hentikan interaksi, tutup halaman, dan
hubungi penyedia lewat kanal resmi yang dicari sendiri. Untuk telepon hadiah yang meminta
transfer, akhiri telepon dan jangan mengikuti panduan transfer sambil tetap tersambung.
FraudGuard akan memilih jalur `fraud-detection` atau `social-engineering` dan dapat mencatat
intervensi yang diotorisasi Core; pencatatan itu tidak membatalkan transaksi eksternal.

Lookup nomor/rekening/domain dapat diberikan sebagai context non-rahasia
`intelligence_query`. Status `UNVERIFIED`, `INSUFFICIENT_INTELLIGENCE`, atau
`PENDING_AGENT_DISCOVERY` berarti bukti belum cukup—bukan berarti aman atau pasti fraud.
Jika Core dikonfigurasi dengan provider berlisensi, `deep_search=true` akan meminta Core
menjalankan provider public-search atau URL/domain; kegagalan provider ditampilkan sebagai
status provider dan tidak dianggap sebagai bukti aman maupun bukti fraud.
Untuk setiap hasil lookup, periksa bagian `intelligence.sources` dan
`intelligence.evidence`. Bila data tersedia, Agent menampilkan URL HTTPS sumber,
metode akses, waktu observasi, ringkasan, confidence, dan status verifikasinya. Bila
keduanya kosong, hasil wajib menyatakan bahwa belum ada sumber/bukti pendukung—jangan
menganggap hasil kosong sebagai bukti bahwa identifier aman.
Label “snapshot tersimpan” berarti excerpt minimum telah disimpan Core agar temuan masih
dapat diaudit saat link mati. Snapshot tersebut tetap mengikuti status verifikasi dan
tidak boleh diperlakukan sebagai vonis otomatis.

## Bukti demo dan submission

Sebelum merekam atau mengirim submission, ikuti `docs/SUBMISSION-CHECKLIST.md`. Jangan
menampilkan `.env`, API key, Authorization header, data personal, atau transaksi nyata.
Gunakan hanya skenario sintetis dan pastikan trace dari respons agent dapat dibaca pada
audit Core yang sama.

## OpenClaw dan CLI

Operator dapat memasang integrasi dengan `./scripts/install_openclaw.sh`. Setelah itu,
OpenClaw menggunakan lima skill produksi dan CLI `<workspace>/tools/fraudguard-agent`
untuk berkomunikasi dengan API agent. Instruksi instalasi, key file mode `600`, contoh
chat, payment, dan intervention tersedia di `docs/OPENCLAW-INSTALL.md`.

Untuk satu analisis normal, OpenClaw memilih satu skill utama dan tidak menjalankan ulang
analisis hanya untuk mengisi kartu frontend. Hasil score, policy, evidence, status action,
dan trace ditampilkan sesuai respons Core. Tidak adanya evidence bukan bukti bahwa entity
aman atau pasti fraud.

Sesudah update repository di VPS, jalankan `./deploy.sh update`, kemudian
`./scripts/install_openclaw.sh --force`, `openclaw skills check`, dan buka session baru.
Installer menyimpan skill lama dalam `.fraudguard-backups/<timestamp>` sehingga update
dapat diaudit dan dipulihkan secara manual bila diperlukan.

Pesan `Missing runtime source: openclaw-workspace/USER.md` berarti paket source di VPS
belum lengkap, bukan error OpenClaw atau Core. Operator harus memperbarui repository dan
memastikan template `USER.md` sudah terlacak Git sebelum menjalankan installer kembali.

Output `Skills Status Check` dengan `Agent: main` bukan verifikasi agent FraudGuard.
Deployment harus menargetkan `OPENCLAW_AGENT_ID=fraudguard` dan memasang allowlist lima
skill pada konfigurasi agent tersebut. Skill bundled yang kekurangan dependency tidak
perlu dipasang selama tidak digunakan oleh FraudGuard.

Untuk belajar membuat skill, jalankan installer dengan `--with-creator`, buka session
OpenClaw baru, lalu tulis misalnya `Buat skill dari capability fraud-detection v1`.
`skill-creator` hanya untuk development: ia memeriksa kontrak Core, mencegah duplikasi,
dan tidak boleh membuat score, policy, endpoint, atau permission sendiri.

Service bridge dan tool adapter tetap harus dideploy walaupun Core sudah aktif. Gunakan
root `deploy.sh`; jalankan `update` untuk pull + rebuild atau `restart` tanpa build.
Pastikan OpenClaw `/v1/responses` aktif, container `bridge` sehat, dan endpoint bridge
`/ready` mengembalikan `orchestrator=openclaw`.

Production saat ini harus memakai satu replica karena session conversation disimpan
in-memory dengan TTL. Untuk horizontal scaling, tambahkan shared Redis session store
dengan TTL dan locking/version check; sticky session saja tidak cukup saat failover.

## Intelligence multi-entity

Untuk memeriksa satu pesan yang berisi beberapa entity, kirim melalui
`context.intelligence_input`:

```json
{
  "text": "Nomor ini mengaku saya menang hadiah dan meminta transfer Rp3 juta.",
  "phone": "+6281234567890",
  "bank_account": "BCA 1234-5678-90",
  "transaction_context": {"recipient_is_new": true}
}
```

Agent meneruskan input ke Core. `ingestion` dan `routed_entities` menjelaskan entity yang
diproses, `evidence` berisi observation, `claims` berisi pernyataan terstruktur, sedangkan
`risk` dan `policy` adalah keputusan authoritative Core. Jangan menyamakan evidence dengan
claim terverifikasi atau keputusan.

Jika intervention dijawab dengan fakta typed, Core mengembalikan `reassessment`. Tampilkan
hasil reassessment terbaru dan jangan menyimpan hasil verifikasi sebagai fakta permanen di
session Agent.

Dashboard web terpadu memakai halaman Analyze sebagai entry point. Data yang ditampilkan
mengikuti urutan `ingestion → entities → provider status → evidence → claims → risk →
policy`. Jika Core mengembalikan keputusan non-ALLOW, Agent dapat menampilkan intervention
yang diotorisasi Core; dashboard tidak mengklaim bahwa rekening atau transaksi bank nyata
telah diblokir.

Routing fraud/payment juga mengenali indikator dasar English, Indonesian, Malay, Spanish,
French, dan German. Untuk bahasa lain, respons akan fallback ke English sampai provider
multilingual terstruktur diaktifkan.
