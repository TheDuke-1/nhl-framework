# Phase 10 A/B Top-1 Recovery

Generated: `2026-02-19T02:34:00.108970+00:00`
- Active profile (unchanged): `phase9-cup-edge-2026-02-13`
- Selected A/B candidate: `experimental-edge-mc100-blend0.90`
- Decision reason: selected highest Top-1 among edge-improved, strict-non-regression candidates

## Candidate Results

| Candidate | Top1 | Top5 | Avg Rank | F1 | Cup Edge | CI Low | Pos Ratio | Prefilter | Hard Gates | Strict Non-Reg | A/B Eligible |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| baseline | 40.0 | 60.0 | 4.60 | 0.974 | 0.0184 | 0.0069 | 0.900 | True | True | True | False |
| experimental-edge-mc100 | 10.0 | 40.0 | 6.90 | 0.974 | -0.0376 | -0.0923 | 0.400 | False | False | False | False |
| recovery-mc85 | 40.0 | 60.0 | 4.60 | 0.974 | 0.0186 | 0.0063 | 0.900 | True | True | True | True |
| recovery-mc80 | 40.0 | 60.0 | 4.60 | 0.974 | 0.0186 | 0.0069 | 0.900 | True | True | True | True |
| recovery-mc75 | 40.0 | 60.0 | 4.60 | 0.974 | 0.0188 | 0.0073 | 0.900 | True | True | True | True |
| experimental-edge-mc100-blend0.00 | 10.0 | 40.0 | 6.90 | 0.974 | -0.0376 | -0.0923 | 0.400 | False | False | False | False |
| experimental-edge-mc100-blend0.35 | 30.0 | 50.0 | 5.00 | 0.974 | -0.0155 | -0.0518 | 0.400 | False | True | False | False |
| experimental-edge-mc100-blend0.90 | 40.0 | 60.0 | 4.60 | 0.974 | 0.0191 | 0.0063 | 0.900 | True | True | True | True |

## Profile Artifacts

- Baseline profile: `/Users/matthewdukovich/Desktop/NHL Playoff Project/data/model_profiles/baseline_profile.json`
- Experimental edge profile: `/Users/matthewdukovich/Desktop/NHL Playoff Project/data/model_profiles/experimental_edge_profile.json`
- Recovery candidate profile: `/Users/matthewdukovich/Desktop/NHL Playoff Project/data/model_profiles/ab_recovery_candidate_profile.json`

Deployment mode: `NO_AUTODEPLOY_AB_ONLY`
