# Benchmark Improvement Playbook (Toward A+)

Generated: `2026-02-07`

## Why Benchmarks Were Flat

1. Several recent phase changes were infrastructure/process improvements, not new high-signal model inputs.
2. Backlog datapoints were initially proxy-only and not true historical source features.
3. Critical issue fixed today: benchmark scripts were evaluating with hardcoded model settings rather than the active tuned profile.

## A+ Target Definition

Target scorecard for "A+" trajectory:

- Cup Top-1: `>= 40%`
- Cup Top-5: `>= 65%`
- Average Winner Rank: `<= 4.5`
- Playoff F1: `>= 0.93`
- Brier Playoff: `<= 0.065`
- Brier Cup: `<= 0.028`
- Calibration Error: `<= 0.012`
- Model minus Vegas Brier: strictly negative by meaningful margin once historical Vegas data is integrated.

## Execution Plan (How We Improve Benchmarks)

### Phase A: Measurement Integrity (Immediate)

- Keep strict walk-forward and leakage audit mandatory.
- Use profile-aware benchmarking for every update.
- Require delta table after every experiment.

### Phase B: High-Value True-Source Data (Next)

- Replace proxy backlog fields with true historical inputs prioritized by expected lift:
- 1) injury-adjusted strength (historical injuries)
- 2) schedule/travel/rest
- 3) discipline taken/drawn
- 4) trade-deadline roster delta
- 5) coach/system continuity in historical windows

### Phase C: Objective-Driven Tuning

- Optimize for three objectives separately:
- Cup Top-1 objective
- Cup Top-5 objective
- Playoff-field objective
- Deploy only blended candidates that pass hard gates and non-regression checks.

### Phase D: Vegas Outperformance Track

- Integrate true historical sportsbook Vegas odds by season.
- Add fixed "model minus Vegas" objective into release gate.
- Only promote candidates that improve model-vs-Vegas deltas without collapsing Cup metrics.

## Iteration Loop (Every Cycle)

1. Implement one material signal or one objective-weight change.
2. Run:
- `python3 scripts/verify_model_performance.py`
- `python3 scripts/update_benchmark_metrics.py`
- `python3 scripts/verify_benchmark_contract.py`
- `python3 scripts/run_phase7_release_cycle.py`
3. Review deltas:
- If improved and gates pass: keep.
- If regressed: rollback and log in `LEARNINGS.md`.
4. Record root-cause for every regression or flat result.

## Team Learning Rules

- Never merge "quality-neutral" complexity without measurable upside.
- Treat flat benchmark deltas as a debugging event, not success.
- Prioritize features that improve Top-1 while preserving Top-5 and calibration.
- Keep experiments small and attributable so wins/losses are diagnosable.
