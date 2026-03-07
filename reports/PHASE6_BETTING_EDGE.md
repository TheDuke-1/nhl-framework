# Phase 6 Betting Edge Report

Generated: `2026-03-07T12:58:59.004622+00:00`

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
| SEA | 3.97 | 0.70 | 3.27 | 14185 | 4.6711 | 0.0329 |
| VGK | 5.88 | 2.90 | 2.98 | 3348 | 1.0274 | 0.0307 |
| PIT | 6.03 | 3.60 | 2.43 | 2677 | 0.6745 | 0.0252 |
| UTA | 7.41 | 5.50 | 1.91 | 1718 | 0.3471 | 0.0202 |
| DET | 4.74 | 3.20 | 1.54 | 3025 | 0.4813 | 0.0159 |
| MTL | 4.88 | 3.70 | 1.18 | 2602 | 0.3186 | 0.0122 |
| CBJ | 1.58 | 0.90 | 0.68 | 11011 | 0.7555 | 0.0069 |
| SJ | 1.28 | 0.70 | 0.58 | 14185 | 0.8285 | 0.0058 |
| EDM | 1.68 | 1.40 | 0.28 | 7042 | 0.1999 | 0.0028 |
| BOS | 2.45 | 2.20 | 0.25 | 4445 | 0.1135 | 0.0026 |
