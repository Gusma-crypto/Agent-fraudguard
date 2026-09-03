# Changelog

All notable workspace, product, configuration, and documentation changes are recorded here. This project follows a simple Keep a Changelog style; versions will be assigned when an implementation milestone is released.

## Unreleased

### Credential-request detection and authority wording - 2026-09-03

- Added deterministic detection for narratives requesting OTP, password, PIN, or CVV without collecting credential values.
- Hardened `fraud-detection` instructions so OpenClaw preserves Core decisions and never replaces `ALLOW` with an unsupported fraud verdict.
- Added regression coverage for Indonesian and English credential-request narratives.

### One-shot intervention context and audit routing - 2026-09-03

- Prioritized explicit trace/audit requests over stale intervention context.
- Made intervention result/status fields one-shot so later turns cannot replay a non-idempotent response implicitly.
- Added planner and runtime regressions for intervention completion followed by audit lookup in one session.

### Unified root Docker operations - 2026-09-03

- Consolidated Agent Docker deployment into `Docker/compose.yml` and removed duplicate local/production Compose files.
- Added root `deploy.sh` actions for deploy, fast-forward update, restart, status, logs, safe stop, and validation.
- Replaced fixed sibling-directory coupling with the shared external `fraudguard-network` contract used by FraudGuard Core.

### Security and deployment hardening - 2026-09-02

- Hardened Agent Core-response parsing so malformed error envelopes and non-object data
  fail closed as `CoreError` instead of causing an internal exception.
- Documented the single-replica in-memory session policy and the Redis/TTL/locking plan
  required before horizontal scaling.
- Added a fail-fast replica guard and bounded multilingual routing indicators for Spanish,
  French, and German; unsupported response languages still use the English fallback.

### OpenClaw quick install and communication CLI - 2026-09-02

- Menambahkan installer idempotent untuk tiga workspace skill dan CLI komunikasi.
- Menambahkan client Python stdlib dengan endpoint allowlist, loopback/HTTPS guard,
  key file mode check, bounded response, session, chat, health, ready, dan tool listing.
- Memperbarui tiga skill dengan jalur eksekusi CLI serta panduan instalasi OpenClaw.
- Menambahkan regression installer/CLI ke target Docker test; 15 test dan Ruff untuk
  `src tests scripts` lulus.
- Menambahkan `skill-creator` ramah pengguna awam sebagai helper development opsional
  melalui installer `--with-creator`, tanpa mengubah tiga skill runtime produksi.
- Menambahkan runtime localization untuk English, Indonesian, dan Malay dengan language
  hint, auto-detection, English fallback, dan preservasi field authoritative Core.

### Evidence-based submission checklist - 2026-09-02

- Mengubah checklist HackFest menjadi readiness gate berbasis bukti untuk repository,
  VPS/OpenClaw, golden demo, backup, video, artikel, dan final submission.
- Menandai Core VPS sebagai terverifikasi dan mempertahankan agent/OpenClaw serta
  artefak publik sebagai pending sampai ada bukti aktual.

### Active fraud response - 2026-09-02

- Fraud detection kini mengorkestrasi intervensi protektif dari decision Core.
- Menambahkan action outcome pada respons chat dan idempotency untuk create intervention.
- Memperjelas bahwa agent tidak melakukan external enforcement.

### Core/agent consolidation - 2026-09-02

- Made `logic-backend-server` the only risk, policy, persistence, incident, learning, and audit authority.
- Replaced the duplicate SQLite/Core runtime with `fraudguard_agent`, a FastAPI conversation, reasoning, session-context, guardrail, and typed-tool service.
- Added fail-closed Core REST integration, trace propagation, payment/event idempotency, agent authentication, turn budgets, and prompt-injection/secret guards.
- Replaced the legacy backend Docker deployment with a stateless agent container and updated OpenClaw skills/contracts.
- Added runtime, integration, and security tests for tool selection, clarification, Core contracts, prompt injection, tenant confusion, and Core outage behavior.

### Production secret, recovery, and deployment reliability - 2026-09-01

- Added a root-only container entrypoint that reads a mode-`600` production secret, then permanently drops to the `fraudguard` UID/GID before executing the API.
- Added an opt-in real production Compose integration test covering secret mount, `/ready`, API-key rejection/acceptance, non-root PID 1, and in-container smoke.
- Fixed JSON repository rollback so failed mutators cannot leak partial in-memory state.
- Added bounded readiness requests and immediate container exit/restart detection to the VPS deploy script, with Compose v1/v2 support.
- Added integrity-checked SQLite online backup and confirmed atomic restore scripts with mandatory pre-restore backup.
- Updated deployment, database, developer, and user documentation for the production workflow.

### Local OpenClaw adapter - 2026-09-01

- Added `fraudguard-adapter`, a loopback-only Python CLI exposing exactly seven fixed backend operations through JSON stdin/stdout.
- Added bounded timeout/response size, protected API-key loading, typed safe errors, path validation, and adapter regression tests.

### Repository responsibility split - 2026-09-01

