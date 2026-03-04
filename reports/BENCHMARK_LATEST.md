# Latest Benchmark Metrics

Generated: `2026-03-04T13:17:28.344367+00:00`
Model Version: `backtest-v2.4-2026-43d92c3204-20e65069f8-14b5b16284`
Profile Version: `phase9-cup-edge-2026-02-13`
Comparison baseline: last distinct snapshot (skipped `14` identical run(s)).

## Evaluation Contract

- Contract Version: `phase-3-tiered-cup-vegas-target-2026-02-15`
- Strict Walk-Forward Leakage-Free: `True`
- Benchmark strict verification: `True`
- Vegas diagnostic random seed: `42`
- Quality CV strict mode: `False` (set `BENCHMARK_QUALITY_STRICT_CV=1` to enforce strict CV model fitting).

## Core 4 Metrics

| Metric | Current | Previous | Delta |
|---|---:|---:|---:|
| Cup Top-1 Accuracy (%) | 40.0 | 40.0 | 0.0 |
| Cup Top-5 Accuracy (%) | 60.0 | 60.0 | 0.0 |
| Average Winner Rank (lower better) | 4.60 | 4.60 | 0.00 |
| Playoff F1 | 0.974 | 0.974 | 0.000 |

## Probability Quality

| Metric | Current | Previous | Delta |
|---|---:|---:|---:|
| Brier Playoff (lower better) | 0.058 | 0.058 | 0.000 |
| Brier Cup (lower better) | 0.029 | 0.029 | 0.000 |
| Log Loss Playoff (lower better) | 0.242 | 0.242 | 0.000 |
| Calibration Error (lower better) | 0.165 | 0.165 | -0.000 |

## Checkpoint Playoff F1

| Metric | Current | Previous | Delta |
|---|---:|---:|---:|
| Games 0 Playoff F1 | 0.672 | 0.672 | 0.000 |
| Games 20 Playoff F1 | 0.924 | 0.924 | 0.000 |
| Games 40 Playoff F1 | 0.930 | 0.930 | 0.000 |
| Games 60 Playoff F1 | 0.936 | 0.936 | 0.000 |

## Data Coverage

| Metric | Current | Previous | Delta |
|---|---:|---:|---:|
| Advanced Accepted Season Ratio | 1.000 | 1.000 | 0.000 |
| Advanced Accepted Team Ratio | 0.958 | 0.958 | 0.000 |
| Advanced Raw Team Ratio | 0.958 | 0.958 | 0.000 |

## Vegas Comparison

| Metric | Current | Previous | Delta |
|---|---:|---:|---:|
| Model - Vegas Brier (Playoff) | -0.130 | -0.130 | 0.000 |
| Model - Vegas Brier (Cup) | -0.001 | -0.001 | 0.000 |
| Model - Vegas Log Loss (Playoff) | -0.358 | -0.358 | 0.000 |
| Model - Vegas Log Loss (Cup) | -0.011 | -0.011 | 0.000 |
| Cup Relative Brier Edge | 0.018 | 0.018 | -0.001 |
| Cup Relative Brier Edge CI Low | 0.006 | 0.007 | -0.001 |
| Cup Relative Brier Edge CI High | 0.032 | 0.032 | -0.000 |

### Cup-Vegas Tiered Target

- Thresholds: release floor `>= 0.015`, strong `>= 0.030`, stretch `>= 0.050`, moonshot `>= 0.080`
- Confidence gate: CI low `> 0.00` at `0.95` confidence
- Sustainability gate: `>= 10` seasons and `>= 0.60` positive-season ratio
- Current: edge `0.018`, CI [`0.006`, `0.032`], positive seasons `9`/`10`
- Release gate status: `PASS`
- Tier reached: `release_floor`
