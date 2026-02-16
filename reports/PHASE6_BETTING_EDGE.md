# Phase 6 Betting Edge Report

Generated: `2026-02-15T23:39:12.880234+00:00`

## Source

- Market Source: `Hockey-Reference Playoff Probabilities`
- Notes: `Probabilities are simulation-based, not sportsbook odds. impliedCupOdds converts cup probability to American odds format.`
- Teams Compared: `23`
- Positive Edge Teams: `11`

## Historical Vegas Validation (strict walk-forward)

- Cup relative Brier edge: `1.84%` (CI: `0.72%` to `3.19%`)
- Cup release-floor status: `PASS` (floor >= `1.5%`, strong >= `3.0%`, stretch >= `5.0%`, moonshot >= `8.0%`)
- Tier reached: `release_floor`
- Model - Vegas Brier (Cup): `-0.0005333521254115674`
- Model - Vegas Log Loss (Cup): `-0.01122582290967973`

## Top Positive Edges

| Team | Model Cup % | Market Cup % | Edge % | Implied Odds | EV (1u) | Kelly f |
|---|---:|---:|---:|---:|---:|---:|
| PIT | 6.91 | 3.70 | 3.21 | 2602 | 0.8671 | 0.0333 |
| VGK | 6.28 | 3.30 | 2.98 | 2930 | 0.9028 | 0.0308 |
| SEA | 4.99 | 2.20 | 2.79 | 4445 | 1.2680 | 0.0285 |
| DET | 5.68 | 3.40 | 2.28 | 2841 | 0.6705 | 0.0236 |
| BOS | 5.28 | 3.00 | 2.28 | 3233 | 0.7598 | 0.0235 |
| UTA | 6.40 | 5.30 | 1.10 | 1786 | 0.2070 | 0.0116 |
| BUF | 6.56 | 5.60 | 0.96 | 1685 | 0.1710 | 0.0101 |
| MTL | 5.69 | 4.90 | 0.79 | 1940 | 0.1608 | 0.0083 |
| EDM | 2.27 | 1.50 | 0.77 | 6566 | 0.5132 | 0.0078 |
| LA | 1.31 | 0.80 | 0.51 | 12400 | 0.6375 | 0.0051 |
| DAL | 9.83 | 9.40 | 0.43 | 963 | 0.0449 | 0.0047 |
