# Before Sensitive Action

> **Enforcement status:** active through typed agent tools and Core policy. Native hook
> registration remains a deployment verification step, not the sole guard.

Before execution, allow only the inventory in `src/fraudguard_agent/tools.py`. Validate
input, budget, credential fields, side effects, and idempotency. Core independently
authenticates, scopes tenant data, validates payloads, and applies Policy Engine.

No caller/model risk score, threshold, policy decision, payment action,
repository handle, generic URL, shell command, or database query is accepted.
If planning or Core validation fails, protected workflows fail closed. Agent inference
never becomes an `ALLOW` decision.
