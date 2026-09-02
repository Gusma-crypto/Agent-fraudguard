# Agent Evaluation Plan

Required suites:

- tool selection and no-tool education;
- clarification for incomplete payment context;
- prompt injection and secret-value rejection;
- tenant/application confusion rejection;
- Core timeout/malformed response fail-closed behavior;
- trace and idempotency propagation;
- Core decisions never overridden;
- `ALLOW` produces no action; every non-`ALLOW` fraud decision maps to one idempotent
  Core intervention;
- intervention failure preserves the Core decision, fails closed, and reports `FAILED`;
- repeated result and turn/tool budget stop conditions;
- authenticated CLI chat and structured JSON response handling;
- rejection of plain HTTP for non-loopback Agent endpoints;
- idempotent OpenClaw installation, conflict preservation, and recoverable `--force`
  backup.

Executable coverage lives in `tests/`. Staging evaluation must use synthetic data and a
scoped Core key.
