# HackFest Submission Checklist

Status terakhir: **BELUM SIAP SUBMIT** — 2 September 2026.

Gunakan `[x]` hanya setelah item dibuktikan. Implementasi lokal tidak cukup untuk
menandai deployment, video, artikel, atau submission sebagai selesai.

## Ringkasan status

- [x] FraudGuard Core terlihat berjalan sehat di organizer VPS (`api`, `worker`,
  `proxy`, dan PostgreSQL) berdasarkan terminal operator.
- [ ] Image `fraudguard-ai-agent` terbaru berjalan dan `/ready` berhasil di VPS.
- [ ] Tiga skill FraudGuard ditemukan dan dipakai oleh OpenClaw di VPS.
- [ ] Golden flow OpenClaw → Agent → Core → intervention → trace/audit direkam.
- [ ] Regression suite versi source terbaru dijalankan dan outputnya disimpan.
- [ ] Video, artikel, backup, URL publik, dan bukti submission tersedia.

## 1. Repository readiness

- [x] Agent dan Core dipisahkan: agent mengorkestrasi, Core menentukan policy dan
  menyimpan authoritative state.
- [x] Tiga kontrak skill tersedia: `fraud-detection`, `safety-payment`, dan
  `realtime-intervention`.
- [x] Guardrail credential, tenant confusion, fail-closed, trace, dan idempotency
  memiliki test source.
- [x] Skenario demo sintetis tersedia di `simulator/scenarios/`.
- [x] Dockerfile dan Compose production agent tersedia.
- [x] Jalankan 15 test agent terbaru dan catat hasilnya (`15 passed`, 2 September
  2026).
- [ ] Jalankan seluruh test Core terbaru dan simpan output terminal.
- [x] Jalankan Ruff agent untuk `src tests scripts` tanpa error.
- [ ] Jalankan Ruff Core tanpa error.
- [ ] Pastikan commit/tag submission memuat source final dan tidak masih bergantung pada
  perubahan lokal yang belum disimpan.

Perintah verifikasi:

```bash
# Agent-fraudguard
docker build --target test -f Docker/Dockerfile -t agent-fraudguard:test .
docker run --rm agent-fraudguard:test pytest -q
docker run --rm agent-fraudguard:test ruff check src tests scripts

# Fraudguard-core
docker build --target test -f Docker/Dockerfile -t fraudguard-core:test .
docker run --rm fraudguard-core:test pytest -q
docker run --rm fraudguard-core:test ruff check src tests migrations
```

## 2. VPS and OpenClaw proof

- [x] Core deployment terlihat sehat pada organizer VPS.
- [ ] Agent terbaru terlihat sehat pada `docker ps`; jangan gunakan image agent lama
  sebagai bukti versi final.
- [ ] `GET /health` agent berhasil.
- [ ] `GET /ready` agent membuktikan koneksi ke Core.
- [ ] `openclaw skills info fraud-detection` menemukan skill workspace.
- [ ] `openclaw skills info safety-payment` menemukan skill workspace.
- [ ] `openclaw skills info realtime-intervention` menemukan skill workspace.
- [ ] OpenClaw menjalankan suspected-fraud turn dengan data sintetis.
- [ ] Respons menunjukkan `selected_skill`, `tool_calls`, decision Core, `actions`, dan
  `trace_id`.
- [ ] Trace yang sama dapat dibaca dari endpoint trace/audit Core.
- [ ] Failure demo menunjukkan fail-closed dan tidak berubah menjadi `ALLOW`.
- [ ] Screenshot dashboard AI Hosting dan terminal VPS sudah diambil.

Minimum terminal proof:

```bash
docker ps
curl http://127.0.0.1:3000/health
curl http://127.0.0.1:3000/ready
openclaw skills info fraud-detection
openclaw skills check
```

Jangan tampilkan API key, `.env`, Authorization header, data pribadi, atau payment data
nyata dalam terminal recording.

## 3. Golden demo acceptance

