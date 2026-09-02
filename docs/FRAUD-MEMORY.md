# Fraud Memory — Evidence-Backed Fraud Intelligence

## Layers
1. Audit Memory: what FraudGuard did.
2. Observation Memory: what was reported/observed; not verified truth.
3. Trusted Fraud Intelligence: knowledge promoted after verification/corroboration/review.

## Status lifecycle
`UNVERIFIED_REPORT → UNDER_REVIEW → SUSPICIOUS → CORROBORATED → CONFIRMED`

Also support `DISPUTED`, `STALE`, `REVOKED`. Avoid `FRAUDSTER` as an automatic entity status.

## Confidence
Use provenance, reporter verification, evidence validity, independent corroboration, prior incidents, relationships, recency, contradiction, and decay. Memory contribution is bounded and cannot be the sole reason for irreversible action.

## Write lifecycle
`Report/Incident → Observation → Memory Candidate → Evidence + Correlation → Review/Policy → Trusted Knowledge`

## Retrieval
`search_fraud_memory(type, normalized_value)` returns masked entity, status, confidence, observation/incident counts, related patterns, evidence refs, last_seen, review status.

Never dump the full fraud history into the LLM context.
