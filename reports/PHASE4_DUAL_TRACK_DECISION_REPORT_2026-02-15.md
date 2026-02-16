# Phase 4 Dual-Track Decision Report (2026-02-15)

## Inputs

- Strict release artifact: `reports/phase7_release_cycle_strict.json`
- Advisory release artifact: `reports/phase7_release_cycle_advisory.json`
- Latest index: `reports/phase7_release_cycle_latest.json`
- Grade artifact: `reports/current_model_dashboard_grade.json`
- Dashboard payload: `dashboard_data.json`
- Previous baseline reference: `reports/SUPERHUMAN_DASHBOARD_REVIEW_EXECUTION_2026-02-15.md`

## Release Truth Outcome

- Ship gate (strict): `FAIL`
- Local advisory: `PASS`
- Strict fail-fast: `true`
- Strict blocker: `NST: Data is 10 days old (fetched: 2026-02-05)`
- Advisory blockers: none

Interpretation:
- Dual-track policy is working as intended.
- Strict truth remains authoritative for release.
- Advisory pass is available for local iterative work but does not override ship gate.

## Dashboard Truth Sync

`dashboard_data.json` meta currently reports:
- `releaseStatus`: `FAIL`
- `releaseStatusStrict`: `FAIL`
- `releaseStatusAdvisory`: `PASS`
- `releaseTruthPolicy`: `dual-track`

This confirms strict/advisory truth is now propagated into dashboard output.

## Grade Snapshot and Delta vs Previous Baseline

Current (generated `2026-02-15T17:45:17.647519+00:00`):
- Model: `75.7 (C)`
- Dashboard: `68.7 (D+)`
- Overall: `73.6 (C)`

Previous baseline (from execution report):
- Model: `86.6 (B)`
- Dashboard: `96.5 (A)`
- Overall: `89.6 (B+)`

Delta:
- Model: `-10.9`
- Dashboard: `-27.8`
- Overall: `-16.0`

Primary cause:
- Strict release fail triggers dashboard grade cap (`release_cycle_not_pass`).

## Phase 15 Promotion Decision

- Latest completed artifact: `reports/phase15_probability_quality_uplift.json` (`2026-02-15T16:43:08.919094+00:00`)
- Decision: `deployed=false`
- Selected: `baseline`
- Reason: `no safe probability-quality improvement candidate found`

## Final Decision

- Release decision: **DO NOT SHIP** (strict gate fail).
- Next highest-leverage fix: resolve stale strict freshness blockers (NST/NHL API path) and rerun strict Phase 7.