- [ ] Pesan impersonation/urgency sintetis diterima melalui OpenClaw.
- [ ] `fraud-detection` memanggil `fraud_analyze`.
- [ ] Decision non-`ALLOW` menghasilkan satu intervensi idempotent di Core.
- [ ] Payment context sintetis menghasilkan protected payment decision.
- [ ] Respons intervensi dicatat melalui `realtime-intervention`.
- [ ] Incident dan audit trace dapat ditampilkan.
- [ ] Agent menjelaskan bahwa intervensi internal bukan pemblokiran bank atau wallet
  eksternal.
- [ ] Demo selesai tanpa prompt, log, atau UI yang memperlihatkan secret.

## 4. Backup and artifact safety

- [ ] Source final agent dan Core dibackup di Git remote yang dapat diakses tim.
- [ ] Commit hash/tag final dicatat: `________________`.
- [ ] Seed/skenario sintetis, non-secret configuration, logs yang sudah disanitasi,
  screenshot, artikel, dan video dibackup di luar VPS.
- [ ] Restore/download backup diuji sebelum Batch 1 VM dimatikan.
- [ ] `.env`, private key, API key, database dump mentah, dan log sensitif tidak masuk
  Git atau artefak publik.
- [ ] Semua identifier manusia, rekening, telepon, URL, dan transaksi pada demo bersifat
  sintetis atau dimasking.

## 5. Video

- [ ] Durasi 5–10 menit.
- [ ] Landscape 16:9, minimal 1080p.
- [ ] Masalah, arsitektur dua-service, tiga skill, dan safety boundary dijelaskan.
- [ ] Golden workflow ditampilkan end-to-end.
- [ ] Dashboard AI Hosting dan terminal organizer VPS ditampilkan.
- [ ] “AI Hosting” dan “IDwebhost” disebutkan atau ditampilkan.
- [ ] Watermark IDwebhost tetap terlihat di salah satu sudut.
- [ ] Audio, musik, gambar, dan footage dimiliki atau memiliki lisensi yang sesuai.
- [ ] Tidak ada secret atau data nyata pada frame, subtitle, description, atau thumbnail.
- [ ] Upload public atau unlisted, bukan private.
- [ ] URL video: `________________`.

## 6. Article

- [ ] Minimal 800 kata original dan belum pernah dipublikasikan.
- [ ] Menjelaskan problem, solusi, arsitektur, OpenClaw skills, Core policy, demo,
  keamanan, dan hasil.
- [ ] Dapat dibuka publik tanpa login/paywall dan dapat diindeks.
- [ ] Memuat [AI Hosting](https://idwebhost.com/ai-hosting) dengan anchor persis
  `AI Hosting`.
- [ ] Memuat [Cloud VPS](https://cloudbaik.com) dengan anchor persis `Cloud VPS`.
- [ ] Tidak memuat API key, data nyata, klaim pemblokiran eksternal, atau klaim fraud
  tanpa bukti.
- [ ] URL artikel: `________________`.

## 7. Final submission

- [ ] Nama event/batch, kategori, field submission, format URL, dan deadline diverifikasi
  ulang dari kanal resmi organizer.
- [ ] Nama project konsisten: `FraudGuard AI`.
- [ ] Repository URL final: `________________`.
- [ ] Demo/application URL final: `________________`.
- [ ] Video URL final sudah diuji dari private browser.
- [ ] Article URL final sudah diuji dari private browser.
- [ ] Repository/demo URL sudah diuji tanpa session admin developer.
- [ ] Form diperiksa ulang oleh minimal satu anggota tim.
- [ ] Submission dikirim sebelum deadline.
- [ ] Screenshot, timestamp, email, atau receipt bukti submission disimpan di luar VPS.

## Blocker prioritas

1. Deploy image agent terbaru dan buktikan `/ready` ke Core.
2. Instal/deteksi tiga skill di workspace OpenClaw VPS.
3. Rekam satu golden flow dengan trace/audit yang sama.
4. Jalankan regression suite final dan sanitasi seluruh artefak.
5. Selesaikan video, artikel, URL publik, backup, lalu submit.
