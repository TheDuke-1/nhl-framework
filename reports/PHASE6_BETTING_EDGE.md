# Phase 6 Betting Edge Report

Generated: `2026-03-16T13:01:24.702674+00:00`

## Source

- Market Source: `Hockey-Reference Playoff Probabilities`
- Notes: `Probabilities are simulation-based, not sportsbook odds. impliedCupOdds converts cup probability to American odds format.`
- Teams Compared: `23`
- Positive Edge Teams: `10`

## Historical Vegas Validation (strict walk-forward)

- Cup relative Brier edge: `1.84%` (CI: `0.72%` to `3.17%`)
- Cup release-floor status: `PASS` (floor >= `1.5%`, strong >= `3.0%`, stretch >= `5.0%`, moonshot >= `8.0%`)
- Tier reached: `release_floor`
- Model - Vegas Brier (Cup): `-0.0005318217442324344`
- Model - Vegas Log Loss (Cup): `-0.011207419430084159`

## Top Positive Edges

| Team | Model Cup % | Market Cup % | Edge % | Implied Odds | EV (1u) | Kelly f |
|---|---:|---:|---:|---:|---:|---:|
| VGK | 6.45 | 2.80 | 3.65 | 3471 | 1.3033 | 0.0375 |
| PIT | 6.26 | 3.00 | 3.26 | 3233 | 1.0865 | 0.0336 |
| UTA | 6.85 | 3.70 | 3.15 | 2602 | 0.8509 | 0.0327 |
| EDM | 5.27 | 2.90 | 2.37 | 3348 | 0.8171 | 0.0244 |
| BOS | 4.78 | 2.60 | 2.18 | 3746 | 0.8384 | 0.0224 |
| MTL | 5.40 | 3.60 | 1.80 | 2677 | 0.4996 | 0.0187 |
| NYI | 4.64 | 3.30 | 1.34 | 2930 | 0.4059 | 0.0139 |
| SJ | 1.32 | 0.30 | 1.02 | 33233 | 3.4000 | 0.0102 |
| SEA | 1.35 | 0.60 | 0.75 | 16566 | 1.2499 | 0.0075 |
| DET | 1.57 | 1.50 | 0.07 | 6566 | 0.0466 | 0.0007 |