- Restricted `src/` to the `fraudguard` Python package and added explicit `core/`, `prompts/`, and `providers/` boundaries without creating a second orchestrator.
- Moved Dockerfile, local/production Compose, environment example, and deployment map into `Docker/`; moved the Gateway config example beside `openclaw-plugin/`.
- Moved database assets, tests, inactive references, project metadata, user context, and preserved runtime data from legacy nested paths to their root directories.
- Added bounded agent command templates under `commands/` and included them in the allowlisted OpenClaw bundle.
- Added `setup.js`, `doctor.js`, `install.js`, `repair.js`, and `release.sh`; mutating install/repair actions require explicit `--apply`.
- Added a repository-layout regression test, bringing the Python suite to 34 tests.

### P0 OpenClaw and production hardening - 2026-09-01

- Added a built and OpenClaw-validated TypeScript plugin that registers exactly seven bounded FraudGuard tools and permits only loopback backend transport.
- Added a strict OpenClaw model-analysis overlay; the backend retains indicator extraction/masking, memory retrieval, risk calculation, final policy, incident, and audit authority.
- Made YAML rules and fallback decisions executable instead of duplicating `FG-001`–`FG-003` in Python; invalid model output retries once and then creates an audited deterministic fallback.
- Enforced a minimum 24-character API key for every non-loopback bind and added Docker secret-file loading.
- Added nested bounded schemas, removed normalized identifiers from analysis responses, and incremented state version only on real mutations.
- Added automated E3, E7, and E8 package evals, production Compose/deploy artifacts, and retry-based Windows SQLite temporary cleanup.
- Expanded the suite to 33 tests; actual Docker/OpenClaw runtime installation on the organizer VPS remains pending external execution.

### Source-directory consolidation - 2026-09-01

- Consolidated backend support artifacts under `src/`: database migrations and seeds, runtime data, tests, deployment files, inactive references, Docker/Compose definitions, Python project metadata, and `USER.md`.
- Updated Python defaults, database initialization, test discovery, Docker build context, Compose commands, manifest entries, ignore rules, and active documentation for the new paths.
- Kept `MEMORY.md` absent because no long-term memory file existed; it will be created only when meaningful content needs to be recorded.
- Removed the temporary `rsc/` target so there is only one final location and no overlapping runtime path.

### OpenClaw bundle and Docker backend separation - 2026-09-01

- Added an allowlist-based exporter that produces `dist/fraudguard-openclaw-agent.zip` with the authoritative MASTER but without backend source, database, runtime state, personal memory, secrets, tests, Docker files, PDFs, or inactive references.
- Added a non-root, health-checked Python backend Docker/Dockerfile and hardened Compose service with loopback-only publishing, persistent SQLite volume, read-only root filesystem, dropped capabilities, and resource limits.
- Added a Docker build-context denylist that excludes OpenClaw workspace files while preserving executable Python handlers under `src/fraudguard/skills/`.
- Added a deployment artifact map, non-secret environment example, and three automated separation tests; the full suite now contains 23 passing tests.
- Removed the mistaken two-agent split: FraudGuard continues to use one OpenClaw orchestrator with three skills, connected through named adapter operations to the Docker backend.

### OpenClaw orchestrator and skill boundaries - 2026-09-01

- Replaced the provisional orchestrator contract with an explicit seven-operation adapter allowlist, routing/state gates, data boundary, forbidden capabilities, failure behavior, and registration acceptance criteria.
- Aligned all three skill invocation, output, side-effect, and failure boundaries with the executable Python handlers, request validation, schemas, repository ownership, and Policy Engine.
- Prevented skills from accepting model/caller-owned risk scores, thresholds, policy overrides, repository state, database handles, or state-changing authority.
- Expanded the tool contract to distinguish bounded internal functions from OpenClaw-registered tools and to prohibit raw SQL, shell, generic network, payment, messaging, memory promotion, and external enforcement.
- Added an adapter access-control eval plan; all three skill structures pass the official quick validator.

### Local relational database - 2026-09-01

- Added an automatically migrated and seeded SQLite P0 database with separate memory, candidate, intervention, incident, audit, and idempotency tables.
- Added WAL mode, full synchronous commits, foreign-key checks, bounded busy timeout, indexed trace/memory lookup, and transaction-serialized updates.
- Enforced append-only audit rows in both repository logic and database triggers.
- Made SQLite the default runtime storage while retaining atomic JSON through `FRAUDGUARD_STORAGE=json`.
- Added a database initialization/integrity command and exposed the active storage backend through health/readiness responses.
- Added four database tests for schema/seed initialization, restart persistence/idempotency, multi-runtime updates, and audit immutability; the full suite now contains 20 passing tests.

### Backend hardening - 2026-09-01

- Bound every idempotency key to a canonical SHA-256 request fingerprint and added `409 IDEMPOTENCY_KEY_REUSED` conflicts.
- Restricted intervention creation to a policy-authorized payment trace; client risk scores, policy state, payment summaries, and secret fields are rejected.
- Made incident and memory-candidate creation depend on the final `KEEP_HOLD_AND_ESCALATE` policy decision.
- Rejected non-finite or boolean payment amounts and non-boolean context flags.
- Replaced shallow output checks with recursive schema validation.
- Added `/ready`, optional constant-time `X-API-Key` enforcement, strict content length handling, and safe exception logging.
- Expanded the regression suite from 10 to 16 passing tests.

