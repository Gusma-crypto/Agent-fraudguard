# PRD — FraudGuard AI

## Problem
Authentication can prove the legitimate user performed a transaction while failing to prove the user's intent was safe. Social-engineering victims can authorize payments themselves. Alert-only systems also force repeated investigation from zero.

## Solution
FraudGuard investigates suspicious activity, protects risky payment intent, performs real-time intent verification, creates incidents/audit trails, and turns verified/corroborated evidence into reusable fraud intelligence.

## P0 MVP
One FraudGuard Orchestrator with three skills:
1. `fraud-detection`
2. `safety-payment`
3. `realtime-intervention`

Core services: Event Gateway, Context Engine, Risk Engine, read-only curated Memory lookup, deterministic Policy Engine, Incident/Audit, and `UNDER_REVIEW` memory-candidate creation. P0 uses synthetic seeded `CORROBORATED` intelligence.

## Golden scenario
Seed reviewed Case #1 as `CORROBORATED` → receive fake customer-service message → extract entities/signals → memory lookup → sandbox payment to the same recipient → correlate → high risk → `TEMPORARY_HOLD` → ask whether a third party instructed transfer → `THIRD_PARTY_INSTRUCTION_CONFIRMED` → `KEEP_HOLD_AND_ESCALATE` → incident/audit → new `UNDER_REVIEW` memory candidate.

## Safety invariant
**Report ≠ Evidence ≠ Verified Fact ≠ Fraud Confirmation.**

## Non-goals
No real bank execution, external account blocking, public blacklist, autonomous criminal accusation, PIN/password/OTP/CVV collection, full multi-agent control plane, or online model fine-tuning.

## P1 after P0 is stable

Report/evidence UI, reviewer workflow, memory promotion, dispute/revocation UI, rich entity graph, notifications, and policy editor.

## Success
End-to-end demo works; high-risk actions pass policy; failures never silently ALLOW; the related case proves reuse of seeded reviewed memory; new knowledge remains `UNDER_REVIEW`; unsupported reports never become trusted memory.
