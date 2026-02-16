# Phase 7 Release Cycle (Advisory)

Generated: `2026-02-15T17:45:03.696392+00:00`
Mode: `advisory`
Truth Tier: `local_advisory`
Overall Status: `PASS`
Fail-fast triggered: `False`
Data warning policy: `ALLOW_WARNINGS`

## Refresh Automation

- Enabled: `False`
- Attempted: `False`
- Stale/Missing before: `4`
- Stale/Missing after: `4`

## Gate Results

| Command | Status |
|---|---|
| `python3 scripts/validate_data.py --allow-warnings` | PASS |
| `python3 -W error::RuntimeWarning scripts/verify_model_performance.py --require-vegas-edge --require-cup-vegas-goal` | PASS |
| `python3 scripts/verify_benchmark_contract.py` | PASS |
| `python3 scripts/grade_model_dashboard.py` | PASS |
| `python3 scripts/generate_betting_edge_report.py` | PASS |

## Data Freshness Advisories

- ⚠️  VALIDATION PASSED WITH WARNINGS - 2 warning(s):
- ⚠️  NST: Data is 10 days old (fetched: 2026-02-05)
- ⚠️  NHL API: Data is 10 days old (fetched: 2026-02-05)

## Current Benchmark Snapshot

- Cup Top-1: 40.0
- Cup Top-5: 60.0
- Average Winner Rank: 4.6
- Playoff F1: 0.974
