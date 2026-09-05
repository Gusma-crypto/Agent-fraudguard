# Catatan Proyek FraudGuard AI

## Sinkronisasi runtime lintas kanal — 2026-09-05

- Jalur web dan Telegram sama-sama melalui OpenClaw Bridge lalu typed Core tools.
- OpenClaw mengatur skill dan bahasa penjelasan; Core menentukan seluruh protected field.
- Bridge mempertahankan narasi manusiawi hanya jika ada hasil Core dan tetap fail closed saat
  tool/Core tidak memberi hasil authoritative.
- Telegram melabeli narasi sebagai penjelasan berbasis Core agar tidak bercampur dengan
  observation, claim, risk, atau policy decision.

Dokumen ini adalah catatan operasional untuk handoff developer: apa yang berubah, alasan keputusan, status validasi, risiko, dan pekerjaan berikutnya.

## Status saat ini

### Telegram consent adapter — 2026-09-05

- Area: OpenClaw Bridge, Core client, channel session model, runtime policy, Docker env,
  operator setup, and tests.
- Flow: Telegram webhook → consent check in Core → OpenClaw primary skill → typed Core
  tools → authoritative result → Telegram response.
- Consent is fail-closed. Before `GRANTED`, message content is not analyzed or persisted
  and the user must resend it. Groups require `/cek`, `/analisis`, mention, or bot reply.
- Core receives only HMAC pseudonyms (`ch_*`, `evt_*`), not raw Telegram user/chat IDs.
- Validation: Agent Ruff passed, 50 tests passed in the Docker test image, the runtime
  image built successfully, and its webhook setup CLI is present.
- Remaining deployment check: apply Core migration, rebuild Agent Bridge, register the
  real HTTPS webhook, and run one synthetic end-to-end message on the VPS.
- WhatsApp remains a future official Business API adapter; only the shared Core channel
  consent contract is prepared.
- UX fix: `/cek` or `/analisis` without target content now returns usage instructions;
  command text is stripped before private-chat analysis. API contract is synchronized.
- VPS evidence: Caddy now reaches the Telegram Bridge (manual requests return Bridge JSON,
  not frontend Nginx HTML), consent UI works, Docker can reach Gateway port `18789`, and
  authenticated `GET /v1/models` returns `200` with `openclaw/fraudguard` available.
- Current blocker: after Gateway token synchronization Telegram can remain silent. A real
  `POST /v1/responses`, Bridge `/ready`, Telegram delivery log, and final Core trace are
  still unverified. README/user guide now document this staged diagnosis and do not treat
  `/v1/models` success as end-to-end completion.
- Telegram setup now registers commands for five production skills: `cek`/`analisis`,
  `bayar`, `intervensi`, `sosial`, and `intelijen`, plus onboarding/privacy commands.
  Operators can update or inspect the menu through `commands-set` and `commands-info`.
- Consented analyses now send a skill-aware loading message before invoking OpenClaw and
  edit that same message into the final response, preventing a silent wait and avoiding
  a long list of progress messages.
- Docker test packaging now includes `openclaw-workspace/`; previously the full suite
  could fail its installer regression because the test image omitted required templates.
- Added a managed Telegram-to-intervention demo runbook installed under workspace
  `docs/`, command aliases from the demo script, and a 30-minute in-memory active
  intervention reference. Browser context cannot inject the trusted intervention field.
- Telegram payment turns receive a server-generated `evt_<HMAC>` external payment ID;
  the value is accepted only on the internal Telegram path and prevents duplicate Core
  payment creation for a retried update.
- Telegram now sends an immediate `typing` chat action and refreshes it every four seconds
  while OpenClaw/Core runs. The task is cancelled on every analysis exit path and does not
  represent backend progress state.
- Correctness fix: explicit fraud/social/intelligence skills expose only
  `intelligence_lookup`, require at least one tool call, force `deep_search=true`, and attach
  the original message as the ingestion envelope. This prevents an OpenClaw-only answer
  from being shown as a Core verdict.
- Presentation fix: final Telegram output is Indonesian and human-readable while retaining
  Core codes in parentheses. A shortlink is explained as hiding its final destination;
  “provider mencatat respons gagal” is shown only when provider evidence contains
  `URL_UNREACHABLE`.
- Native Telegram typing was hardened: refresh interval is three seconds, an initial or
  periodic transient API error no longer disables subsequent attempts, and lifecycle logs
  contain no chat identifier or message content. Telegram clients still control whether
  the top-bar animation is rendered.
- Validation: complete Agent suite passed (62 tests) and Ruff passed in the Docker test image.

