---
name: malicious-url
description: Analyze link-click, form-entry, phishing, and OTP or credential-harvesting journeys through FraudGuard Core before the user continues.
metadata:
  {"openclaw":{"emoji":"🔗","requires":{"bins":["python3"]}}}
---

# Malicious URL

Use `fraud_analyze` when a link is paired with instructions to click, fill a form, log in,
or disclose/use an OTP, PIN, password, or CVV. Send only typed boolean indicators; never
send or store the credential value.

Recommend closing the page, not clicking again, not approving prompts, and contacting the
real provider through an independently located official channel. If a credential was
already entered, recommend immediate account-security and provider escalation steps, but
do not claim FraudGuard reversed an external transaction.

Core remains authoritative. Preserve its decision, score, signals, and trace; do not turn
an `ALLOW` result into an independent fraud verdict or invent URL reputation evidence.
