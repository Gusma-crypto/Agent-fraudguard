# Catatan Proyek FraudGuard AI

Dokumen ini adalah catatan operasional untuk handoff developer: apa yang berubah, alasan keputusan, status validasi, risiko, dan pekerjaan berikutnya.

## Status saat ini

- **Tanggal:** 2 September 2026
- **Tahap:** agent conversation/reasoning/orchestration terpisah dari Core; deployment VPS belum dijalankan.
- **Kompetisi:** AI HackFest 2026, Batch 1, periode VPS 1–5 September 2026.
- **Runtime pilihan:** OpenClaw.
- **Track:** Digital Safety & Public Good.
- **Subkategori:** Cyber Security & Anti Scam.
- **Prioritas:** P0 end-to-end sebelum P1 atau UI polish.

## Security hardening — 2026-09-02

- Deploy Core `deploy-vps.sh` sekarang gagal dengan exit code `1` jika `/ready` tidak
  tercapai dalam batas waktu.
- Learning patterns/candidates/evaluations diputuskan sebagai global governance data;
  endpoint memakai scope `learning:global-read` dan `learning:global-review`. Experience
  tetap tenant-scoped.
- Core menolak `context.signals`/payload signal list dari caller dan RiskEngine tidak
  lagi menghitung daftar signal mentah sebagai otoritas.
- Webhook delivery mem-pin koneksi TCP ke alamat publik yang divalidasi per koneksi,
  mempertahankan TLS SNI dan mematikan redirect untuk mencegah DNS rebinding.
- Agent fail-closed terhadap malformed Core error/data response.
- Scaling session belum diaktifkan: produksi harus satu replica in-memory; Redis shared
  store dengan TTL dan version locking adalah prasyarat scale-out.

## Keputusan produk aktif

- FraudGuard adalah anti-scam payment intervention agent, bukan hanya transaction-anomaly dashboard.
- OpenClaw/native runtime bertindak sebagai harness agent; Policy Engine di `logic-backend-server` adalah final authority.
- Gunakan satu orchestrator dengan tiga skill: `fraud-detection`, `safety-payment`, dan `realtime-intervention`.
- Seluruh payment action adalah sandbox/simulasi, bukan integrasi bank nyata.
- `Report != Evidence != Verified Fact != Fraud Confirmation`.
- Session memory agent bersifat in-memory dan non-authoritative; learning/experience authoritative berada di Core.
- Report/evidence UI, human review, dan memory promotion adalah P1.
- Semua demo data wajib sintetis atau dimasking.

## Perubahan workspace — 2026-09-01

## Konsolidasi Core dan Agent — 2026-09-02

- Target final hanya dua runtime: `fraudguard-ai-agent` dan `logic-backend-server`.
- Package agent aktif adalah `src/fraudguard_agent`; ia tidak mengakses PostgreSQL dan tidak memiliki score/policy engine.
- Conversation API, session context, deterministic planner, typed tool registry, three-layer guardrails, trace propagation, idempotency, dan fail-closed behavior sudah diimplementasikan.
- Provider model tetap configurable secara arsitektural, tetapi deployment ini memakai provider `deterministic` tanpa API key eksternal.
- Validasi: 8 test runtime/integration/security lulus dan Ruff bersih pada Python 3.12 Docker image.

## Active fraud response — 2026-09-02

- Fraud detection diperluas dari analyze-only menjadi analyze-then-act.
- Otorisasi tetap berasal dari policy decision Core; agent hanya memetakan decision
  non-`ALLOW` ke intervensi reversible yang tercatat dan diaudit.
- Endpoint intervensi Core dibuat idempotent untuk mencegah duplikasi saat retry.
- External enforcement sengaja tetap di luar scope dan tool allowlist.

## Audit checklist submission — 2026-09-02

- `docs/SUBMISSION-CHECKLIST.md` sekarang memisahkan kesiapan source, bukti VPS/OpenClaw,
  acceptance golden demo, keamanan artefak, video, artikel, dan final submission.
- Berdasarkan terminal operator, Core (`api`, `worker`, `proxy`, PostgreSQL) sudah sehat
  di VPS. Agent image terbaru dan eksekusi tiga skill melalui OpenClaw belum terbukti.
