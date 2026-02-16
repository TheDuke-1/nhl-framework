# Historical Vegas Odds Import

Place raw historical odds CSV files in this folder, then run:

```bash
python3 scripts/import_historical_vegas_odds.py
```

The importer normalizes common column names and writes benchmark files to:

- `data/historical/verified/vegas_odds_YYYY.csv`

Minimum required per row:

- Team (`team` or similar)
- Cup market signal (`cup_odds_american` or `cup_implied_prob`)
- Playoff market signal (`playoff_odds_american` or `playoff_implied_prob`)

If actual outcomes are missing in raw files, the importer fills:

- `actual_made_playoffs`
- `actual_won_cup`

from `data/historical/verified/season_YYYY.json`.
