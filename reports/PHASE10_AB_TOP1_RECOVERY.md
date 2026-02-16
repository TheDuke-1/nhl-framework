# Phase 10 A/B Top-1 Recovery

Generated: `2026-02-12T03:41:36.544148+00:00`
- Active profile (unchanged): `phase3-optimized-market-prior-v2-2026-02-10`
- Selected A/B candidate: `baseline`
- Decision reason: no edge-improved candidate satisfied strict non-regression

## Candidate Results

| Candidate | Top1 | Top5 | Avg Rank | F1 | Cup Edge | CI Low | Pos Ratio | Prefilter | Hard Gates | Strict Non-Reg | A/B Eligible |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| baseline | 40.0 | 60.0 | 4.60 | 0.974 | 0.0196 | 0.0093 | 0.900 | True | True | True | False |
| experimental-edge-mc100 | 16.7 | 41.7 | 6.25 | 0.973 | -0.0299 | -0.0859 | 0.400 | False | False | False | False |
| recovery-mc85 | 41.7 | 58.3 | 4.67 | 0.973 | 0.0174 | 0.0089 | 0.900 | True | True | False | False |
| recovery-mc80 | 41.7 | 58.3 | 4.67 | 0.973 | 0.0174 | 0.0090 | 0.900 | True | True | False | False |
| recovery-mc75 | 41.7 | 58.3 | 4.67 | 0.973 | 0.0175 | 0.0089 | 0.900 | True | True | False | False |
| experimental-edge-mc100-blend0.00 | 16.7 | 41.7 | 6.25 | 0.973 | -0.0299 | -0.0859 | 0.400 | False | False | False | False |
| experimental-edge-mc100-blend0.35 | 33.3 | 75.0 | 4.08 | 0.973 | -0.0098 | -0.0465 | 0.400 | False | True | False | False |
| experimental-edge-mc100-blend0.90 | 41.7 | 58.3 | 4.67 | 0.973 | 0.0180 | 0.0095 | 0.800 | True | True | False | False |

## Profile Artifacts

- Baseline profile: `/Users/matthewdukovich/Desktop/NHL Playoff Project/data/model_profiles/baseline_profile.json`
- Experimental edge profile: `/Users/matthewdukovich/Desktop/NHL Playoff Project/data/model_profiles/experimental_edge_profile.json`
- Recovery candidate profile: `/Users/matthewdukovich/Desktop/NHL Playoff Project/data/model_profiles/ab_recovery_candidate_profile.json`

Deployment mode: `NO_AUTODEPLOY_AB_ONLY`