- Test source saat ini berisi 15 test agent dan 33 fungsi test Core. Regression agent
  terbaru lulus `15 passed in 1.57s` dan Ruff lulus untuk `src tests scripts`; regression
  Core terbaru tetap harus dijalankan dan outputnya disimpan sebelum submit.
- Blocker utama: deploy agent final, buktikan `/ready`, pasang/deteksi skill OpenClaw,
  rekam golden trace, sanitasi/backup artefak, lalu selesaikan video dan artikel.

## Installer OpenClaw dan CLI komunikasi — 2026-09-02

- `scripts/install_openclaw.sh` memasang tiga skill dan client ke workspace yang dibaca
  dari OpenClaw CLI atau diberikan lewat `--workspace`/`--profile`/`--dev`.
- Konflik tidak ditimpa secara default; `--force` membuat backup di workspace sebelum
  replacement. Installer tidak menulis secret dan tidak mengubah system `PATH`.
- `scripts/fraudguard_agent_cli.py` menyediakan health, ready, tools, session-create,
  dan chat. HTTP dibatasi ke loopback; remote endpoint wajib HTTPS.
- Credential dibaca dari environment atau key file luar workspace dengan permission
  `600`. Skill dilarang fallback ke `curl`, generic HTTP, atau policy lokal.
- Test integrasi mencakup authenticated structured chat, penolakan HTTP non-loopback,
  idempotent install, conflict preservation, dan recoverable force backup.
- Installer telah diverifikasi pada workspace OpenClaw lokal terisolasi: ketiga skill
  terdeteksi sebagai workspace skill, eligible, dan instalasi ulang tidak mengubah file.
  Pembuktian yang sama pada workspace OpenClaw VPS tetap pending.
- Target Docker test membawa skill source agar perilaku installer ikut diuji, sementara
  target runtime produksi tetap hanya berisi package agent.
- `skills/skill-creator/SKILL.md` menyediakan workflow pembuatan/validasi skill dengan
  bahasa sederhana. Instalasinya opt-in melalui `--with-creator`; tiga skill operasional
  tetap menjadi default agar surface produksi tidak bertambah.
- Runtime chat kini menegosiasikan `en`, `id`, atau `ms`, mengembalikan language code,
  dan melokalkan pesan safety/failure tanpa menerjemahkan decision atau trace Core.

### Secret production, rollback, dan recovery VPS

Area yang berubah:

- `src/fraudguard/container_entrypoint.py`, `Docker/Dockerfile`, dan `Docker/compose.production.yaml` — secret root-only dibaca sebelum proses menjatuhkan UID/GID secara permanen ke `fraudguard`; hanya capability baca `DAC_READ_SEARCH` dan transisi `SETUID`/`SETGID` tersedia sebelum privilege drop.
- `scripts/deploy_vps.sh` — fallback Compose v1/v2, timeout per request, batas readiness, deteksi state container dan restart count, serta log diagnostik otomatis.
- `src/fraudguard/memory/repository.py` — mutasi JSON dilakukan pada deep-copy dan baru dipublikasikan setelah validasi/tulis berhasil sehingga exception benar-benar rollback.
- `scripts/backup_database.sh` dan `scripts/restore_database.sh` — online backup SQLite, integrity/schema validation, backup pra-restore, atomic replacement, ownership, dan readiness pasca-restore.
- `tests/test_compose_integration.py` dan regression tests — pengujian Compose produksi nyata bersifat opt-in agar suite default tetap dapat berjalan tanpa Docker.

Keputusan:

- Secret host tetap mode `600`; `chmod 644` dilarang sebagai workaround.
- Proses aplikasi, bukan hanya konfigurasi image, harus terbukti berjalan non-root.
- Restore memerlukan `--confirm`, tidak boleh berjalan tanpa backup pra-restore, dan tidak menghapus named volume.
- Folder `backups/` diabaikan Git dan harus direplikasi operator ke storage terenkripsi di luar VPS.

Status validasi akhir dicatat setelah suite Python, shell syntax, Docker build, dan integration test Compose selesai dijalankan.

