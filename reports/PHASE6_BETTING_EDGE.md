# Phase 6 Betting Edge Report

Generated: `2026-02-26T03:37:02.345764+00:00`

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
| SEA | 5.15 | 1.50 | 3.65 | 6566 | 2.4330 | 0.0371 |
| VGK | 6.61 | 3.10 | 3.51 | 3125 | 1.1317 | 0.0362 |
| DET | 5.47 | 2.20 | 3.27 | 4445 | 1.4861 | 0.0334 |
| EDM | 4.43 | 1.50 | 2.93 | 6566 | 1.9530 | 0.0297 |
| PIT | 6.68 | 3.90 | 2.78 | 2464 | 0.7128 | 0.0289 |
| BUF | 5.61 | 3.40 | 2.21 | 2841 | 0.6499 | 0.0229 |
| BOS | 5.57 | 3.50 | 2.07 | 2757 | 0.5913 | 0.0214 |
| MTL | 5.96 | 4.10 | 1.86 | 2339 | 0.4536 | 0.0194 |
| CBJ | 1.22 | 0.90 | 0.32 | 11011 | 0.3555 | 0.0032 |
| UTA | 6.26 | 6.10 | 0.16 | 1539 | 0.0260 | 0.0017 |
| DAL | 9.01 | 9.00 | 0.01 | 1011 | 0.0010 | 0.0001 |
