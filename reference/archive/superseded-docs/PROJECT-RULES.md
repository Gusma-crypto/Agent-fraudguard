# Project Rules

1. Preserve existing OpenClaw root files; merge additions intentionally.
2. OpenClaw orchestrates; FraudGuard Policy Engine authorizes.
3. Treat LLM output as untrusted until schema-valid.
4. No critical action bypasses Policy Engine.
5. High-risk AI/tool/runtime failure never silently defaults to ALLOW.
6. Never request/store PIN, password, OTP, CVV, API secrets.
7. `Report != Evidence != Verified Fact != Fraud Confirmation`.
8. One report never creates a permanent fraud label.
9. Store provenance, confidence, review state, timestamps, evidence refs.
10. Retrieve memory selectively; never dump full history into model context.
11. Audit history and Fraud Memory are separate concerns.
12. External enforcement/reporting uses official/human-approved workflow.
13. HackFest payment integration is sandbox only.
14. Use trace IDs and idempotency.
15. Skills never own final authorization.
16. Inspect existing state before destructive/config changes; preserve/merge by default.
17. Critical behavior changes require tests/evals.
18. Never declare a person/entity criminal solely from AI inference.