### Adapter CLI lokal OpenClaw

`src/fraudguard/adapter.py` dan entry point `fraudguard-adapter` menyediakan tujuh
operasi tetap yang memanggil API loopback VPS. Adapter tidak menerima URL bebas,
tidak mengekspos shell/SQL/repository, membaca API key dari file atau environment,
menghapus field idempotency internal sebelum mengirim body, membatasi timeout dan
ukuran response, serta mengembalikan error typed tanpa secret.

OpenClaw harus diberi allowlist command `fraudguard-adapter` dengan subcommand yang
ditentukan; jangan memberi izin generic Python, curl, docker, atau shell. Aktivasi
agent baru dianggap selesai setelah command allowlist dan satu golden flow diuji
di Gateway VPS.

### Pemisahan tanggung jawab repository - 2026-09-01

Area dan keputusan:

- `src/fraudguard/` kini satu-satunya isi aktif `src/`; `core/` menjadi facade stabil, `prompts/` membatasi instruksi model, dan `providers/` mendefinisikan kontrak runtime-neutral. Implementasi orchestrator tetap tunggal di `agent/`.
- `scripts/` memuat setup, diagnosis, install, repair, release, database init, validator, bundle export, dan deploy VPS. `install.js`/`repair.js` dry-run kecuali diberi `--apply`.
- `commands/` memuat empat template command cepat agent. Template ikut bundle, tetapi status native slash-command tetap pending verifikasi Gateway VPS.
- `Docker/` memiliki seluruh artefak container. Contoh konfigurasi Gateway dipisahkan ke `openclaw-plugin/` karena bukan konfigurasi Docker.
- `database/`, `tests/`, `reference/`, `data/`, `pyproject.toml`, dan `USER.md` dipindahkan keluar `src/`. Database SQLite 102400 byte beserta WAL/SHM dipertahankan dan lolos `PRAGMA integrity_check`.

Validasi selesai: validator layout, 34 Python tests, smoke flow, JavaScript syntax/doctor/dry-run, bundle 26 file, Compose parse, shell syntax, serta plugin build/validation lulus. Docker engine tetap tidak tersedia secara lokal.

### Hardening P0, adapter OpenClaw, dan mode production

Area yang berubah:

- `openclaw-plugin/` — plugin TypeScript resmi dengan tujuh `contracts.tools`, TypeBox schema, model overlay, loopback-only fetch, response cap, dan API key dari protected config.
- `src/fraudguard/policy/engine.py` — rule/effect/fallback dibaca dan dieksekusi dari `policy/policy.yaml`.
- `src/fraudguard/config.py` — non-loopback wajib API key minimal 24 karakter serta dukungan Docker secret file.
- `schemas/` dan `src/fraudguard/schema_validation.py` — validasi nested, length/item bounds, enum, dan additional-properties enforcement.
- `src/fraudguard/memory/*repository.py` — `state_version` bertambah hanya jika state benar-benar berubah.
- `tests/test_safety_evals.py` — E3 invalid model output, E7 prompt injection, E8 exact tool inventory, dan bounded model overlay.
- `Docker/compose.production.yaml` dan `scripts/deploy_vps.sh` — mode deploy VPS dengan secret, loopback, resource/log limits, health wait, dan smoke flow.

Keputusan:

- OpenClaw melakukan model reasoning dan mengirim `model_analysis` terbatas; backend tidak menerima score, policy, action, repository state, atau generic tool selection dari model.
- Equivalent before/after guards aktif di plugin dan backend sehingga keamanan tidak bergantung pada file hook Markdown.
- Plugin telah lulus build, manifest generation, `openclaw plugins validate`, dan dry-run package lokal.
- Status belum `VPS_ACTIVE` sampai plugin di-install, Gateway direstart, runtime inventory di-inspect, dan real model call tercatat di VPS.

Validasi:

- 34 Python tests termasuk policy dinamis, E3/E7/E8, state version, dan repository/deployment separation: lulus.
- Project validator, golden smoke, TypeScript build, OpenClaw plugin validation, dan npm audit: lulus.
- Container production sudah dibuild dan dijalankan lokal dengan Python 3.12; akses shell/target VPS organizer, konfigurasi Gateway aktif, dan binding agent masih belum tersedia.

