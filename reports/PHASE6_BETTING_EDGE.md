# Phase 6 Betting Edge Report

Generated: `2026-03-04T13:06:56.502578+00:00`

## Source

- Market Source: `Hockey-Reference Playoff Probabilities`
- Notes: `Probabilities are simulation-based, not sportsbook odds. impliedCupOdds converts cup probability to American odds format.`
- Teams Compared: `22`
- Positive Edge Teams: `13`

## Historical Vegas Validation (strict walk-forward)

- Cup relative Brier edge: `1.79%` (CI: `0.64%` to `3.15%`)
- Cup release-floor status: `PASS` (floor >= `1.5%`, strong >= `3.0%`, stretch >= `5.0%`, moonshot >= `8.0%`)
- Tier reached: `release_floor`
- Model - Vegas Brier (Cup): `-0.0005173718927627448`
- Model - Vegas Log Loss (Cup): `-0.011159931548644572`

## Top Positive Edges

| Team | Model Cup % | Market Cup % | Edge % | Implied Odds | EV (1u) | Kelly f |
|---|---:|---:|---:|---:|---:|---:|
| VGK | 6.13 | 2.80 | 3.33 | 3471 | 1.1890 | 0.0343 |
| SEA | 4.79 | 1.60 | 3.19 | 6150 | 1.9938 | 0.0324 |
| MTL | 5.15 | 2.80 | 2.35 | 3471 | 0.8391 | 0.0242 |
| BOS | 4.79 | 2.50 | 2.29 | 3900 | 0.9160 | 0.0235 |
| DET | 5.41 | 3.30 | 2.11 | 2930 | 0.6392 | 0.0218 |
| NYI | 4.93 | 2.90 | 2.03 | 3348 | 0.6999 | 0.0209 |
| PIT | 7.29 | 5.50 | 1.79 | 1718 | 0.3253 | 0.0189 |
| BUF | 6.66 | 5.70 | 0.96 | 1654 | 0.1682 | 0.0102 |
| UTA | 6.11 | 5.40 | 0.71 | 1751 | 0.1310 | 0.0075 |
| EDM | 2.49 | 2.00 | 0.49 | 4900 | 0.2450 | 0.0050 |
| CAR | 8.39 | 8.00 | 0.39 | 1150 | 0.0487 | 0.0042 |
| CBJ | 0.90 | 0.70 | 0.20 | 14185 | 0.2857 | 0.0020 |
| SJ | 0.99 | 0.90 | 0.09 | 11011 | 0.1000 | 0.0009 |
