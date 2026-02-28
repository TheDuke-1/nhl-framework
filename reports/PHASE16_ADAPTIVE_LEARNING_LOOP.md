# Phase 16 Adaptive Learning Loop

Generated: `2026-02-18T13:58:21.894715+00:00`
- Target tier: `strong` (`0.0300`)
- Historical samples: `87`
- Stage1 candidates: `11`
- Stage2 core-evaluated: `6`
- Baseline edge: `0.0184`
- Best raw edge: `anchor-01` (`0.020691027810476024`)
- Best eligible: `anchor-01` (`0.020691027810476024`)
- Target met: `False`
- Recommendation: `ITERATE_WITH_BLOCKERS`
- Deploy status: `False` (no promotion; target-tier and strict eligibility not both satisfied)
- Strict promotion gate status: `SKIPPED`

## Blockers

- Best raw edge is 0.0207; strong-tier target requires 0.0300.

## Candidate Snapshot

| Candidate | Edge | Gap To Target | Eligible | Core Eval | Positive-Ratio Prefilter |
|---|---:|---:|---|---|---|
| anchor-01 | 0.0207 | 0.0093 | True | True | True |
| anchor-03 | 0.0206 | 0.0094 | True | True | True |
| anchor-05 | 0.0206 | 0.0094 | True | True | True |
| anchor-06 | 0.0205 | 0.0095 | True | True | True |
| explore-15 | 0.0203 | 0.0097 | True | True | True |
| anchor-01-diversified | 0.0202 | 0.0098 | False | False | True |
| anchor-04-diversified | 0.0201 | 0.0099 | False | False | True |
| anchor-06-diversified | 0.0201 | 0.0099 | False | False | True |
| anchor-01-stability | 0.0201 | 0.0099 | False | False | True |
| anchor-06-stability | 0.0199 | 0.0101 | False | False | True |
| baseline | 0.0184 | 0.0116 | False | True | True |
