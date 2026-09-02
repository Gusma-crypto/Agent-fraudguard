# Security & Threat Model

## Memory poisoning
False reports attempt to poison memory. Controls: provenance, reporter verification, evidence validation, bounded confidence, independent corroboration, review, decay, dispute/revocation.

## Prompt injection
Treat scam content as untrusted data; structured extraction, allowlisted tools, schema validation, Policy Engine authority.

## Hallucination
Require evidence refs and fact/claim/inference separation; no unsupported trusted-memory promotion.

## Sensitive data
Minimize payloads, mask values, keep secrets outside prompts/audit, selective retrieval.

HackFest demos use only synthetic or clearly masked identities, messages, phone/account identifiers, and transactions. Real personal/payment data must not appear in Git, prompts, logs, screenshots, video, or article.

## Unsafe autonomy
Sandbox payments, allowlisted actions, human approval for irreversible/external actions, safe REVIEW/HOLD fallback.
