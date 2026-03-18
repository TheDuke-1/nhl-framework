# Phase 6 Betting Edge Report

Generated: `2026-03-18T13:20:37.172389+00:00`

## Source

- Market Source: `Hockey-Reference Playoff Probabilities`
- Notes: `Probabilities are simulation-based, not sportsbook odds. impliedCupOdds converts cup probability to American odds format.`
- Teams Compared: `21`
- Positive Edge Teams: `11`

## Historical Vegas Validation (strict walk-forward)

- Cup relative Brier edge: `1.79%` (CI: `0.64%` to `3.15%`)
- Cup release-floor status: `PASS` (floor >= `1.5%`, strong >= `3.0%`, stretch >= `5.0%`, moonshot >= `8.0%`)
- Tier reached: `release_floor`
- Model - Vegas Brier (Cup): `-0.0005173718927627448`
- Model - Vegas Log Loss (Cup): `-0.011159931548644572`

## Top Positive Edges

| Team | Model Cup % | Market Cup % | Edge % | Implied Odds | EV (1u) | Kelly f |
|---|---:|---:|---:|---:|---:|---:|
| VGK | 6.38 | 2.40 | 3.98 | 4066 | 1.6579 | 0.0408 |
| EDM | 5.44 | 2.20 | 3.24 | 4445 | 1.4725 | 0.0331 |
| UTA | 8.11 | 5.10 | 3.01 | 1860 | 0.5896 | 0.0317 |
| PIT | 6.26 | 4.70 | 1.56 | 2027 | 0.3315 | 0.0164 |
| NYI | 4.55 | 3.20 | 1.35 | 3025 | 0.4219 | 0.0139 |
| MTL | 5.61 | 4.30 | 1.31 | 2225 | 0.3043 | 0.0137 |
| CAR | 8.45 | 7.70 | 0.75 | 1198 | 0.0968 | 0.0081 |
| MIN | 5.64 | 5.20 | 0.44 | 1823 | 0.0846 | 0.0046 |
| DET | 1.79 | 1.40 | 0.39 | 7042 | 0.2784 | 0.0040 |
| SEA | 0.63 | 0.50 | 0.13 | 19900 | 0.2600 | 0.0013 |
| BOS | 2.29 | 2.20 | 0.09 | 4445 | 0.0408 | 0.0009 |
