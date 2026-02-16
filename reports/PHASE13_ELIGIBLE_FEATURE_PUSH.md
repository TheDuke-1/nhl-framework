# Phase 13 Eligible Feature Push

Generated: `2026-02-13T04:27:43.871070+00:00`

- Input strict-eligible (Phase 12): `3`
- Phase 12 anchor mode: `feasible_prefilter_fallback`
- Total candidates: `13`
- Core evaluated: `11`
- High-confidence checked: `8`
- Positive-ratio prefilter pass: `11`
- Adaptive frontier fallback: `False`
- Best raw edge: `baseline` (0.022348955050053687)
- Best eligible: `None` (None)
- Closest-to-goal: `e01-anchor`
- Closest feasible: `e01-anchor`
- Undeniable candidates: `0`
- Recommendation: `BLOCKED_BY_POSITIVE_RATIO_FLOOR`

## Candidate Board

| Candidate | Source | Tweak | Edge | CI Low | Pos Ratio | Prefilter | Goal Gap | Top1 | Top5 | F1 | Avg Rank | Hard Gates | Strict Non-Reg | Eligible |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|---|
| baseline | baseline | none | 0.0163 | 0.0086 | 0.900 | True | 0.0637 | 40.0 | 60.0 | 0.974 | 4.60 | True | True | False |
| e03-anchor | anchor3-d0.09-b2.00-m0.90-w0.05-0.00-0.95 | anchor | 0.0197 | 0.0108 | 0.900 | True | 0.0603 | 41.7 | 58.3 | 0.973 | 4.67 | True | False | False |
| e02-anchor | anchor3-d0.09-b1.85-m0.80-w0.05-0.00-0.95 | anchor | 0.0177 | 0.0065 | 0.800 | True | 0.0623 | 41.7 | 58.3 | 0.973 | 4.75 | True | False | False |
| e01-stability | anchor3-d0.09-b2.00-m0.90-w0.07-0.00-0.93 | stability | 0.0190 | 0.0092 | 0.900 | True | 0.0610 | 41.7 | 58.3 | 0.973 | 4.75 | True | False | False |
| e01-anchor | anchor3-d0.09-b2.00-m0.90-w0.07-0.00-0.93 | anchor | 0.0216 | 0.0122 | 0.900 | True | 0.0584 | 41.7 | 58.3 | 0.973 | 4.67 | True | False | False |
| e03-stability | anchor3-d0.09-b2.00-m0.90-w0.05-0.00-0.95 | stability | 0.0213 | 0.0122 | 0.900 | True | 0.0587 | 41.7 | 58.3 | 0.973 | 4.75 | True | False | False |
| e03-calibrated | anchor3-d0.09-b2.00-m0.90-w0.05-0.00-0.95 | calibrated | 0.0171 | 0.0026 | 0.800 | True | 0.0629 | 40.0 | 60.0 | 0.974 | 4.90 | True | False | False |
| e02-stability | anchor3-d0.09-b1.85-m0.80-w0.05-0.00-0.95 | stability | 0.0141 | -0.0021 | 0.600 | True | 0.0680 | 41.7 | 58.3 | 0.973 | 4.75 | True | False | False |
| e03-diversified | anchor3-d0.09-b2.00-m0.90-w0.05-0.00-0.95 | diversified | 0.0123 | -0.0005 | 0.800 | True | 0.0682 | 41.7 | 58.3 | 0.973 | 4.67 | True | False | False |
| e01-calibrated | anchor3-d0.09-b2.00-m0.90-w0.07-0.00-0.93 | calibrated | 0.0115 | -0.0014 | 0.600 | True | 0.0699 | 40.0 | 60.0 | 0.974 | 4.90 | True | False | False |
| e01-diversified | anchor3-d0.09-b2.00-m0.90-w0.07-0.00-0.93 | diversified | 0.0103 | -0.0051 | 0.700 | True | 0.0747 | 41.7 | 58.3 | 0.973 | 4.75 | True | False | False |
| e02-calibrated | anchor3-d0.09-b1.85-m0.80-w0.05-0.00-0.95 | calibrated | 0.0072 | -0.0122 | 0.500 | False | 0.1851 | N/A | N/A | N/A | N/A | None | None | False |
| e02-diversified | anchor3-d0.09-b1.85-m0.80-w0.05-0.00-0.95 | diversified | 0.0060 | -0.0135 | 0.400 | False | 0.2875 | N/A | N/A | N/A | N/A | None | None | False |
