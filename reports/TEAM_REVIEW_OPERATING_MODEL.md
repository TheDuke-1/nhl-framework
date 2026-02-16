# Team Review Operating Model (Dual-Track Release Truth)

## Daily Review Loop (20-30 min)

1. Release Sheriff: present strict/advisory statuses and blocker aging.
2. Data Ops: report freshness SLA compliance (NHL API, NST, MoneyPuck, Odds).
3. Model Lead: report quality deltas and non-regression evidence.
4. Dashboard Lead: verify strict/advisory truth alignment in Mission Control.
5. QA: sign off on gate matrix and test outcomes.

## PR Review Checklist (Required)

1. Strict ship-gate truth cannot be masked by advisory mode.
2. Blocker reasons are concrete and actionable.
3. Dashboard consumes current report artifacts only (no stale embedded truth).
4. Tests cover contract and failure-mode changes.
5. Acceptance metrics and report timestamps are updated.

## Weekly Improvement Review

1. Track strict pass rate trend.
2. Track freshness SLA pass rate trend.
3. Track grade trend (model, dashboard, overall) vs prior baseline.
4. Convert failed experiments into new guardrails/playbooks.
5. Re-prioritize next wave by highest blocker impact.

## Acceptance Gate Matrix

1. Strict Phase 7 status: must be `PASS` to ship.
2. Advisory Phase 7 status: telemetry only; never overrides strict truth.
3. Truth sync: dashboard/meta/reports must agree on strict release status.
4. Grade policy: release-truth caps remain tied to strict mode only.
5. Promotion: Phase 15 deploys only if eligible and objectively improves target score.