- **Tanggal:** 2 September 2026
- **Tahap:** agent conversation/reasoning/orchestration terpisah dari Core; deployment VPS belum dijalankan.
- **Kompetisi:** AI HackFest 2026, Batch 1, periode VPS 1–5 September 2026.
- **Runtime pilihan:** OpenClaw.
- **Track:** Digital Safety & Public Good.
- **Subkategori:** Cyber Security & Anti Scam.
- **Prioritas:** P0 end-to-end sebelum P1 atau UI polish.

## Dedicated OpenClaw runtime workspace - 2026-09-04

- `openclaw-workspace/` sekarang menjadi sumber tunggal untuk tujuh file kontrak root
  yang dipasang ke `/root/.openclaw/workspace-fraudguard`.
- Runtime produksi memakai lima skill dengan satu primary skill per turn. Tiga protection
  skill tetap terlihat sebagai capability produk; `social-engineering` dan
  `intelligence-search` menangani routing khusus tanpa membuat keputusan sendiri.
- `malicious-url` dipensiunkan dari runtime: perilaku link/login/OTP masuk
  `fraud-detection`, sedangkan lookup reputasi URL/domain masuk `intelligence-search`.
- Installer menyimpan konflik dan skill lama sebagai backup yang dapat dipulihkan,
  memasang file root mode `600` dan CLI mode `700`, serta tidak mengubah config global,
  credential, memory, atau file buatan operator.
- Komponen berubah: template workspace, installer, lima kontrak skill, Bridge allowlist,
  fallback planner/runtime, regression test, README, user guide, dan install guide.
- Runtime `AGENTS.md` mengadopsi bagian terbaik dari referensi operator: integritas field
  Core, maksimum satu primary assessment per turn, anti-duplikasi, evidence kosong bukan
  bukti aman/fraud, isolasi session/memory, read-only case runtime, dan format hasil.
  Aturan heartbeat proaktif, self-modification, dan pemanggilan CLI `chat` tidak diambil
  karena bertentangan dengan boundary produksi.
- Validasi lokal final: 42 test lulus, Ruff bersih, Python compile berhasil, shell syntax
  valid, installer idempotent, dan `git diff --check` bersih.
- Perbaikan deployment: aturan global `.gitignore` untuk `USER.md` sebelumnya membuat
  `openclaw-workspace/USER.md` tidak ikut commit. Pengecualian khusus sekarang memastikan
  ketujuh root contract tersedia setelah clone/pull di VPS.
- Audit VPS menunjukkan `openclaw skills check` masih berjalan sebagai `Agent: main` dan
  menampilkan katalog global. Default Bridge telah diubah menjadi agent `fraudguard`;
  operator perlu menetapkan allowlist lima skill pada entry agent tersebut. Skill global
  seperti `malicious-url` tidak perlu dihapus karena akan terisolasi oleh allowlist.
- Risiko tersisa: binding agent `fraudguard` ke workspace dan panggilan model nyata harus
  diverifikasi pada VPS; kegagalan provider/model harus tetap terlihat dan fail closed.

## OpenClaw-only orchestration bridge - 2026-09-04

- Frontend `/agent/v1/chat` sekarang ditargetkan ke service `bridge` yang meneruskan turn
  ke endpoint private OpenClaw `/v1/responses`; alias Docker publik tetap `fraudguard-agent`.
- Service `agent` menjadi bounded tool adapter. Endpoint
  `/agent/v1/tools/{tool_name}/execute` memvalidasi input melalui registry yang sudah ada
  dan meneruskan hanya typed tool allowlist ke Core.
- CLI workspace memiliki `tool-execute`; lima skill operasional tidak lagi memakai
  subcommand `chat`, sehingga planner native tidak berada pada jalur OpenClaw.
- Core tetap satu-satunya authority untuk evidence/risk/policy/decision. Bridge tidak
  mengarang field yang tidak dikembalikan OpenClaw/Core.
- Validasi lokal mencakup compile, unit contract bridge, frontend build, dan Compose parse;
  aktivasi endpoint OpenResponses serta real Gateway call tetap harus diverifikasi di VPS.
- Hardening tambahan: skill/input routing hint di Bridge telah di-allowlist, `/tools`
  mengembalikan 503 saat Gateway gagal, dan tool payload menolak credential sensitif.
- Frontend utama sekarang memberi label OpenClaw sebagai orchestrator, menyimpan session
  OpenClaw per browser tab, dan hanya menampilkan tahap proses generik pada progress ringkas.
- Jalur browser menggunakan client function tools dari Bridge agar tidak bergantung pada
  network sandbox OpenClaw. Hanya hasil Core yang boleh mengisi risk/policy/evidence/trace;
  output model tanpa Core result dipaksa menjadi `UNKNOWN`/`PENDING` (fail closed).
- Gateway host harus bind `custom` ke private Docker host-gateway agar service Bridge bisa
  mengakses port 18789; port tersebut tidak boleh dibuka di firewall publik.
