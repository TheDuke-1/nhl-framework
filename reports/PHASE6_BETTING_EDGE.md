# Phase 6 Betting Edge Report

Generated: `2026-02-16T04:22:39.595981+00:00`

## Source

- Market Source: `Hockey-Reference Playoff Probabilities`
- Notes: `Probabilities are simulation-based, not sportsbook odds. impliedCupOdds converts cup probability to American odds format.`
- Teams Compared: `24`
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
| VGK | 6.25 | 2.70 | 3.55 | 3603 | 1.3144 | 0.0365 |
| SEA | 4.82 | 1.40 | 3.42 | 7042 | 2.4424 | 0.0347 |
| DET | 5.35 | 2.20 | 3.15 | 4445 | 1.4316 | 0.0322 |
| BOS | 5.29 | 2.90 | 2.39 | 3348 | 0.8240 | 0.0246 |
| EDM | 4.35 | 2.20 | 2.15 | 4445 | 0.9771 | 0.0220 |
| UTA | 6.21 | 4.10 | 2.11 | 2339 | 0.5146 | 0.0220 |
| PIT | 6.54 | 4.50 | 2.04 | 2122 | 0.4532 | 0.0214 |
| MTL | 5.85 | 4.50 | 1.35 | 2122 | 0.2999 | 0.0141 |
| DAL | 9.43 | 8.10 | 1.33 | 1134 | 0.1637 | 0.0144 |
| BUF | 5.68 | 4.50 | 1.18 | 2122 | 0.2621 | 0.0124 |
| NYI | 2.23 | 2.10 | 0.13 | 4661 | 0.0617 | 0.0013 |
