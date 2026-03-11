# Phase 6 Betting Edge Report

Generated: `2026-03-11T13:10:04.734580+00:00`

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
| VGK | 4.58 | 1.40 | 3.18 | 7042 | 2.2710 | 0.0322 |
| EDM | 5.50 | 2.40 | 3.10 | 4066 | 1.2913 | 0.0318 |
| UTA | 7.13 | 4.30 | 2.83 | 2225 | 0.6577 | 0.0296 |
| BOS | 4.01 | 2.40 | 1.61 | 4066 | 0.6706 | 0.0165 |
| PIT | 5.66 | 4.20 | 1.46 | 2280 | 0.3471 | 0.0152 |
| DET | 3.94 | 2.60 | 1.34 | 3746 | 0.5153 | 0.0138 |
| NYI | 3.87 | 2.70 | 1.17 | 3603 | 0.4331 | 0.0120 |
| MTL | 4.97 | 4.00 | 0.97 | 2400 | 0.2425 | 0.0101 |
| SJ | 0.80 | 0.30 | 0.50 | 33233 | 1.6666 | 0.0050 |
| SEA | 0.78 | 0.60 | 0.18 | 16566 | 0.2999 | 0.0018 |