- Validasi lokal: 40 test Python, Ruff, Python compile, shell syntax, Compose parse,
  TypeScript production build, dan whitespace diff lulus melalui test image Docker.

## Core Intelligence Provider Layer - 2026-09-04

- Core sekarang memiliki adapter nyata untuk Tavily, Exa, Brave (opsional), VirusTotal,
  DNS resolver lokal, dan RDAP berbasis IANA bootstrap; adapter dipanggil hanya saat
  `deep_search=true` dan intelligence lokal belum memiliki evidence.
- Hasil eksternal divalidasi sebagai evidence `UNVERIFIED`, disimpan bersama source URL,
  provider, trace, waktu retrieval, dan extractor version; provider tidak menentukan risk/policy.
- Timeout/error provider diisolasi, dicatat ke audit, dan tidak menghasilkan evidence palsu.
- Signal provider disimpan dalam provenance dan dapat dipakai ulang pada pencarian berikutnya;
  `MULTIPLE_PUBLIC_REPORTS` hanya dibuat bila ada minimal dua source berbeda.
- Endpoint provider dan API key dikonfigurasi di Core melalui `FRAUDGUARD_INTELLIGENCE_*`.
  Belum ada vendor credential yang diaktifkan pada environment saat ini.
- Validasi: 73 test lulus, Ruff lulus; mypy masih memiliki 4 error existing di webhook delivery.

## Sinkronisasi Agent dengan Core Intelligence - 2026-09-04

- `tools.py` menerima legacy `query` maupun structured `input`.
- `reasoning.py` meneruskan `context.intelligence_input` untuk pesan dengan banyak entity.
- `runtime.py` meneruskan field pipeline Core untuk ditampilkan pada response Agent.
- Skill dan tool contract menjelaskan batas `OBSERVATION → CLAIM → DECISION`.
- API key provider tetap hanya berada di Core; Agent tidak menyimpan vendor key.
- Validasi runtime resmi Python 3.12 dan full integration deployment masih perlu dijalankan.

## Sinkronisasi Frontend - 2026-09-04

- Frontend aktif berada di root `frontend/`, sesuai build context Compose Core.
- Analyze mengirim `context.intelligence_input` ke Agent melalui same-origin `/agent/v1/chat`.
- UI menampilkan observation/evidence, claim, risk, dan policy sebagai lapisan terpisah.
- Frontend tidak menerima Core API key, Agent key, vendor key, atau akses PostgreSQL.
- Node syntax check berhasil; Docker/browser integration masih pending runtime deployment.

## Deployment Docker terpadu - 2026-09-03

- Artifact Agent aktif sekarang adalah `Docker/Dockerfile` dan `Docker/compose.yml`.
- Root `deploy.sh` menangani deploy awal, update fast-forward, restart, status, logs,
  stop, serta validasi konfigurasi.
- Agent dan Core tidak lagi bergantung pada nama/path folder saudara; komunikasi lokal
  memakai external Docker network `fraudguard-network` dengan alias
  `fraudguard-core-api` dan `fraudguard-agent`.

## Scam journey + Intelligence P0 - 2026-09-03

- Planner extracts link-click, credential, prize, authority-impersonation, payment, and
  remote-guidance candidate facts without carrying secret values.
- Routing specialization tersedia melalui `social-engineering` dan
  `intelligence-search`; source `malicious-url` lama tidak lagi dipasang secara default.
- Explicit lookup is bounded to Core `POST /api/v1/intelligence/search`; Agent still has
  no generic HTTP, SQL, filesystem, or shell tool.
- Unknown deep searches remain `PENDING_AGENT_DISCOVERY` until an allowlisted public
  provider is implemented; the agent must not invent sources or accusations.
- Every lookup propagates Core `sources`, `evidence`, and `claims`; OpenClaw must show
  source attribution and evidence metadata when present, or an explicit no-evidence state.
- Optional thumbnail URLs remain external HTTPS references; bounded archived excerpts and
  hashes provide durable fallback context without treating an unverified report as truth.
- Regression coverage includes link/form/OTP and marketplace prize/transfer narratives.

## Update skill OpenClaw - 2026-09-03

- Setelah `./deploy.sh update`, sinkronkan workspace dengan
  `./scripts/install_openclaw.sh --force`.
- Installer mem-backup versi berbeda sebelum menyalin tujuh root contract, lima skill,
  dan CLI terbaru.
- Jalankan `openclaw skills check` dan buka session baru; restart Gateway hanya bila
  watcher atau environment credential belum diperbarui.

## Perbaikan routing audit setelah intervensi - 2026-09-03

- `intervention_result` dan `intervention_status` sekarang merupakan context sekali-pakai
  agar runtime tidak mengulang submission non-idempotent pada turn berikutnya.
