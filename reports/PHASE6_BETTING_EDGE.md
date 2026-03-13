# Phase 6 Betting Edge Report

Generated: `2026-03-13T12:46:05.489359+00:00`

## Source

- Market Source: `Hockey-Reference Playoff Probabilities`
- Notes: `Probabilities are simulation-based, not sportsbook odds. impliedCupOdds converts cup probability to American odds format.`
- Teams Compared: `21`
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
| UTA | 7.92 | 3.70 | 4.22 | 2602 | 1.1400 | 0.0438 |
| VGK | 6.60 | 2.60 | 4.00 | 3746 | 1.5384 | 0.0411 |
| EDM | 4.86 | 1.90 | 2.96 | 5163 | 1.5578 | 0.0302 |
| PIT | 6.29 | 3.80 | 2.49 | 2531 | 0.6549 | 0.0259 |
| NYI | 5.18 | 3.40 | 1.78 | 2841 | 0.5234 | 0.0184 |
| SJ | 2.14 | 0.70 | 1.44 | 14185 | 2.0570 | 0.0145 |
| MTL | 5.94 | 4.70 | 1.24 | 2027 | 0.2634 | 0.0130 |
| DET | 2.44 | 1.60 | 0.84 | 6150 | 0.5250 | 0.0085 |
| BUF | 6.95 | 6.30 | 0.65 | 1487 | 0.1030 | 0.0069 |
| CAR | 8.22 | 7.90 | 0.32 | 1165 | 0.0398 | 0.0034 |
| BOS | 2.79 | 2.50 | 0.29 | 3900 | 0.1160 | 0.0030 |
| SEA | 0.32 | 0.10 | 0.22 | 99900 | 2.2000 | 0.0022 |
