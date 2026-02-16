# Phase 2 Feature Hardening

Generated: `2026-02-07T21:06:14.739520+00:00`

## Baseline

- Cup Top-1: 16.7%
- Cup Top-5: 58.3%
- Avg Winner Rank: 7.67
- Playoff F1: 0.905

## Final Keep / Reduce / Remove / Add Table

| Feature | Decision | Confidence | Top1 Importance | Top5 Importance | Playoff Importance | Era Stable |
|---|---|---|---:|---:|---:|---|
| true_xgf_rate | keep_reduce_weight | medium | 4.15 | 0.00 | 0.00 | False |
| true_xga_rate | keep_reduce_weight | medium | 4.15 | 0.00 | 0.00 | False |
| xg_diff_rate | keep_reduce_weight | medium | 0.00 | 4.20 | 0.00 | False |
| goal_differential_rate | keep_reduce_weight | medium | 0.00 | 0.00 | 0.55 | False |
| offense_rate | reduce_or_remove | low | 0.00 | 0.00 | 0.00 | False |
| discipline_proxy_special_teams | reduce_or_remove | low | 0.00 | 0.00 | 0.00 | True |
| pk_pct | reduce_or_remove | low | 0.00 | 0.00 | 0.00 | False |
| sustainability | reduce_or_remove | low | 0.00 | 0.00 | 0.00 | False |
| defense_rate | keep_reduce_weight | medium | 0.00 | 0.00 | 0.00 | False |
| hdcf_pct | keep_reduce_weight | medium | 0.00 | 0.00 | 0.00 | False |
| road_performance | reduce_or_remove | low | 0.00 | 0.00 | 0.00 | False |
| goaltending_quality | keep_reduce_weight | medium | 0.00 | 0.00 | 0.00 | False |
| save_pct | keep_reduce_weight | medium | 0.00 | 0.00 | 0.00 | False |
| playoff_experience | reduce_or_remove | low | 0.00 | 0.00 | 0.00 | False |
| dynasty_score | reduce_or_remove | low | 0.00 | 0.00 | 0.00 | False |
| cf_pct | reduce_or_remove | low | 0.00 | 0.00 | 0.00 | False |
| xgf_pct | reduce_or_remove | low | 0.00 | 0.00 | 0.00 | False |
| pp_pct | reduce_or_remove | low | 0.00 | 0.00 | 0.00 | False |

## Top Interaction Pairs

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

## Backlog Datapoints Still Missing

- goalie_usage_quality_starter_load
- goalie_backup_dropoff
- injury_adjusted_strength
- score_state_adjusted_5v5_close_game
- schedule_travel_rest_load
- discipline_taken_drawn_split
- trade_deadline_roster_delta
- playoff_style_netfront_rush_forecheck
- coach_system_continuity