- Permintaan eksplisit audit/trace diprioritaskan atas context intervensi yang tersisa.
- Regression test mencakup urutan submit intervensi lalu audit dalam session yang sama.

## Deteksi permintaan credential - 2026-09-03

- Planner mengekstrak `credential_request=true` dari narasi permintaan OTP, password,
  PIN, atau CVV tanpa menerima nilai credential.
- Core menetapkan bobot `CREDENTIAL_REQUEST=70`, sehingga indikator tunggal memerlukan
  `STEP_UP_VERIFY` dan kombinasi indikator dapat menghasilkan hold.
- Skill dilarang mengganti decision/score Core atau menyatakan kepastian fraud sendiri;
  saran keamanan universal harus disajikan terpisah dari keputusan authoritative.

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
- Gunakan satu orchestrator dengan lima skill: `fraud-detection`, `safety-payment`,
  `realtime-intervention`, `intelligence-search`, dan `social-engineering`.
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
  di VPS. Agent image terbaru dan eksekusi lima skill melalui OpenClaw belum terbukti.
- Test source saat ini berisi 15 test agent dan 33 fungsi test Core. Regression agent
  terbaru lulus `15 passed in 1.57s` dan Ruff lulus untuk `src tests scripts`; regression
  Core terbaru tetap harus dijalankan dan outputnya disimpan sebelum submit.
- Blocker utama: deploy agent final, buktikan `/ready`, pasang/deteksi skill OpenClaw,
  rekam golden trace, sanitasi/backup artefak, lalu selesaikan video dan artikel.

## Installer OpenClaw dan CLI komunikasi — 2026-09-02

- `scripts/install_openclaw.sh` memasang tujuh root contract, lima skill, dan client ke
  workspace yang dibaca
  dari OpenClaw CLI atau diberikan lewat `--workspace`/`--profile`/`--dev`.
- Konflik tidak ditimpa secara default; `--force` membuat backup di workspace sebelum
  replacement. Installer tidak menulis secret dan tidak mengubah system `PATH`.
- `scripts/fraudguard_agent_cli.py` menyediakan health, ready, tools, session-create,
  dan chat. HTTP dibatasi ke loopback; remote endpoint wajib HTTPS.
- Credential dibaca dari environment atau key file luar workspace dengan permission
  `600`. Skill dilarang fallback ke `curl`, generic HTTP, atau policy lokal.
- Test integrasi mencakup authenticated structured chat, penolakan HTTP non-loopback,
  idempotent install, conflict preservation, dan recoverable force backup.
- Installer telah diverifikasi pada workspace OpenClaw lokal terisolasi: seluruh skill
  terdeteksi sebagai workspace skill, eligible, dan instalasi ulang tidak mengubah file.
  Pembuktian yang sama pada workspace OpenClaw VPS tetap pending.
- Target Docker test membawa skill source agar perilaku installer ikut diuji, sementara
  target runtime produksi tetap hanya berisi package agent.
- `skills/skill-creator/SKILL.md` menyediakan workflow pembuatan/validasi skill dengan
  bahasa sederhana. Instalasinya opt-in melalui `--with-creator`; lima skill operasional
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

- Tetap gunakan satu OpenClaw orchestrator dengan lima skill; tidak ada frontend agent kedua.
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

## Sinkronisasi struktur frontend - 2026-09-04

Frontend mengikuti struktur Next.js yang disepakati: route di `frontend/app`, komponen reusable
di `frontend/components/fraudguard`, tipe di `frontend/types`, hook di `frontend/hooks`, dan
integrasi HTTP di `frontend/lib`. Analyze sudah memakai komponen shared dan kontrak Agent/Core.
Route operasional lain tersedia sebagai entry point; endpoint listing dashboard/incidents/audit
masih perlu dihubungkan saat API operasionalnya diaktifkan.
- Memulihkan package `src/fraudguard/memory/` yang sebelumnya direferensikan runtime tetapi tidak ada: repository JSON atomic, repository SQLite WAL/transactional, retrieval masked/bounded, confidence helper, dan package export.
- Validasi Python 3.11 lulus 34/34 test dan smoke flow lulus. Verifikasi container production juga lulus readiness, API key, audit, restart/idempotency, SQLite integrity, dan backup; validasi Python 3.12 dijalankan melalui image dengan API key sintetis.
- `scripts/release.sh` sekarang memvalidasi versi Python dan menerima `PYTHON_BIN`, sehingga host dengan `python3` 3.10 tidak gagal secara ambigu.
- Tutorial uji VPS/OpenClaw ditambahkan ke `guide_user.md` dan ditautkan dari `README.md`; status remote tetap pending sampai dijalankan pada Gateway organizer.
- `scripts/deploy_vps.sh` sekarang otomatis memilih `docker compose` atau `docker-compose`, sesuai runtime Docker yang tersedia di VPS.
