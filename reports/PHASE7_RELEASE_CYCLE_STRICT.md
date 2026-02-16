# Phase 7 Release Cycle (Strict)

Generated: `2026-02-15T23:44:08.445995+00:00`
Mode: `strict`
Truth Tier: `ship_gate`
Overall Status: `PASS`
Fail-fast triggered: `False`
Data warning policy: `STRICT`

## Refresh Automation

- Enabled: `True`
- Attempted: `True`
- Stale/Missing before: `3`
- Stale/Missing after: `3`
- Refresh command: `python3 scripts/refresh_data.py`
- Refresh status: `FAIL`

## Gate Results

| Command | Status |
|---|---|
| `phase7.refresh_health_gate` | PASS |
| `python3 scripts/validate_data.py --strict --break-aware` | PASS |
| `python3 -W error::RuntimeWarning scripts/verify_model_performance.py --require-vegas-edge --require-cup-vegas-goal` | PASS |
| `python3 scripts/verify_benchmark_contract.py` | PASS |
| `python3 scripts/grade_model_dashboard.py` | PASS |
| `python3 scripts/generate_betting_edge_report.py` | PASS |

## Current Benchmark Snapshot

- Cup Top-1: 40.0
- Cup Top-5: 60.0
- Average Winner Rank: 4.6
- Playoff F1: 0.974
