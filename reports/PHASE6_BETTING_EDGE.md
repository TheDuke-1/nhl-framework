# Phase 6 Betting Edge Report

Generated: `2026-03-03T13:09:14.865485+00:00`

## Source

- Market Source: `Hockey-Reference Playoff Probabilities`
- Notes: `Probabilities are simulation-based, not sportsbook odds. impliedCupOdds converts cup probability to American odds format.`
- Teams Compared: `23`
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
| SEA | 5.30 | 0.90 | 4.40 | 11011 | 4.8888 | 0.0444 |
| DET | 5.39 | 2.10 | 3.29 | 4661 | 1.5662 | 0.0336 |
| VGK | 6.16 | 3.20 | 2.96 | 3025 | 0.9250 | 0.0306 |
| BOS | 4.51 | 1.80 | 2.71 | 5455 | 1.5053 | 0.0276 |
| PIT | 7.53 | 5.00 | 2.53 | 1899 | 0.5052 | 0.0266 |
| UTA | 6.06 | 4.00 | 2.06 | 2400 | 0.5150 | 0.0215 |
| MTL | 5.85 | 4.10 | 1.75 | 2339 | 0.4268 | 0.0182 |
| NYI | 5.00 | 3.40 | 1.60 | 2841 | 0.4705 | 0.0166 |
| EDM | 2.28 | 1.80 | 0.48 | 5455 | 0.2665 | 0.0049 |
| SJ | 0.74 | 0.50 | 0.24 | 19900 | 0.4800 | 0.0024 |
| BUF | 6.18 | 6.00 | 0.18 | 1566 | 0.0296 | 0.0019 |
