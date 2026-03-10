# Phase 6 Betting Edge Report

Generated: `2026-03-10T12:47:51.679976+00:00`

## Source

- Market Source: `Hockey-Reference Playoff Probabilities`
- Notes: `Probabilities are simulation-based, not sportsbook odds. impliedCupOdds converts cup probability to American odds format.`
- Teams Compared: `23`
- Positive Edge Teams: `13`

## Historical Vegas Validation (strict walk-forward)

- Cup relative Brier edge: `1.84%` (CI: `0.72%` to `3.17%`)
- Cup release-floor status: `PASS` (floor >= `1.5%`, strong >= `3.0%`, stretch >= `5.0%`, moonshot >= `8.0%`)
- Tier reached: `release_floor`
- Model - Vegas Brier (Cup): `-0.0005318217442324344`
- Model - Vegas Log Loss (Cup): `-0.011207419430084159`

## Top Positive Edges

| Team | Model Cup % | Market Cup % | Edge % | Implied Odds | EV (1u) | Kelly f |
|---|---:|---:|---:|---:|---:|---:|
| VGK | 5.80 | 2.00 | 3.80 | 4900 | 1.9000 | 0.0388 |
| PIT | 6.94 | 4.30 | 2.64 | 2225 | 0.6136 | 0.0276 |
| DET | 5.10 | 2.50 | 2.60 | 3900 | 1.0400 | 0.0267 |
| EDM | 4.59 | 2.10 | 2.49 | 4661 | 1.1853 | 0.0254 |
| BOS | 4.47 | 2.50 | 1.97 | 3900 | 0.7880 | 0.0202 |
| UTA | 7.47 | 5.60 | 1.87 | 1685 | 0.3334 | 0.0198 |
| MTL | 5.33 | 4.00 | 1.33 | 2400 | 0.3325 | 0.0139 |
| NYI | 4.34 | 3.50 | 0.84 | 2757 | 0.2399 | 0.0087 |
| SJ | 1.40 | 0.60 | 0.80 | 16566 | 1.3332 | 0.0080 |
| DAL | 9.17 | 8.60 | 0.57 | 1062 | 0.0656 | 0.0062 |
| SEA | 1.49 | 1.00 | 0.49 | 9900 | 0.4900 | 0.0049 |
| BUF | 6.73 | 6.60 | 0.13 | 1415 | 0.0196 | 0.0014 |
| LA | 0.14 | 0.10 | 0.04 | 99900 | 0.4000 | 0.0004 |