### Layout konsolidasi lama (superseded)

Layout lama pernah menaruh database, tests, deployment, reference, metadata, dan
runtime data di bawah `src/`. Keputusan tersebut sudah digantikan oleh pemisahan
tanggung jawab di atas. Path aktif sekarang adalah `src/fraudguard/`, `database/`,
`tests/`, `reference/`, `data/`, `Docker/`, dan root `pyproject.toml`.

### OpenClaw aktif

File yang diubah:

- `AGENTS.md` — aturan produk, policy, evidence/memory safety, security, delivery, dan sinkronisasi dokumentasi.
- `SOUL.md` — misi evidence-driven dan perlindungan tanpa tuduhan otomatis.
- `IDENTITY.md` — identitas FraudGuard AI.
- `TOOLS.md` — catatan runtime OpenClaw, sandbox, database, dan detail VPS pending.
- `HEARTBEAT.md` — dinonaktifkan selama P0.
- `USER.md` — konteks pemilik proyek dan preferensi kerja.
- `BOOTSTRAP.md` — dihapus setelah onboarding selesai; dapat dipulihkan dari Git/reference.

### Spesifikasi dan kontrak

Area yang diubah:

- MASTER/PRD disatukan pada skenario social engineering, intervention, incident/audit, dan evidence-backed Fraud Memory.
- Policy threshold dan intervention outcome dibuat konsisten.
- Tiga `SKILL.md` dilengkapi frontmatter, input/output, tool boundary, dan failure behavior.
- Skenario Case #1 → review/promote → Case #2 diperbaiki.
- API dibagi menjadi P0 dan P1.
- Test plan dan submission checklist diselaraskan dengan playbook.
- Struktur pack dipindahkan ke root dan referensinya diperbaiki.
- `README.md` diubah menjadi panduan developer; `guide_user.md`, `changelog.md`, dan `catatan_project.md` dijadikan dokumentasi wajib setiap perubahan.
- `MANIFEST.md` diperbarui untuk mencakup dokumen operasional baru.

## Validasi terakhir

### Core Python dan hardening backend

Area yang berubah:

- `src/fraudguard/agent/` - orchestrator, runtime composition, dan payload-bound idempotency.
- `src/fraudguard/validation.py` - strict finite amount, JSON boolean, currency, secret, dan intervention validation.
- `src/fraudguard/schema_validation.py` - recursive schema enforcement.
- `src/fraudguard/server.py` - `/ready`, optional API key, body limit, dan safe exception logging.
- `tests/` - regression coverage untuk seluruh temuan backend.

### Database SQLite lokal

Area yang berubah:

- `database/migrations/001_initial.sql` — schema P0 dan append-only audit triggers.
- `src/fraudguard/memory/sqlite_repository.py` — koneksi, transaksi, seed, persistence, dan restart-safe state.
- `src/fraudguard/config.py` dan `agent/runtime.py` — pemilihan storage melalui environment.
- `scripts/init_database.py` — init dan integrity check lokal.
- `tests/test_database.py` — schema, restart, multi-runtime, dan audit immutability.

Keputusan:

- SQLite menjadi default P0 karena dependency-free dan paling stabil untuk demo satu host.
- JSON dipertahankan sebagai fallback eksplisit, bukan menjadi dua authority runtime.
- OpenClaw hanya boleh mengakses operasi FraudGuard yang di-allowlist melalui adapter; model tidak diberi arbitrary SQL.
- PostgreSQL ditunda sampai kebutuhan multi-service/worker benar-benar ada.

Validasi:

- Empat database tests lulus, termasuk persistence setelah runtime restart.
- `PRAGMA integrity_check` menghasilkan `ok`.
- Audit ditolak jika dicoba diubah dan dilindungi trigger database.
- Dua runtime instance membaca state terbaru dalam transaksi tanpa lost update pada pengujian.

### Batas akses orchestrator dan skill OpenClaw

Area yang berubah:

