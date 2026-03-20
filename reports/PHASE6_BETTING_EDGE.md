# Phase 6 Betting Edge Report

Generated: `2026-03-20T13:08:12.071847+00:00`

## Source

- Market Source: `Hockey-Reference Playoff Probabilities`
- Notes: `Probabilities are simulation-based, not sportsbook odds. impliedCupOdds converts cup probability to American odds format.`
- Teams Compared: `22`
- Positive Edge Teams: `10`

## Historical Vegas Validation (strict walk-forward)

- Cup relative Brier edge: `1.79%` (CI: `0.64%` to `3.15%`)
- Cup release-floor status: `PASS` (floor >= `1.5%`, strong >= `3.0%`, stretch >= `5.0%`, moonshot >= `8.0%`)
- Tier reached: `release_floor`
- Model - Vegas Brier (Cup): `-0.0005173718927627448`
- Model - Vegas Log Loss (Cup): `-0.011159931548644572`

## Top Positive Edges

| Team | Model Cup % | Market Cup % | Edge % | Implied Odds | EV (1u) | Kelly f |
|---|---:|---:|---:|---:|---:|---:|
| VGK | 6.11 | 2.40 | 3.71 | 4066 | 1.5454 | 0.0380 |
| EDM | 5.42 | 1.80 | 3.62 | 5455 | 2.0108 | 0.0369 |
| CBJ | 4.94 | 2.10 | 2.84 | 4661 | 1.3519 | 0.0290 |
| DET | 4.35 | 1.80 | 2.55 | 5455 | 1.4164 | 0.0260 |
| MTL | 5.00 | 2.60 | 2.40 | 3746 | 0.9230 | 0.0246 |
| BOS | 4.68 | 2.60 | 2.08 | 3746 | 0.7999 | 0.0214 |
| UTA | 8.00 | 6.30 | 1.70 | 1487 | 0.2696 | 0.0181 |
| PIT | 5.96 | 4.80 | 1.16 | 1983 | 0.2415 | 0.0122 |
| LA | 0.95 | 0.60 | 0.35 | 16566 | 0.5833 | 0.0035 |
| NSH | 0.28 | 0.20 | 0.08 | 49900 | 0.4000 | 0.0008 |
