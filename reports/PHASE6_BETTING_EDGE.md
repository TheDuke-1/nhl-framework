# Phase 6 Betting Edge Report

Generated: `2026-03-15T13:02:15.976996+00:00`

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
| VGK | 6.63 | 3.60 | 3.03 | 2677 | 0.8412 | 0.0314 |
| EDM | 4.36 | 1.40 | 2.96 | 7042 | 2.1139 | 0.0300 |
| UTA | 6.65 | 3.90 | 2.75 | 2464 | 0.7051 | 0.0286 |
| NYI | 4.32 | 1.70 | 2.62 | 5782 | 1.5410 | 0.0267 |
| BOS | 4.42 | 2.70 | 1.72 | 3603 | 0.6367 | 0.0177 |
| PIT | 6.10 | 4.40 | 1.70 | 2172 | 0.3859 | 0.0178 |
| SJ | 2.46 | 1.10 | 1.36 | 8990 | 1.2361 | 0.0138 |
| MTL | 5.71 | 5.20 | 0.51 | 1823 | 0.0980 | 0.0054 |
| DET | 1.54 | 1.30 | 0.24 | 7592 | 0.1846 | 0.0024 |
| SEA | 0.59 | 0.50 | 0.09 | 19900 | 0.1800 | 0.0009 |