- `agents/fraudguard-orchestrator.md` — tujuh operasi adapter yang boleh diekspos, routing/state gate, data boundary, larangan tool, fallback, dan acceptance criteria registrasi.
- `skills/*/SKILL.md` — invocation, input/output, side effect, tool, dan failure boundary diselaraskan dengan handler Python serta schema masing-masing.
- `tools/TOOL-CONTRACTS.md` — internal function allowlist dipisahkan dari tool yang benar-benar diregistrasikan ke OpenClaw.
- `evals/EVAL-PLAN.md` — negative eval untuk inventory tool dan percobaan capability terlarang.

Keputusan:

- Adapter sebaiknya mengekspos operasi orchestrator, bukan fungsi repository/tool level rendah.
- Model tidak menerima raw state, SQLite/SQL, filesystem path, threshold/weight, risk score buatan caller, atau policy override.
- Risk Engine menghitung skor dan Policy Engine tetap satu-satunya final authority.
- Kontrak ini belum dianggap enforcement OpenClaw sampai adapter, hook/equivalent guards, dan eval registrasi benar-benar berjalan.

Validasi:

- Ketiga `SKILL.md` lulus `skill-creator/scripts/quick_validate.py`.
- Nama handler, input, output schema, state effect, dan keputusan policy dibandingkan dengan backend yang executable.
- Tidak ada threshold atau weight yang diduplikasi ke kontrak skill.

### Pemisahan bundle OpenClaw dan Docker backend

Area yang berubah:

- `scripts/export_openclaw_bundle.py` — menghasilkan ZIP agent dari explicit allowlist.
- `Docker/Dockerfile`, `Docker/compose.yaml`, dan `.dockerignore` — backend Python non-root, loopback-only, persistent SQLite, dan build context terpisah.
- `Docker/DEPLOYMENT-MAP.md` dan `Docker/docker.env.example` — peta file upload/build dan environment non-secret.
- `tests/test_deployment.py` — memastikan ZIP tidak memuat backend dan image tidak memuat workspace agent.

Keputusan:

- Tetap gunakan satu OpenClaw orchestrator dengan tiga skill; tidak ada frontend agent kedua.
- Upload ke OpenClaw hanya ZIP hasil exporter, bukan repository lengkap.
- Docker menerima hanya `pyproject.toml`, `src/fraudguard/`, `database/`, `policy/`, dan `schemas/`.
- Host OpenClaw berkomunikasi ke container melalui named operations dan API loopback; API key tetap di environment.

Status:

- ZIP OpenClaw berhasil dibuat dengan 26 file allowlisted termasuk MASTER dan empat command cepat agent.
- Tiga deployment separation tests lulus; Docker build aktual masih pending karena CLI Docker lokal tidak tersedia.

Keputusan penting:

- Client tidak boleh membuat risk score atau policy state melalui intervention endpoint.
- `POST /interventions` hanya me-resolve intervention yang sudah dibuat dari payment-policy trace.
- Idempotency key menyimpan request fingerprint; payload berbeda dengan key sama mendapat HTTP 409.
- Incident dan candidate hanya dibuat jika final policy adalah `KEEP_HOLD_AND_ESCALATE`.
- API key opsional untuk local loopback, tetapi wajib sebelum route API diekspos melalui reverse proxy.

Hasil validasi terbaru:

- Dua puluh tiga Python unit/integration tests: lulus.
- Golden-flow smoke: lulus sampai hold, intervention, escalation, incident, candidate `UNDER_REVIEW`, dan audit.
- Policy, schema, scenario, manifest, pyproject, dan Python compilation diperiksa oleh project validator.

- Tiga skill: valid.
- Policy YAML: valid.
- Semua simulator JSON: valid.
- Manifest: seluruh path ditemukan.
- Konfigurasi bootstrap: selesai dan backup tersedia.
- `git diff --check`: tidak ada error; hanya normalisasi LF/CRLF Windows yang mungkin dilakukan Git.

## Konsolidasi instruksi — 2026-09-01

Tujuan: mencegah agent membaca dua authority untuk concern yang sama.

Keputusan:

