# Phase 3 Weight Optimization (Official Pipeline)

Generated: `2026-02-08T02:26:17.777259+00:00`

## Baseline

- Decay: 0.15
- Cup Winner Boost: 2.0
- Core: `{'top1_accuracy_pct': 16.7, 'top5_accuracy_pct': 58.3, 'average_winner_rank': 6.42, 'playoff_f1': 0.905}`
- Quality: `{'brier_playoff': 0.07303852094561894, 'brier_cup': 0.036367745359850545, 'log_loss_playoff': 0.23408688239132203, 'calibration_error': 0.024577581595219194}`
- Quality Score: `0.201267`

## Candidate Results

| Decay | Cup Boost | Hard Gates | Core Non-Regression | Quality Score |
|---:|---:|---|---|---:|
| 0.10 | 2.00 | True | True | 0.195048 |
| 0.10 | 2.50 | True | True | 0.196501 |
| 0.15 | 2.00 | True | True | 0.201267 |
| 0.15 | 2.50 | True | True | 0.201724 |
| 0.20 | 2.00 | True | True | 0.206100 |
| 0.20 | 2.50 | True | False | 0.206389 |

## Deployment Decision

- Deployed: `True`
- Reason: candidate improved quality score with hard gates + non-regression
- Selected Decay: `0.1`
- Selected Cup Winner Boost: `2.0`
