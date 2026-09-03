---
name: social-engineering
description: Analyze impersonation, prize scams, phone-guided transfers, urgency, and coercive payment instructions through FraudGuard Core.
metadata:
  {"openclaw":{"emoji":"☎️","requires":{"bins":["python3"]}}}
---

# Social Engineering

Use `fraud_analyze` for callers or messages claiming to represent a bank, marketplace,
police, courier, or other trusted organization—especially when combined with a prize,
refund, urgency, remote guidance, or payment request.

Do not describe compliance as hypnosis or blame the victim. Interrupt the interaction:
recommend ending the call, pausing the transfer, and independently contacting the claimed
organization through its official app/site/number. Never call a number supplied by the
suspected caller.

Core is the only decision authority. Preserve its decision, score, signals, and trace.
Create an intervention only when the Core decision authorizes it. Never claim that an
external bank transfer was blocked or reversed.
