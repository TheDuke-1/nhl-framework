# Phase 6 Betting Edge Report

Generated: `2026-03-14T13:00:31.485882+00:00`

## Source

- Market Source: `Hockey-Reference Playoff Probabilities`
- Notes: `Probabilities are simulation-based, not sportsbook odds. impliedCupOdds converts cup probability to American odds format.`
- Teams Compared: `22`
- Positive Edge Teams: `12`

## Historical Vegas Validation (strict walk-forward)

- Cup relative Brier edge: `1.79%` (CI: `0.64%` to `3.15%`)
- Cup release-floor status: `PASS` (floor >= `1.5%`, strong >= `3.0%`, stretch >= `5.0%`, moonshot >= `8.0%`)
- Tier reached: `release_floor`
- Model - Vegas Brier (Cup): `-0.0005173718927627448`
- Model - Vegas Log Loss (Cup): `-0.011159931548644572`

## Top Positive Edges

| Team | Model Cup % | Market Cup % | Edge % | Implied Odds | EV (1u) | Kelly f |
|---|---:|---:|---:|---:|---:|---:|
| VGK | 6.47 | 2.30 | 4.17 | 4247 | 1.8125 | 0.0427 |
| UTA | 8.08 | 4.30 | 3.78 | 2225 | 0.8786 | 0.0395 |
| EDM | 4.58 | 2.00 | 2.58 | 4900 | 1.2900 | 0.0263 |
| PIT | 6.34 | 4.50 | 1.84 | 2122 | 0.4087 | 0.0193 |
| BOS | 4.34 | 2.70 | 1.64 | 3603 | 0.6071 | 0.0168 |
| DET | 2.47 | 0.90 | 1.57 | 11011 | 1.7444 | 0.0158 |
| MTL | 5.65 | 4.40 | 1.25 | 2172 | 0.2837 | 0.0131 |
| CAR | 8.70 | 7.90 | 0.80 | 1165 | 0.1005 | 0.0086 |
| SJ | 1.75 | 1.00 | 0.75 | 9900 | 0.7500 | 0.0076 |
| NYI | 2.38 | 1.70 | 0.68 | 5782 | 0.3999 | 0.0069 |
| DAL | 10.22 | 10.20 | 0.02 | 880 | 0.0016 | 0.0002 |
| LA | 0.61 | 0.60 | 0.01 | 16566 | 0.0166 | 0.0001 |
