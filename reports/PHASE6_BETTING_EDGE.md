# Phase 6 Betting Edge Report

Generated: `2026-03-12T13:09:00.331375+00:00`

## Source

- Market Source: `Hockey-Reference Playoff Probabilities`
- Notes: `Probabilities are simulation-based, not sportsbook odds. impliedCupOdds converts cup probability to American odds format.`
- Teams Compared: `21`
- Positive Edge Teams: `8`

## Historical Vegas Validation (strict walk-forward)

- Cup relative Brier edge: `1.79%` (CI: `0.64%` to `3.15%`)
- Cup release-floor status: `PASS` (floor >= `1.5%`, strong >= `3.0%`, stretch >= `5.0%`, moonshot >= `8.0%`)
- Tier reached: `release_floor`
- Model - Vegas Brier (Cup): `-0.0005173718927627448`
- Model - Vegas Log Loss (Cup): `-0.011159931548644572`

## Top Positive Edges

| Team | Model Cup % | Market Cup % | Edge % | Implied Odds | EV (1u) | Kelly f |
|---|---:|---:|---:|---:|---:|---:|
| VGK | 4.85 | 1.80 | 3.05 | 5455 | 1.6942 | 0.0311 |
| UTA | 7.16 | 4.40 | 2.76 | 2172 | 0.6268 | 0.0289 |
| EDM | 5.30 | 3.10 | 2.20 | 3125 | 0.7093 | 0.0227 |
| DET | 3.97 | 1.80 | 2.17 | 5455 | 1.2053 | 0.0221 |
| BOS | 4.25 | 2.20 | 2.05 | 4445 | 0.9316 | 0.0210 |
| PIT | 5.60 | 4.20 | 1.40 | 2280 | 0.3328 | 0.0146 |
| NYI | 3.89 | 2.80 | 1.09 | 3471 | 0.3891 | 0.0112 |
| SJ | 0.78 | 0.40 | 0.38 | 24900 | 0.9500 | 0.0038 |
