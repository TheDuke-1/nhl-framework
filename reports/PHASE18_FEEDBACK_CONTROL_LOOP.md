# Phase 18 Feedback Control Loop

Generated: `2026-02-28T03:00:55.159541+00:00`
- Control mode: `ESCALATE_EXPLORATION`
- Target edge: `0.03`
- Phase16 best edge: `0.020691027810476024`
- Strong-tier gap: `0.009308972189523975`
- Phase17 downside min-season-edge delta: `0.0`
- Stagnation streak: `2`
- Downside regression streak: `0`
- Execute recommended loop this run: `False`

## Recommended Commands

- Phase16: `PHASE16_CANDIDATE_BUDGET=32 PHASE16_HIGH_CONF_BOOTSTRAP=1600 PHASE16_MAX_STAGE2_EVALS=8 PHASE16_SHORTLIST_N=5 PHASE16_STAGE1_TOP_N=16 PHASE16_VEGAS_BOOTSTRAP=420 python3 scripts/run_phase16_adaptive_learning_loop.py`
- Phase17: `PHASE17_CANDIDATE_BUDGET=24 PHASE17_HIGH_CONF_BOOTSTRAP=1200 PHASE17_MAX_EDGE_DROP_VS_BASELINE=0.0008 PHASE17_MAX_NEGATIVE_SEASON_RATIO=0.3 PHASE17_MIN_POSITIVE_RATIO=0.85 PHASE17_MIN_SEASON_EDGE_FLOOR=-0.03 PHASE17_SHORTLIST_N=4 PHASE17_STAGE2_EVALS=5 PHASE17_VEGAS_BOOTSTRAP=320 python3 scripts/run_phase17_downside_stability_lane.py`

## Blockers

- Strong-tier gap remains 0.0093 (target 0.0300).
- Edge stagnation streak is 2 loops.

## Next Actions

- `Model Lead` (P0): Execute feedback-tuned phase16 lane: `PHASE16_CANDIDATE_BUDGET=32 PHASE16_HIGH_CONF_BOOTSTRAP=1600 PHASE16_MAX_STAGE2_EVALS=8 PHASE16_SHORTLIST_N=5 PHASE16_STAGE1_TOP_N=16 PHASE16_VEGAS_BOOTSTRAP=420 python3 scripts/run_phase16_adaptive_learning_loop.py`
- `Quant Engineer` (P0): Execute feedback-tuned phase17 lane: `PHASE17_CANDIDATE_BUDGET=24 PHASE17_HIGH_CONF_BOOTSTRAP=1200 PHASE17_MAX_EDGE_DROP_VS_BASELINE=0.0008 PHASE17_MAX_NEGATIVE_SEASON_RATIO=0.3 PHASE17_MIN_POSITIVE_RATIO=0.85 PHASE17_MIN_SEASON_EDGE_FLOOR=-0.03 PHASE17_SHORTLIST_N=4 PHASE17_STAGE2_EVALS=5 PHASE17_VEGAS_BOOTSTRAP=320 python3 scripts/run_phase17_downside_stability_lane.py`
- `Program Lead` (P1): Control mode is `ESCALATE_EXPLORATION`; keep strict non-regression and promotion safety unchanged.
- `Prevention Loop` (P1): Convert top blocker into hard control: Strong-tier gap remains 0.0093 (target 0.0300).
