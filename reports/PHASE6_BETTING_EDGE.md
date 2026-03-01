# Phase 6 Betting Edge Report

Generated: `2026-03-01T12:56:52.758060+00:00`

## Source

- Market Source: `Hockey-Reference Playoff Probabilities`
- Notes: `Probabilities are simulation-based, not sportsbook odds. impliedCupOdds converts cup probability to American odds format.`
- Teams Compared: `23`
- Positive Edge Teams: `9`

## Historical Vegas Validation (strict walk-forward)

- Cup relative Brier edge: `1.79%` (CI: `0.64%` to `3.15%`)
- Cup release-floor status: `PASS` (floor >= `1.5%`, strong >= `3.0%`, stretch >= `5.0%`, moonshot >= `8.0%`)
- Tier reached: `release_floor`
- Model - Vegas Brier (Cup): `-0.0005173718927627448`
- Model - Vegas Log Loss (Cup): `-0.011159931548644572`

## Top Positive Edges

| Team | Model Cup % | Market Cup % | Edge % | Implied Odds | EV (1u) | Kelly f |
|---|---:|---:|---:|---:|---:|---:|
| SEA | 4.62 | 0.70 | 3.92 | 14185 | 5.5997 | 0.0395 |
| PIT | 7.41 | 4.00 | 3.41 | 2400 | 0.8525 | 0.0355 |
| DET | 5.57 | 2.50 | 3.07 | 3900 | 1.2280 | 0.0315 |
| VGK | 6.08 | 3.30 | 2.78 | 2930 | 0.8422 | 0.0287 |
| NYI | 5.07 | 2.90 | 2.17 | 3348 | 0.7481 | 0.0223 |
| BUF | 6.53 | 4.70 | 1.83 | 2027 | 0.3889 | 0.0192 |
| MTL | 5.67 | 3.90 | 1.77 | 2464 | 0.4538 | 0.0184 |
| BOS | 4.90 | 3.20 | 1.70 | 3025 | 0.5313 | 0.0176 |
| UTA | 6.59 | 5.20 | 1.39 | 1823 | 0.2673 | 0.0147 |
