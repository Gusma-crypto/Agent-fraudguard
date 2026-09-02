# Typed Tool Allowlist

Runtime inventory berasal dari `src/fraudguard_agent/tools.py`. Setiap tool menetapkan
input model, scope Core, side effect, protected action, dan idempotency requirement.

Agent tidak memiliki generic HTTP, shell, filesystem mutation, SQL/database, payment,
messaging, public-reporting, policy-editing, atau external-enforcement tool.

`create_intervention` adalah side effect protektif dan idempotent. Tool ini hanya boleh
dipanggil setelah decision Core `REVIEW`, `STEP_UP_VERIFY`, atau `TEMPORARY_HOLD`, dengan
tipe tindakan yang dipetakan secara deterministik oleh runtime. `ALLOW` tidak membuat
intervensi.

OpenClaw harus memanggil endpoint agent atau adapter yang memetakan tepat ke inventory
ini. URL arbitrary dan caller-supplied tenant authority dilarang.
