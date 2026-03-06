# Phase 6 Betting Edge Report

Generated: `2026-03-06T13:05:36.575308+00:00`

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
| MTL | 5.50 | 2.00 | 3.50 | 4900 | 1.7500 | 0.0357 |
| DET | 5.55 | 2.60 | 2.95 | 3746 | 1.1345 | 0.0303 |
| VGK | 6.06 | 3.50 | 2.56 | 2757 | 0.7313 | 0.0265 |
| BUF | 7.78 | 5.50 | 2.28 | 1718 | 0.4144 | 0.0241 |
| PIT | 6.64 | 4.80 | 1.84 | 1983 | 0.3831 | 0.0193 |
| UTA | 6.96 | 5.20 | 1.76 | 1823 | 0.3384 | 0.0186 |
| BOS | 4.43 | 2.70 | 1.73 | 3603 | 0.6404 | 0.0178 |
| SEA | 2.38 | 0.90 | 1.48 | 11011 | 1.6444 | 0.0149 |
| CBJ | 1.64 | 1.00 | 0.64 | 9900 | 0.6400 | 0.0065 |
| NYI | 2.29 | 1.70 | 0.59 | 5782 | 0.3470 | 0.0060 |
| EDM | 2.53 | 2.30 | 0.23 | 4247 | 0.0998 | 0.0023 |
