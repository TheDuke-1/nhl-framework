# Feature Test Matrix

Generated: `2026-02-07T21:04:41.022607+00:00`

## Baseline

- Cup Top-1: 16.7%
- Cup Top-5: 58.3%
- Avg Winner Rank: 7.67
- Playoff F1: 0.905

## Decision Table

| Feature | Add-One Top1 | LOO Top1 | Recommendation |
|---|---:|---:|---|
| goal_differential_rate | 16.7 | 16.7 | keep_or_increase |
| cf_pct | 8.3 | 16.7 | reduce_but_keep |
| hdcf_pct | 0.0 | 16.7 | reduce_or_remove |
| xgf_pct | 8.3 | 16.7 | reduce_or_remove |
| goaltending_quality | 0.0 | 16.7 | keep_or_increase |
| pp_pct | 0.0 | 25.0 | keep_or_increase |
| pk_pct | 0.0 | 16.7 | reduce_or_remove |
| road_performance | 0.0 | 25.0 | reduce_or_remove |
| sustainability | 0.0 | 33.3 | reduce_or_remove |
| true_xgf_rate | 25.0 | 16.7 | keep_or_increase |
| true_xga_rate | 25.0 | 16.7 | keep_or_increase |
| xg_diff_rate | 16.7 | 16.7 | keep_or_increase |
| offense_rate | 16.7 | 16.7 | reduce_but_keep |
| defense_rate | 16.7 | 16.7 | keep_or_increase |
| save_pct | 0.0 | 16.7 | reduce_or_remove |
| discipline_proxy_special_teams | 0.0 | 16.7 | reduce_or_remove |
| playoff_experience | 8.3 | 16.7 | reduce_or_remove |
| dynasty_score | 8.3 | 16.7 | reduce_or_remove |

## Top Interactions

| Pair | Cup Top1 | Cup Top5 | Winner Rank | Playoff F1 |
|---|---:|---:|---:|---:|
| goaltending_quality + true_xgf_rate | 33.3 | 50.0 | 5.92 | 0.869 |
| true_xga_rate + save_pct | 33.3 | 50.0 | 6.33 | 0.849 |
| goaltending_quality + true_xga_rate | 33.3 | 50.0 | 6.75 | 0.839 |
| xg_diff_rate + save_pct | 25.0 | 66.7 | 5.42 | 0.884 |
| goal_differential_rate + true_xga_rate | 25.0 | 58.3 | 5.58 | 0.905 |
| true_xgf_rate + save_pct | 25.0 | 58.3 | 5.58 | 0.879 |
| goal_differential_rate + hdcf_pct | 25.0 | 50.0 | 5.67 | 0.921 |
| hdcf_pct + true_xga_rate | 25.0 | 50.0 | 7.42 | 0.839 |
| goaltending_quality + xg_diff_rate | 16.7 | 66.7 | 5.42 | 0.890 |
| goal_differential_rate + xgf_pct | 16.7 | 66.7 | 6.08 | 0.921 |
| hdcf_pct + xg_diff_rate | 16.7 | 66.7 | 6.33 | 0.890 |
| goal_differential_rate + goaltending_quality | 16.7 | 58.3 | 5.08 | 0.916 |
| goal_differential_rate + true_xgf_rate | 16.7 | 58.3 | 5.33 | 0.916 |
| goal_differential_rate + xg_diff_rate | 16.7 | 58.3 | 5.50 | 0.921 |
| true_xgf_rate + xg_diff_rate | 16.7 | 58.3 | 6.42 | 0.869 |

## Unavailable Backlog Datapoints

- goalie_usage_quality_starter_load
- goalie_backup_dropoff
- injury_adjusted_strength
- score_state_adjusted_5v5_close_game
- schedule_travel_rest_load
- discipline_taken_drawn_split
- trade_deadline_roster_delta
- playoff_style_netfront_rush_forecheck
- coach_system_continuity
