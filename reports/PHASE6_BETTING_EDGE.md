# Phase 6 Betting Edge Report

Generated: `2026-03-02T13:09:24.960849+00:00`

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
| DET | 5.47 | 2.10 | 3.37 | 4661 | 1.6043 | 0.0344 |
| SEA | 4.24 | 0.90 | 3.34 | 11011 | 3.7111 | 0.0337 |
| BOS | 5.02 | 1.80 | 3.22 | 5455 | 1.7886 | 0.0328 |
| VGK | 6.33 | 3.20 | 3.13 | 3025 | 0.9781 | 0.0323 |
| UTA | 5.97 | 4.00 | 1.97 | 2400 | 0.4925 | 0.0205 |
| NYI | 5.10 | 3.40 | 1.70 | 2841 | 0.4999 | 0.0176 |
| PIT | 6.62 | 5.00 | 1.62 | 1899 | 0.3233 | 0.0170 |
| MTL | 5.61 | 4.10 | 1.51 | 2339 | 0.3683 | 0.0157 |
| BUF | 7.45 | 6.00 | 1.45 | 1566 | 0.2412 | 0.0154 |
| EDM | 2.41 | 1.80 | 0.61 | 5455 | 0.3388 | 0.0062 |
| SJ | 0.71 | 0.50 | 0.21 | 19900 | 0.4200 | 0.0021 |
