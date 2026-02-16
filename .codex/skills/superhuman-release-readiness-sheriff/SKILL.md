---
name: superhuman-release-readiness-sheriff
description: Enforce deterministic release-cycle truth by validating strict gates, timeout policy, blocker reasons, and report alignment.
---

# Superhuman Release Readiness Sheriff

Use this skill when release status, gate outcomes, and dashboard/report trust must be aligned.

## Workflow
1. Run release cycle: `python3 scripts/run_phase7_release_cycle.py`.
2. Verify contract truth: `python3 scripts/verify_benchmark_contract.py`.
3. Check timeout policy and blocker reasons in `reports/phase7_release_cycle.json`.
4. Confirm dashboard grade alignment: `python3 scripts/grade_model_dashboard.py`.
5. Produce a go/no-go summary with explicit blocking reasons and commands.

## Rules
- Treat `FAIL` in release or benchmark contract as non-promotable.
- Treat timeout-driven failures as infra defects until proven otherwise.
- Report must include the exact failing command and reason.
- Do not allow dashboard messaging to contradict release truth.
