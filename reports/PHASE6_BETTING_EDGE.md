# Phase 6 Betting Edge Report

Generated: `2026-03-08T12:56:01.539494+00:00`

## Source

- Market Source: `Hockey-Reference Playoff Probabilities`
- Notes: `Probabilities are simulation-based, not sportsbook odds. impliedCupOdds converts cup probability to American odds format.`
- Teams Compared: `25`
- Positive Edge Teams: `9`

## Historical Vegas Validation (strict walk-forward)

- Cup relative Brier edge: `1.79%` (CI: `0.64%` to `3.15%`)
- Cup release-floor status: `PASS` (floor >= `1.5%`, strong >= `3.0%`, stretch >= `5.0%`, moonshot >= `8.0%`)
- Tier reached: `release_floor`
- Model - Vegas Brier (Cup): `-0.0005173718927627448`
- Model - Vegas Log Loss (Cup): `-0.011159931548644572`

## Top Positive Edges

| Team | Model Cup % | Market Cup % | Edge % | Implied Odds | EV (1u) | Kelly f |
|---|---:|---:|---:|---:|---:|---:|
| VGK | 5.69 | 1.80 | 3.89 | 5455 | 2.1608 | 0.0396 |
| UTA | 7.51 | 4.90 | 2.61 | 1940 | 0.5320 | 0.0274 |
| DET | 4.77 | 2.20 | 2.57 | 4445 | 1.1680 | 0.0263 |
| PIT | 5.75 | 3.70 | 2.05 | 2602 | 0.5537 | 0.0213 |
| MTL | 4.91 | 3.70 | 1.21 | 2602 | 0.3267 | 0.0126 |
| BOS | 4.20 | 3.00 | 1.20 | 3233 | 0.3999 | 0.0124 |
| SJ | 1.45 | 0.60 | 0.85 | 16566 | 1.4166 | 0.0086 |
| SEA | 1.60 | 0.80 | 0.80 | 12400 | 1.0000 | 0.0081 |
| EDM | 1.82 | 1.20 | 0.62 | 8233 | 0.5166 | 0.0063 |
