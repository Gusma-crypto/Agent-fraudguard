# FraudGuard UI/UX

Demo screens: Overview, Live Investigation, Payment Intervention, Incident
Detail, Trace Timeline, and masked Fraud Intelligence.

The UI or OpenClaw conversation surface is an untrusted API caller. It may collect
synthetic input and present typed backend responses, but it cannot calculate or
edit risk, matched rule, policy decision, intervention, incident, audit, or memory
status. Display only stages and actions returned by the backend, retaining the
trace ID and sandbox wording.

Fraud Intelligence displays masked entity, status, confidence, observations,
incidents, related patterns, and review state. Never show an automatic
`fraudster` label. Never request or display PIN, password, OTP, CVV, token, API
key, stack trace, database path, or internal configuration.
