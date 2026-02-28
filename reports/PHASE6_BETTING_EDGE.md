# Phase 6 Betting Edge Report

Generated: `2026-02-28T12:56:33.425227+00:00`

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
| UTA | 7.22 | 3.80 | 3.42 | 2531 | 0.8996 | 0.0355 |
| NYI | 4.63 | 1.80 | 2.83 | 5455 | 1.5720 | 0.0288 |
| VGK | 6.22 | 3.50 | 2.72 | 2757 | 0.7771 | 0.0282 |
| MTL | 5.61 | 3.30 | 2.31 | 2930 | 0.6998 | 0.0239 |
| DET | 5.83 | 3.70 | 2.13 | 2602 | 0.5753 | 0.0221 |
| BOS | 5.28 | 3.20 | 2.08 | 3025 | 0.6500 | 0.0215 |
| BUF | 6.36 | 4.60 | 1.76 | 2073 | 0.3820 | 0.0184 |
| SEA | 2.14 | 0.50 | 1.64 | 19900 | 3.2800 | 0.0165 |
| EDM | 5.09 | 3.50 | 1.59 | 2757 | 0.4542 | 0.0165 |
| PIT | 7.32 | 5.90 | 1.42 | 1594 | 0.2400 | 0.0151 |
| NSH | 0.30 | 0.10 | 0.20 | 99900 | 2.0000 | 0.0020 |
