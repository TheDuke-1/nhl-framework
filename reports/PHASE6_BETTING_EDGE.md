# Phase 6 Betting Edge Report

Generated: `2026-03-05T13:10:54.773693+00:00`

## Source

- Market Source: `Hockey-Reference Playoff Probabilities`
- Notes: `Probabilities are simulation-based, not sportsbook odds. impliedCupOdds converts cup probability to American odds format.`
- Teams Compared: `23`
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
| MTL | 5.31 | 2.00 | 3.31 | 4900 | 1.6550 | 0.0338 |
| NYI | 4.57 | 1.70 | 2.87 | 5782 | 1.6881 | 0.0292 |
| DET | 5.34 | 2.60 | 2.74 | 3746 | 1.0538 | 0.0281 |
| VGK | 5.85 | 3.50 | 2.35 | 2757 | 0.6713 | 0.0244 |
| BOS | 5.03 | 2.70 | 2.33 | 3603 | 0.8626 | 0.0239 |
| EDM | 4.29 | 2.30 | 1.99 | 4247 | 0.8649 | 0.0204 |
| PIT | 6.72 | 4.80 | 1.92 | 1983 | 0.3998 | 0.0202 |
| SEA | 2.45 | 0.90 | 1.55 | 11011 | 1.7222 | 0.0156 |
| BUF | 6.82 | 5.50 | 1.32 | 1718 | 0.2399 | 0.0140 |
| UTA | 6.49 | 5.20 | 1.29 | 1823 | 0.2480 | 0.0136 |
