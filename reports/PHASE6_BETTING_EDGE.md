# Phase 6 Betting Edge Report

Generated: `2026-03-19T13:12:01.669714+00:00`

## Source

- Market Source: `Hockey-Reference Playoff Probabilities`
- Notes: `Probabilities are simulation-based, not sportsbook odds. impliedCupOdds converts cup probability to American odds format.`
- Teams Compared: `22`
- Positive Edge Teams: `12`

## Historical Vegas Validation (strict walk-forward)

- Cup relative Brier edge: `1.79%` (CI: `0.64%` to `3.15%`)
- Cup release-floor status: `PASS` (floor >= `1.5%`, strong >= `3.0%`, stretch >= `5.0%`, moonshot >= `8.0%`)
- Tier reached: `release_floor`
- Model - Vegas Brier (Cup): `-0.0005173718927627448`
- Model - Vegas Log Loss (Cup): `-0.011159931548644572`

## Top Positive Edges

| Team | Model Cup % | Market Cup % | Edge % | Implied Odds | EV (1u) | Kelly f |
|---|---:|---:|---:|---:|---:|---:|
| VGK | 6.44 | 2.60 | 3.84 | 3746 | 1.4768 | 0.0394 |
| UTA | 8.27 | 4.70 | 3.57 | 2027 | 0.7590 | 0.0374 |
| EDM | 5.65 | 2.10 | 3.55 | 4661 | 1.6900 | 0.0363 |
| PIT | 6.73 | 4.80 | 1.93 | 1983 | 0.4019 | 0.0203 |
| CBJ | 2.64 | 1.30 | 1.34 | 7592 | 1.0307 | 0.0136 |
| MTL | 5.76 | 4.60 | 1.16 | 2073 | 0.2516 | 0.0121 |
| NYI | 4.71 | 3.90 | 0.81 | 2464 | 0.2076 | 0.0084 |
| DET | 2.19 | 1.50 | 0.69 | 6566 | 0.4599 | 0.0070 |
| MIN | 5.95 | 5.40 | 0.55 | 1751 | 0.1013 | 0.0058 |
| SEA | 0.66 | 0.30 | 0.36 | 33233 | 1.2000 | 0.0036 |
| SJ | 0.55 | 0.40 | 0.15 | 24900 | 0.3750 | 0.0015 |
| BOS | 2.21 | 2.20 | 0.01 | 4445 | 0.0044 | 0.0001 |
