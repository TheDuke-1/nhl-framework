---
name: superhuman-edge-goal-loop
description: Run targeted Cup-vs-Vegas objective loops with bounded hypotheses, strict non-regression, and promotion safety.
---

# Superhuman Edge Goal Loop

Use this skill when the objective is to close the Cup-vs-Vegas goal gap quickly and safely.

## Workflow
1. Run targeted candidate lanes (Phase 9/12/13 scripts) with bounded budgets.
2. Keep hypotheses focused on edge lift, not broad parameter churn.
3. Enforce hard gates + non-regression + positive-season floor.
4. Promote only when strict contract is met in the same run context.
5. Record champion/challenger deltas in reports.

## Rules
- No promotion on edge lift alone; all strict gates must pass.
- Abort tracks that fail to improve edge after fixed budget.
- Preserve reproducibility: keep profile and command history explicit.
- Log why each candidate was rejected (gate, ratio, CI, or regression).