- `AGENTS.md` menjadi satu-satunya authority workspace behavior dan safety.
- MASTER menjadi satu-satunya authority scope, P0/P1, delivery, dan HackFest.
- `policy/policy.yaml` menjadi satu-satunya authority threshold, override, dan fallback.
- Tiga `SKILL.md` hanya mengatur perilaku masing-masing skill.
- Contract agent/API/database/tool/hook/test/eval tidak boleh mengoverride authority di atasnya.
- `reference/` dinyatakan tidak aktif dan dilarang dimuat saat startup agent.

File yang digabung/dirapikan:

- Unique rules dari `docs/PROJECT-RULES.md` telah masuk ke `AGENTS.md`; dokumen lama diarsipkan.
- Rencana lima hari aktif hanya berada di MASTER; `docs/IMPLEMENTATION-PLAN.md` diarsipkan.
- Repository map aktif hanya berada di README; `docs/FILE-MAP.md` diarsipkan.
- `openclaw-additions/` yang sudah diterapkan dipindahkan ke `reference/archive/openclaw-additions/`.
- Orchestrator dan hook diperjelas sebagai contract, bukan authority/runtime activation kedua.

Tidak ada dokumen yang dihapus permanen. Semua sumber superseded tetap tersedia di `reference/archive/` untuk audit.

## Risiko dan detail pending

- Plugin OpenClaw tujuh operasi sudah dibangun dan divalidasi melalui CLI lokal terisolasi, tetapi instalasi pada workspace aktif, agent binding, model, startup command, dan eksekusi tool end-to-end belum dikonfirmasi di VPS.
- Docker tidak ditemukan pada environment Windows/VS Code; build container aktual dan registrasi plugin pada Gateway organizer harus diuji di VPS.
- Endpoint, model default, limit, dan autentikasi AI belum dikonfirmasi.
- Port publik, domain, service manager, dan mekanisme backup VPS belum dikonfirmasi; Docker production sudah dibuild/run lokal dan backup SQLite diuji melalui SQLite Online Backup API.
- Core/API, SQLite P0, serta adapter plugin OpenClaw sudah diimplementasikan; PostgreSQL multi-service, web UI, reverse proxy, dan deployment service host belum diimplementasikan.
- Python 3.11+ pada VPS belum diverifikasi.
- VPS tidak memiliki swap; hindari build berat berjalan bersamaan dengan demo service.
- Jangan menulis kredensial atau token ke dokumentasi maupun Git.

## Pekerjaan berikutnya

1. Verifikasi Python, OS/CPU, workspace OpenClaw aktif, model, port, dan service manager di VPS.
2. Jalankan validator, 34 tests, database init/integrity check, dan smoke flow di VPS.
3. Build/jalankan `docker compose -f Docker/compose.yaml` dengan `FRAUDGUARD_API_KEY`, lalu uji `/health` dan `/ready` pada loopback.
4. Upload bundle dan plugin OpenClaw, daftarkan tujuh operasi serta guard ekuivalen, lalu jalankan E3/E7/E8 pada Gateway VPS sebelum menyebut OpenClaw aktif.
5. Tambahkan reverse proxy, UI demo minimum, backup, dan bukti video setelah adapter stabil.
- Memulihkan package `src/fraudguard/memory/` yang sebelumnya direferensikan runtime tetapi tidak ada: repository JSON atomic, repository SQLite WAL/transactional, retrieval masked/bounded, confidence helper, dan package export.
- Validasi Python 3.11 lulus 34/34 test dan smoke flow lulus. Verifikasi container production juga lulus readiness, API key, audit, restart/idempotency, SQLite integrity, dan backup; validasi Python 3.12 dijalankan melalui image dengan API key sintetis.
- `scripts/release.sh` sekarang memvalidasi versi Python dan menerima `PYTHON_BIN`, sehingga host dengan `python3` 3.10 tidak gagal secara ambigu.
- Tutorial uji VPS/OpenClaw ditambahkan ke `guide_user.md` dan ditautkan dari `README.md`; status remote tetap pending sampai dijalankan pada Gateway organizer.
- `scripts/deploy_vps.sh` sekarang otomatis memilih `docker compose` atau `docker-compose`, sesuai runtime Docker yang tersedia di VPS.
