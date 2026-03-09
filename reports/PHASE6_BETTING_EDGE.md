# Phase 6 Betting Edge Report

Generated: `2026-03-09T12:50:18.185830+00:00`

## Source

- Market Source: `Hockey-Reference Playoff Probabilities`
- Notes: `Probabilities are simulation-based, not sportsbook odds. impliedCupOdds converts cup probability to American odds format.`
- Teams Compared: `23`
- Positive Edge Teams: `12`

## Historical Vegas Validation (strict walk-forward)

- Cup relative Brier edge: `1.84%` (CI: `0.72%` to `3.17%`)
- Cup release-floor status: `PASS` (floor >= `1.5%`, strong >= `3.0%`, stretch >= `5.0%`, moonshot >= `8.0%`)
- Tier reached: `release_floor`
- Model - Vegas Brier (Cup): `-0.0005318217442324344`
- Model - Vegas Log Loss (Cup): `-0.011207419430084159`

## Top Positive Edges

| Team | Model Cup % | Market Cup % | Edge % | Implied Odds | EV (1u) | Kelly f |
|---|---:|---:|---:|---:|---:|---:|
| VGK | 5.81 | 2.50 | 3.31 | 3900 | 1.3240 | 0.0339 |
| EDM | 4.49 | 1.90 | 2.59 | 5163 | 1.3631 | 0.0264 |
| DET | 4.95 | 2.40 | 2.55 | 4066 | 1.0622 | 0.0261 |
| BOS | 4.47 | 2.20 | 2.27 | 4445 | 1.0316 | 0.0232 |
| PIT | 7.03 | 4.90 | 2.13 | 1940 | 0.4341 | 0.0224 |
| UTA | 7.68 | 6.30 | 1.38 | 1487 | 0.2188 | 0.0147 |
| MTL | 5.52 | 4.50 | 1.02 | 2122 | 0.2265 | 0.0107 |
| DAL | 9.49 | 8.70 | 0.79 | 1049 | 0.0904 | 0.0086 |
| SJ | 1.55 | 0.80 | 0.75 | 12400 | 0.9375 | 0.0076 |
| SEA | 1.61 | 0.90 | 0.71 | 11011 | 0.7889 | 0.0072 |
| NYI | 2.69 | 2.20 | 0.49 | 4445 | 0.2226 | 0.0050 |
| CBJ | 1.37 | 1.30 | 0.07 | 7592 | 0.0538 | 0.0007 |
