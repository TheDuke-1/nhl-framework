# Phase 5 Rebuild + Calibration

Generated: `2026-02-08T18:59:21.729567+00:00`

## Active Profile

- Profile Version: `phase3-optimized-2026-02-08`
- Recency Decay: `0.1`
- Cup Winner Boost: `2.0`

## Calibration Diagnostics (Cross-Validation)

- Brier Playoff: 0.0725
- Brier Cup: 0.0308
- Log Loss Playoff: 0.2326
- Calibration Error (playoff): 0.0209
- Cup Picks Correct: 2/13

## Verification Gates

| Command | Status |
|---|---|
| `python3 scripts/verify_model_performance.py` | FAIL |
| `python3 scripts/update_benchmark_metrics.py` | PASS |
| `python3 scripts/verify_benchmark_contract.py` | FAIL |