### Core Python P0+�u���T 2026-09-01

- Built a dependency-free Python 3.11+ core under `src/fraudguard/` using the requested agent, skills, risk, memory, policy, incidents, audit, and tools boundaries.
- Added executable HTTP endpoints, bounded stdin CLI, atomic local state, idempotency, typed errors, request-size limits, secret-field rejection, and masked memory lookup.
- Converted `policy/policy.yaml` to JSON-compatible YAML so Python reads the single authoritative policy without a YAML dependency.
- Added three machine-readable output schemas and enforced them at runtime.
- Added a synthetic `CORROBORATED` Fraud Memory seed and executable Case 1/Case 2 request fixtures.
- Added ten Python unit/integration tests, an isolated golden-flow smoke command, and a dependency-free project validator.
- Replaced the provisional Node core with one Python runtime to prevent overlapping implementations.
- Aligned all three OpenClaw skill contracts with their Python handlers and documented that organizer runtime tool registration remains pending.
- Recorded the verified VPS RAM, disk, Node, and OpenClaw baseline; Python version, model, ports, domain, service manager, and backup remain pending.

### Consolidated — 2026-09-01

- Established an explicit instruction hierarchy so workspace policy, product scope, deterministic policy, skills, and implementation contracts have one authority each.
- Merged unique idempotency and test/eval requirements from the duplicate project-rules document into active `AGENTS.md`.
- Reworked the orchestrator file as a single contract that inherits active authority instead of duplicating thresholds or workspace rules.
- Marked hook files as inactive contracts until they are registered in the organizer's OpenClaw runtime.
- Moved already-applied OpenClaw merge snippets to `reference/archive/openclaw-additions/`.
- Moved superseded `PROJECT-RULES.md`, `IMPLEMENTATION-PLAN.md`, and `FILE-MAP.md` to `reference/archive/superseded-docs/` rather than deleting them.
- Added `docs/INSTRUCTION-HIERARCHY.md` and `reference/README.md`.
- Split `MANIFEST.md` into active sources and inactive reference archive.
- Corrected the stale pre-move contract path in the MASTER document.

### Added — 2026-09-01

- Added the authoritative FraudGuard AI HackFest master specification.
- Added OpenClaw orchestrator, three skill contracts, tool/policy contracts, simulator scenarios, evaluation/test plans, and evidence-backed Fraud Memory documentation.
- Added a reviewed synthetic Case #1 seed to make Case #2 memory reuse logically valid.
- Added an explicit HackFest video, article, VPS, backup, and submission checklist.
- Added `USER.md` with project-owner context and working preferences.
- Added `guide_user.md`, `catatan_project.md`, and developer guidance in `README.md`.
- Added permanent documentation-synchronization rules to `AGENTS.md`.

### Changed — 2026-09-01

- Configured the active OpenClaw workspace identity as FraudGuard AI.
- Merged FraudGuard product, policy, evidence, memory, security, and delivery rules into the active workspace files.
- Unified risk bands to `ALLOW` 0–29, `REVIEW` 30–59, `STEP_UP_VERIFY` 60–79, and `TEMPORARY_HOLD` 80–100.
- Replaced ambiguous intervention outcomes with explicit safe-intent, third-party-instruction, unrecognized-transaction, no-third-party-instruction, and uncertain states.
- Limited P0 to a reliable end-to-end demo using read-only seeded `CORROBORATED` memory; full reporting, review, and promotion UI remains P1.
- Moved the additive pack contents to the repository root and corrected internal references and manifest entries.
- Kept heartbeat disabled for the HackFest MVP to avoid background side effects and unnecessary token usage.

### Removed — 2026-09-01

- Removed the active `BOOTSTRAP.md` after OpenClaw workspace onboarding completed. It remains recoverable from Git and `reference/openclaw-current/BOOTSTRAP.md`.

### Validated — 2026-09-01

- Validated all three skill structures.
- Validated policy YAML and simulator JSON files.
- Verified every manifest path exists.
- Verified the active bootstrap is removed and its reference copy remains available.
- Restored the missing `fraudguard.memory` persistence and bounded retrieval modules, including transactional SQLite state, atomic JSON fallback, masked lookup, and audit immutability checks.
- Removed the stale `USER.md` entry from `MANIFEST.md` so project validation matches the intentionally excluded personal runtime file.
- Hardened `scripts/release.sh` to require Python 3.11+ and support an explicit `PYTHON_BIN` interpreter.
- Added a user-facing VPS/OpenClaw communication test tutorial covering safe fast-forward pull, backend deployment, plugin installation, and trace/audit verification.
- Made `scripts/deploy_vps.sh` compatible with both Docker Compose v2 (`docker compose`) and legacy Compose v1 (`docker-compose`).
