# Phase 3B Profile Grid

Generated: `2026-02-08T02:41:33.489457+00:00`

## Baseline

- Profile Version: `phase3-optimized-2026-02-08`
- Quality Score: `0.190633`
- Core: `{'top1_accuracy_pct': 16.7, 'top5_accuracy_pct': 58.3, 'average_winner_rank': 6.0, 'playoff_f1': 0.905}`
- Quality: `{'brier_playoff': 0.07251472422178856, 'brier_cup': 0.030790591224907633, 'log_loss_playoff': 0.2326178541696349, 'calibration_error': 0.020936700149755155}`

## Candidates

| Candidate | Hard Gates | Core Non-Regression | Quality Score |
|---|---|---|---:|
| baseline | True | True | 0.190633 |
| gb-heavy | True | True | 0.190633 |
| mc-heavy | True | True | 0.190633 |
| nn-heavy | True | True | 0.190633 |
| decay-010 | True | True | 0.190633 |
| decay-020 | True | False | 0.200604 |

## Decision

- Deployed: `False`
- Candidate: `baseline`
- Reason: no candidate improved quality score under hard-gate + non-regression constraints
- Active Profile Version: `phase3-optimized-2026-02-08`
