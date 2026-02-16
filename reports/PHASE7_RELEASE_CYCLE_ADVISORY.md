# Phase 7 Release Cycle (Advisory)

Generated: `2026-02-16T04:33:27.594884+00:00`
Mode: `advisory`
Truth Tier: `local_advisory`
Overall Status: `PASS`
Fail-fast triggered: `False`
Data warning policy: `ALLOW_WARNINGS`

## Refresh Automation

- Enabled: `False`
- Attempted: `False`
- Stale/Missing before: `0`
- Stale/Missing after: `0`

## Gate Results

| Command | Status |
|---|---|
| `phase7.refresh_health_gate` | PASS |
| `python3 scripts/validate_data.py --allow-warnings --break-aware` | PASS |
| `python3 -W error::RuntimeWarning scripts/verify_model_performance.py --require-vegas-edge --require-cup-vegas-goal` | PASS |
| `python3 scripts/verify_benchmark_contract.py` | PASS |
| `python3 scripts/grade_model_dashboard.py` | PASS |
| `python3 scripts/generate_betting_edge_report.py` | PASS |

## Current Benchmark Snapshot

- Cup Top-1: 40.0
- Cup Top-5: 60.0
- Average Winner Rank: 4.6
- Playoff F1: 0.974
