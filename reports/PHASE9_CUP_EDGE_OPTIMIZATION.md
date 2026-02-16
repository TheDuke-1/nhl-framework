# Phase 9 Cup Edge Optimization

Generated: `2026-02-13T03:33:24.766035+00:00`

- Deployed: `True`
- Selected: `decay-022-boost15`
- Reason: deployed `decay-022-boost15` with improved Cup-vs-Vegas relative edge
- Positive-ratio prefilter pass count: `11`

## Candidate Results

| Candidate | Edge | CI Low | Pos Season Ratio | Prefilter | Hard Gates | Non-Regression | Eligible |
|---|---:|---:|---:|---|---|---|---|
| nn-nocal-w000-000-100 | 0.0234 | 0.0127 | 0.900 | True | True | False | False |
| decay-022-boost15 | 0.0232 | 0.0161 | 1.000 | True | True | True | True |
| nn-nocal-w020-000-080 | 0.0223 | 0.0144 | 1.000 | True | True | False | False |
| nn-nocal-w020-020-060 | 0.0184 | 0.0064 | 0.900 | True | True | False | False |
| nn-nocal-w040-020-040 | 0.0182 | 0.0079 | 0.900 | True | True | False | False |
| decay-008-boost20 | 0.0173 | 0.0079 | 0.900 | True | True | True | True |
| decay-025-boost15 | 0.0170 | 0.0070 | 0.900 | True | None | None | False |
| decay-018-boost20 | 0.0169 | 0.0075 | 0.900 | True | None | None | False |
| nn-cal-w020-020-060 | 0.0169 | 0.0093 | 0.900 | True | None | None | False |
| decay-025-boost20 | 0.0160 | 0.0086 | 0.900 | True | None | None | False |
| baseline | 0.0147 | 0.0063 | 0.900 | True | True | True | True |

## Benchmark Refresh

- Command: `python3 scripts/update_benchmark_metrics.py`
- Status: `PASS`
