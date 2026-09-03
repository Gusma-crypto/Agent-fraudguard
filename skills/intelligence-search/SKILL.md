---
name: intelligence-search
description: Search a phone, bank account, URL/domain, email, username, brand, or message fingerprint in FraudGuard's tenant-scoped intelligence before trust or payment decisions.
metadata:
  {"openclaw":{"emoji":"🔎","requires":{"bins":["python3"]}}}
---

# Intelligence Search

Use `intelligence_lookup` for an explicit identifier lookup. Provide `intelligence_query`,
optional `entity_type`, and optional `deep_search` as non-secret context. For a message
with multiple indicators, provide `intelligence_input` containing `text` and optional
`phone`, `url`, `bank_account`, `email`, and `transaction_context`; Core routes every
extracted entity. Never request or submit an OTP, PIN, password, CVV, token, or full credential.

Treat `UNVERIFIED`, `INSUFFICIENT_INTELLIGENCE`, and `PENDING_AGENT_DISCOVERY` literally.
They are not fraud confirmation. Preserve Core risk, policy, confidence, provenance, and
trace data without inventing sources or converting a report into a verified fact.

For every result, explain the layers: `evidence` is an observation, `claims` are
structured reports derived from observations, and `risk`/`policy` are the authoritative
Core decision. State whether evidence was found. When `sources` or `evidence` is
non-empty, show each source name, HTTPS URL, access method, retrieval/observation time,
evidence summary, confidence, and verification status. Keep source attribution visible.
If Core returns `archived_excerpt`, label it as a stored snapshot and retain its
`content_hash`; it is fallback evidence when the original URL is unavailable, not proof
that an unverified claim is true. Show an HTTPS thumbnail only when Core supplies one.
When both lists are empty, explicitly say that no supporting source/evidence is currently
stored. Never cite a source that is absent from the structured Core response.

Local lookup is first. Public discovery may continue only through bounded, allowlisted
providers with provenance. If no provider is configured, explain that context-based risk
still applies and recommend verification through the brand's independently located
official channel.

Use `ingestion`, `routed_entities`, and `provider_status` to explain what Core actually
processed. Do not infer safety from an empty provider response.

## OpenClaw execution

Use `tools/fraudguard-agent chat` and pass lookup fields via `--context-json`. Never use
arbitrary HTTP, shell, SQL, leaked datasets, credential dumps, or unrestricted scraping.
