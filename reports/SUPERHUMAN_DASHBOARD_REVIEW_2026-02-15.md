# Superhuman Dashboard Review (2026-02-15)

## Scope
This review executed the full superhuman design process for trust-critical dashboard decisions:
1. Truth audit
2. Task audit
3. Friction audit
4. Redesign plan
5. Validation protocol

## 1) Truth Audit (Source-of-Truth Mapping)

| Dashboard Surface | Truth Source | Contract Rule | Current State |
|---|---|---|---|
| Release Ready badge | `reports/phase7_release_cycle.json` (`status`) | Must not show healthy when release is `FAIL` | Correctly blocked (`FAIL`) |
| Cup Goal / Tier status | `reports/benchmark_latest.json` -> `current.vegas.cup_target` | Tiered targets (release/strong/stretch/moonshot) | `release_floor` only |
| Blocker reasons | `phase7_release_cycle.json` (`blockingReasons`) + command outputs | Must expose concrete failure reason | Present, can be more actionable |
| Dashboard grade | `reports/current_model_dashboard_grade.json` | Cap when release is not pass | Capped by `release_cycle_not_pass` |
| Freshness trust rows | data source `_metadata.fetchedAt` + dashboard meta | stale sources must be visible | Visible, currently stale warning risk |

### Truth Findings
- Main grade blocker is release status (not missing UI content).
- Tier framing is now correct; decision clarity still needs stronger actionability.
- Data freshness warnings are currently the local non-deterministic blocker for Phase 7 pass.

## 2) Task Audit (Top User Jobs)

Primary user jobs and required answer time:
- Can I release now? (<10s)
- If not, what exactly is blocking? (<20s)
- What is the next best action to unblock? (<30s)
- Are we improving model quality or only process reliability? (<30s)

### Task Findings
- "Can I release now?" is answered quickly.
- "What do I do next?" is still too implicit; blockers are listed but not yet transformed into prioritized actions.

## 3) Friction Audit

High-friction points:
- Release cycle state can remain stale if heavy gate runs are long.
- Data freshness warnings can fail strict local runs even when model and benchmark contracts pass.
- Probability-quality weakness is visible in grading, but no first-class “quality uplift lane” in the dashboard.

## 4) Redesign + Delivery Plan

### Wave A (Release Trust Determinism)
- Add explicit Phase 7 data-warning policy mode for local/offline runs with advisory visibility.
- Keep strict mode default and CI strict gates unchanged.
- Surface policy mode and advisories in release artifacts.

### Wave B (Actionability UX)
- Convert blocker output into a ranked “Immediate Actions” list in Mission Control.
- Show “next target tier gap” and “estimated unblock path” language.

### Wave C (A-grade Lock)
- Re-run Phase 7 + benchmark + grading with fresh artifacts.
- Lock dashboard truth from current reports only (no stale embedded grade snapshots).

### Wave D (Model Quality Uplift Lane)
- Run a targeted probability-quality tuning cycle with bounded candidates and non-regression constraints.
- Promote only if quality score improves while hard gates remain pass.

## 5) Validation Protocol

Required checks after each wave:
- `python3 scripts/verify_benchmark_contract.py`
- `python3 -W error::RuntimeWarning scripts/verify_model_performance.py --require-vegas-edge --require-cup-vegas-goal`
- `python3 scripts/grade_model_dashboard.py`
- `python3 -m pytest tests/test_dashboard.py tests/test_dashboard_interactions.py tests/test_dashboard_grade_contract.py -q`

Acceptance targets:
- Release cycle: `PASS`
- Dashboard grade: >= 93 (A band)
- No truth mismatch between `dashboard_data.json` and report artifacts
- No regression in benchmark hard gates

## Team Ownership

- Design Lead: truth model + hierarchy + acceptance criteria
- Product Designer: mission-control decision flow + action cards
- Data Viz Designer: uncertainty + tier runway clarity
- UX Writer: blocker/action copy
- Frontend Engineer: implementation + performance
- QA/Experiment: validation + regression + score lock

## Immediate Execution Order
1. Ship Phase 7 deterministic local policy + artifact transparency.
2. Run release cycle to pass and regenerate grade/dashboard artifacts.
3. Ship Mission Control actionability polish.
4. Execute targeted probability-quality uplift loop and report deltas.
