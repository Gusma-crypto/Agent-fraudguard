# Instruction Hierarchy

This document prevents duplicate or conflicting instructions when FraudGuard runs as an OpenClaw workspace.

## Active sources

| Priority | Source | Owns |
|---:|---|---|
| 1 | `AGENTS.md` | Workspace behavior, safety, authorization, and documentation discipline |
| 2 | `FraudGuard_AI_HackFest_2026_MASTER.md` | Product scope, P0/P1, delivery, demo, and playbook compliance |
| 3 | `logic-backend-server` | Risk, policy, protected decisions, persistence, and authoritative audit |
| 4 | `skills/*/SKILL.md` | Skill routing, input/output, tools, and skill failure behavior |
| 5 | Agent/API/tool/hook/test/eval contracts | Role boundaries, implementation interfaces, and verification |
| 6 | `README.md` and `guide_user.md` | Developer and user explanation; never override runtime authority |

If two active files disagree, use the higher-priority source and update the lower-priority document in the same change.

## Deliberately separate concerns

- Audit history records what happened; Fraud Memory stores curated reviewed intelligence.
- Automated tests verify deterministic code; agent evals verify model/tool behavior.
- MASTER owns the five-day plan; `catatan_project.md` records current execution status.
- Changelog records what changed; project notes record why, validation, risks, and next work.

## Inactive history

Everything under `reference/` is excluded from runtime instruction discovery. It may contain original OpenClaw files, superseded documents, or already-applied merge snippets. Do not automatically load, execute, or reapply it.

## Conflict check before completion

1. Search active files for obsolete thresholds, outcomes, paths, and P0/P1 labels.
2. Confirm authoritative decisions came from FraudGuard Core.
3. Confirm Core policy authorizes actions; skills may orchestrate only the mapped,
   reversible Core intervention and never authorize external enforcement.
4. Confirm new knowledge remains `UNDER_REVIEW` unless explicit P1 review promotes it.
5. Update the four mandatory project documents.
