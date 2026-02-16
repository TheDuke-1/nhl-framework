# DESIGN DECISIONS: NHL Playoff Prediction Framework

> **What This Is:** A log of all design decisions, approvals, rejections, and extracted principles. This is Claude's "design memory."

> **How It's Used:** 
> - Claude references this to understand your taste
> - Used for autonomy progression tracking
> - Captures visual evidence and reasoning

> **How It's Updated:** Automatically during design reviews and when you give feedback

---

## Autonomy Tracking

### Overall Status

| Area | Approval Rate | Level | Notes |
|------|---------------|-------|-------|
| Color Usage | _/_ | [CHECKPOINT] | |
| Typography | _/_ | [CHECKPOINT] | |
| Layout | _/_ | [CHECKPOINT] | |
| Components | _/_ | [CHECKPOINT] | |
| Overall UI | _/_ | [CHECKPOINT] | |

### Level Definitions

- **CHECKPOINT (0-5 approvals):** Show milestones, wait for approval
- **FINAL_APPROVAL (5-10 approvals):** Work independently, show final result  
- **AUTONOMOUS (10+ approvals, 90%+ rate):** Ship confidently, escalate when uncertain

---

## Extracted Principles

> Patterns discovered from your feedback

### Principle: [Name]

**Discovered:** [date]
**Source:** [Which decision/feedback]
**Rule:** [The principle in actionable form]

Example:
```
### Principle: Depth Over Flat

**Discovered:** 2025-01-15
**Source:** Rejected flat button design
**Rule:** Always use subtle shadows on interactive elements. 
        Flat design feels "cheap" to this user.
```

---

## Decision Log

### [Date] — [View/Component Name]

**Type:** [New View / Modification / Component]
**Agent:** [UI Designer / Creative Director / etc.]
**Autonomy Level:** [CHECKPOINT / FINAL_APPROVAL / AUTONOMOUS]

**What Was Built:**
[Description of what was created]

**User Verdict:** ✅ APPROVED / ❌ REJECTED / 🔄 REVISION REQUESTED

**User Feedback:**
> "[Exact words from user]"

**Extracted Learning:**
- [What this teaches about user's preferences]

**Design System Impact:**
- [ ] Color update needed
- [ ] Typography update needed
- [ ] Component style update needed
- [ ] Anti-pattern identified
- [ ] No updates needed

**Screenshots:**
- Before: [link/reference]
- After: [link/reference]

---

## Approval History

### Approved Designs

| Date | View/Component | Key Feedback | Principle Extracted |
|------|----------------|--------------|---------------------|
| [date] | [name] | "[feedback]" | [principle] |

### Rejected Designs

| Date | View/Component | Rejection Reason | Fix Applied |
|------|----------------|------------------|-------------|
| [date] | [name] | "[reason]" | [what was changed] |

### Revision Requests

| Date | View/Component | Revision Requested | Final Outcome |
|------|----------------|-------------------|---------------|
| [date] | [name] | "[request]" | [approved/rejected] |

---

## Reference Comparisons

> When user compares to other apps

### Positive Comparisons ("Like this")

| Date | Our Design | Reference App | What User Liked |
|------|------------|---------------|-----------------|
| [date] | [view] | [app name] | "[specific element]" |

### Negative Comparisons ("Not like this")

| Date | Our Design | Reference App | What User Disliked |
|------|------------|---------------|-------------------|
| [date] | [view] | [app name] | "[specific element]" |

---

## Visual Evidence

### Baseline Screenshots

> Approved designs that represent the standard

| View | Status | Screenshot | Approved Date |
|------|--------|------------|---------------|
| [view name] | BASELINE | [link] | [date] |

### Anti-Pattern Examples

> Designs that were rejected — what NOT to do

| Example | Why Rejected | Screenshot |
|---------|--------------|------------|
| [description] | "[reason]" | [link] |

---

## Design Interview Highlights

> Key quotes and preferences from `/design-interview`

### Visual Identity

> "[Quote about overall feel]"

### Color Preferences

> "[Quote about colors]"

### Typography Preferences

> "[Quote about fonts/text]"

### What to Avoid

> "[Quote about what they don't want]"

---

## Trend Analysis

### Improving Areas

- [Area where approval rate is increasing]

### Struggling Areas

- [Area where rejections are common]

### Recommendations

- [What to focus on based on patterns]

---

## Notes for Agents

### For UI Designer

- User prefers: [key preferences]
- User dislikes: [key dislikes]
- Safe choices: [things that consistently get approved]
- Risk areas: [things that often get rejected]

### For Creative Director

- Brand alignment priorities: [what matters most]
- Consistency gaps: [areas needing attention]
- Evolution direction: [how style is evolving]

---

*This document is updated automatically during design workflows. Manual additions are welcome for capturing additional context.*

---

### 2026-02-08 — Dashboard Interaction and Responsiveness Hardening

**Type:** Modification  
**Agent:** `ui-designer` + `visual-qa`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Built:**
- Reworked header freshness interaction to use an accessible button and stable popover state handling.
- Aligned tab navigation markup/CSS for consistent horizontal mobile behavior.
- Added missing footer/value flag style hooks so production HTML and CSS contracts are in sync.

**Reasoning:**
The dashboard had interaction inconsistencies (first-click popover failure) and class/markup drift that reduced polish on smaller viewports.

**Result:**
Interaction reliability improved, mobile tab behavior is cleaner, and visual contract mismatches were removed.

### 2026-02-08 — Keep Baseline Profile After Phase 3B Grid

**Type:** Modification  
**Agent:** `superhuman-builder-verifier`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Ran `scripts/run_phase3b_profile_grid.py` across ensemble and decay candidates.
- Kept baseline profile `phase3-optimized-2026-02-08` as active profile.

**Reasoning:**
Every candidate that passed hard gates tied baseline quality score; one decay candidate regressed core non-regression checks. No candidate produced a strict improvement worth deployment.

**Result:**
Model remained on the strongest known profile under current constraints, avoiding a change that would not move benchmarks forward.

### 2026-02-08 — Cup-Vegas "Undeniable" Target Adopted as Top-Level Goal

**Type:** Modification  
**Agent:** `superhuman-project-operator` + `superhuman-review-improver`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Locked the primary market goal to: at least `8%` relative Cup Brier improvement vs Vegas, with season-level CI low above zero and sustained positive seasons.
- Added this goal to evaluation contract and benchmark outputs as a first-class gate.
- Enforced strict release-cycle failure when the goal is not met.

**Reasoning:**
Core model quality can look strong while still missing the market-proof threshold; a hard target prevents false promotion.

**Result:**
Release flow now reports explicit PASS/FAIL against the Cup-Vegas undeniable bar, and current state is transparently marked as FAIL.

### 2026-02-08 — Keep Baseline Profile After Phase 9 Cup-Edge Search

**Type:** Modification  
**Agent:** `superhuman-builder-verifier`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Added and ran `scripts/run_phase9_cup_edge_optimization.py` with strict walk-forward Cup-vs-Vegas objective.
- Kept baseline profile active (`data/model_profile.json` unchanged) because no candidate passed both hard gates and non-regression while improving Cup edge.

**Reasoning:**
Several candidates improved raw Cup-vs-Vegas edge numerically, but each violated at least one deployment constraint (Top-5 floor or non-regression guardrail). Promoting those would weaken contract integrity.

**Result:**
Profile stability preserved; Phase 9 now gives repeatable, auditable evidence that current search space is insufficient to clear the hard target.

### 2026-02-08 — Add Phase 8-14 Deterministic Orchestration

**Type:** Modification  
**Agent:** `superhuman-project-operator`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Added `scripts/run_phases_8_to_14.py` to execute Phase 8 through Phase 14 in order and emit a consolidated PASS/FAIL report.
- Added Phase 8 truth-lock script with validation + fingerprinting output.

**Reasoning:**
Manual phase execution obscured blockers and made progress tracking inconsistent. A single orchestration path ensures repeatability and clear phase-level failure attribution.

**Result:**
Execution status is now centralized in:
- `reports/phase8_14_execution.json`
- `reports/PHASE8_14_EXECUTION.md`

### 2026-02-08 — Phase 8 Truth Lock Runs Repair Before Validation

**Type:** Modification  
**Agent:** `superhuman-project-operator` + `superhuman-builder-verifier`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Make Phase 8 deterministic and self-healing by running Vegas historical repair before validation and benchmark refresh.

**Reasoning:**
Validation-only truth lock surfaced missing rows repeatedly but did not close the gap. Repair-first execution turns phase failures into actionable data corrections.

**Result:**
Phase 8 now passes with complete 2010-2025 canonical Vegas coverage and full file fingerprint lock.

### 2026-02-08 — Keep Baseline Despite Better Raw Cup Edge Candidate

**Type:** Modification  
**Agent:** `superhuman-builder-verifier`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Ran wide Phase 9 experiment and kept baseline profile active.
- Did not deploy top raw-edge candidate (`w-0.0-0.0-1.0`).

**Reasoning:**
Although raw Cup-vs-Vegas edge improved materially, candidate failed non-regression constraints (notably Top-1 accuracy drop) and still did not deliver CI-low-above-zero.

**Result:**
Deployment contract integrity preserved; experiment remains report-only (`DISABLED_EXPERIMENT_ONLY`).

### 2026-02-08 — Warning Suppression Is Localized To Training Paths

**Type:** Modification  
**Agent:** `superhuman-builder-verifier`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Applied local warning suppression around sklearn/scipy fit/predict calls in `superhuman/models.py` rather than disabling warnings globally.

**Reasoning:**
Strict runtime-warning mode is required for release flow, but environment-specific BLAS/scipy warnings were noisy and non-actionable. Localized suppression keeps strict mode useful while avoiding false pipeline aborts.

**Result:**
Strict verification now fails for true contract reasons (Cup-vs-Vegas gate), not incidental runtime warning exceptions.

### 2026-02-08 — Introduce Separate A/B Profile Track (No Auto-Deploy)

**Type:** Modification  
**Agent:** `superhuman-project-operator` + `superhuman-builder-verifier`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Add a dedicated Phase 10 A/B runner (`scripts/run_phase10_ab_top1_recovery.py`) that evaluates baseline vs experimental edge profiles and writes profile artifacts without changing active production profile.

**Reasoning:**
The edge-optimized profile improves Cup-vs-Vegas numerically but still violates strict non-regression; it should be available for controlled iteration, not deployment.

**Result:**
- A/B artifact profiles now exist under `data/model_profiles/`.
- Production profile remains unchanged unless a future candidate satisfies strict deployment gates.

### 2026-02-08 — New Cup Signals Are Cup-Only Features

**Type:** Modification  
**Agent:** `superhuman-builder-verifier`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Added three new Cup signals:
  - series history
  - market movement
  - goalie/injury impact
- Kept them out of playoff/strength models and reserved them for Cup-focused learning paths.

**Reasoning:**
When these signals were fed into all model paths, core playoff gates regressed. Cup-only routing preserves core stability while still expanding Cup-signal search space.

**Result:**
Core gates returned to passing while the new signals remain integrated in the model feature system.

### 2026-02-08 — Repair 2024 Advanced Overrides To Full Team Coverage

**Type:** Modification  
**Agent:** `superhuman-builder-verifier`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Backfilled 2024 advanced override file to full-team coverage using proxy fill policy.

**Reasoning:**
Sparse 2024 coverage was reducing override acceptance and undercutting historical consistency.

**Result:**
2024 override file now includes all 32 teams and passes accepted-coverage thresholds.

### 2026-02-09 — Add Formal Superhuman Team Cycle Runner

**Type:** Modification  
**Agent:** `superhuman-project-operator` + `superhuman-review-improver`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Introduce an explicit owner-mapped cycle runner (`scripts/run_superhuman_team_cycle.py`) and collaboration plan doc for recurring execution.

**Reasoning:**
The project needed a reproducible mechanism to coordinate discovery, build, review, and verification with a single consolidated PASS/FAIL outcome and clear next-owner actions.

**Result:**
- Team cycle now emits a unified report with:
  - blocking failures
  - benchmark/phase snapshots
  - owner-specific next actions
- Release status remains blocked by Cup-vs-Vegas gate, but decision traceability and team handoff quality improved.

### 2026-02-10 — Adopt Issue-Squad Team Structure with Portable Skill Pack

**Type:** Process/Framework Modification  
**Agent:** `superhuman-project-operator` + `framework-improver`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Shift from generic team roster to issue-specific squad ownership.
- Require multi-agent assignment per issue with explicit acceptance criteria and dependencies.
- Publish a reusable cross-project skill pack to make this execution model portable.

**Reasoning:**
Issue discovery alone does not guarantee resolution quality. Explicit squad ownership plus reusable skills improves closure speed, prevention quality, and future-project transfer.

**Result:**
- Team charter updated (`SUPERHUMAN_TEAM.md`).
- Issue board created (`reports/SUPERHUMAN_ISSUE_SWARM_BOARD.md`).
- Reusable skills created in `.codex/skills/*` and cataloged.

### 2026-02-10 — Align “Phase 8-14” Orchestration With True Phase Scope

**Type:** Modification  
**Agent:** `superhuman-project-operator`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Reworked `scripts/run_phases_8_to_14.py` to execute explicit phase steps for 8, 9, 10, 11, 12, 13, and release closure checks in phase 14.
- Added timeout controls to avoid indefinite orchestration hangs.

**Reasoning:**
An orchestration label that does not match executed phases creates false progress confidence and weakens release governance.

**Result:**
Phase execution now has traceable scope fidelity and bounded runtime behavior.

### 2026-02-10 — Keep Hard Positive-Ratio Gate But Add Adaptive Frontier Evaluation

**Type:** Modification  
**Agent:** `superhuman-builder-verifier` + `superhuman-review-improver`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Preserved strict positive-season-ratio gate for eligibility in Phase 13.
- Added adaptive frontier core/high-confidence evaluation when the prefilter has zero feasible candidates.

**Reasoning:**
Strict gating protects deployment quality, but zero-feasible batches without additional diagnostics prevent learning and can stall root-cause discovery.

**Result:**
Phase 13 now balances deployment safety with measurable exploratory evidence.

### 2026-02-10 — Promote Mission Control To Executive Trust Surface

**Type:** Product/UX Modification  
**Agent:** `ux-designer` + `design-system`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Upgraded visual system to a premium enterprise style (typography, hierarchy, motion, and branded layout).
- Added mission-level trust primitives: Data Trust Panel and Release Decision Trace.

**Reasoning:**
A model platform with release-critical decisions needs explicit operational evidence and polished information hierarchy to support executive confidence.

**Result:**
Dashboard now communicates release status, risk, and freshness evidence in a decision-ready form.

### 2026-02-13 — Separate Model Quality From Release Readiness in Dashboard UX

**Type:** Product/UX + Governance Alignment  
**Agent:** `superhuman-dashboard-trust-polisher`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Mission Control and Performance now present separate states for model quality and release readiness.
- Added explicit “Why Blocked Right Now” panel from release artifacts and grade-cap reasons.

**Reasoning:**
A single blended status can hide whether failures are model-goal issues, release process failures, or both.

**Result:**
Operators can distinguish “model is healthy but release is blocked” from “model quality itself is degraded.”

### 2026-02-13 — Enforce Timeout Floors for Heavy Phase Commands

**Type:** Reliability/Operations Modification  
**Agent:** `superhuman-release-readiness-sheriff`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Added minimum timeout floors and structured timeout policy reporting for phase runners.
- Added per-command timeout and duration details in release artifacts.

**Reasoning:**
Misconfigured short env timeouts produce false negative release outcomes and noisy decision cycles.

**Result:**
Timeout behavior is now explicit, bounded, and auditable in output artifacts.

### 2026-02-13 — Productize Targeted Operating Skills for Ongoing Improvement

**Type:** Framework/Process Productization  
**Agent:** `superhuman-skill-productizer`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
Added three project skills:
- `superhuman-release-readiness-sheriff`
- `superhuman-dashboard-trust-polisher`
- `superhuman-edge-goal-loop`

**Reasoning:**
The team needed reusable, task-specific operating procedures for release truth, trust UX, and edge-goal iteration.

**Result:**
These workflows are now codified in `.codex/skills` and mapped in `TEAM_SKILLS.md`.

### 2026-02-13 — Make Strict Vegas Evaluation Deterministic by Contract

**Type:** Reliability + Quality Gate Integrity  
**Agent:** `superhuman-quality-gate-architect`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Seed strict Vegas diagnostics per held-out season with a stable seed strategy.
- Expose seed configuration in benchmark/performance verification surfaces.

**Reasoning:**
Outcome gates must be reproducible. Stochastic diagnostics created apparent regression/improvement noise with no code or data changes.

**Result:**
Cup-vs-Vegas contract evidence is stable across repeated runs for identical inputs.

### 2026-02-13 — Explicitly Skip Underpowered Early OOF Windows in Strict Backtests

**Type:** Reliability + Operational Clarity  
**Agent:** `superhuman-release-readiness-sheriff`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Added an explicit strict OOF history threshold skip in walk-forward backtest generation.
- Added structured `skippedSplits` reasons in walk-forward audit artifacts.

**Reasoning:**
Early windows with insufficient historical seasons cannot satisfy strict OOF Cup calibration requirements; retrying them is expensive noise.

**Result:**
Backtest artifacts now cleanly separate feasible evaluated splits from intentionally skipped underpowered windows.

### 2026-02-15 — Replace Single 8% Cup Gate With Tiered Release/Strong/Stretch/Moonshot Targets

**Type:** Quality Gate Strategy Realignment  
**Agent:** `superhuman-quality-gate-architect` + `superhuman-project-operator`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Set Cup-vs-Vegas edge tiers:
  - release floor `>= 0.015`
  - strong `>= 0.030`
  - stretch `>= 0.050`
  - moonshot `>= 0.080`
- Preserve `goal_met` as backward-compatible release-floor gate flag.
- Extend benchmark/betting reports with tier statuses (`goal_tier`, `strong_met`, `stretch_met`, `moonshot_met`).

**Reasoning:**
Efficient market edges should be governed by realistic production bars plus explicit stretch goals; a single moonshot threshold obscures useful progress and causes avoidable release deadlocks.

**Result:**
Contracts now support both pragmatic deployment decisions and ambitious optimization tracking in one coherent framework.

### 2026-02-15 — Require Strong Tier for Phase 9 Profile Promotion

**Type:** Promotion Safety / Quality Gate Coupling  
**Agent:** `superhuman-quality-gate-architect` + `superhuman-project-operator`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- Keep release eligibility tied to release-floor gate.
- Raise Phase 9 profile promotion requirement to `relative_brier_improvement_strong` (`>= 0.030`).
- Record promotion gate outcome and threshold in Phase 9 JSON/markdown decision artifacts.

**Reasoning:**
Release readiness and profile promotion solve different risks. Release can proceed on realistic floor evidence, but automatic profile replacement should require stronger edge confidence to prevent drift and unnecessary churn.

**Result:**
Promotion logic now enforces stronger evidence than release-floor gating, improving stability of model-profile evolution.

### 2026-02-15 — Separate Release Truth Gates From Benchmark Refresh Volatility

**Type:** Release Determinism + Operational Safety  
**Agent:** `superhuman-release-readiness-sheriff` + `superhuman-quality-gate-architect`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
- In Phase 7, keep benchmark contract verification as a blocking gate.
- Move benchmark refresh execution to non-blocking observability output in the same report.
- Add explicit data-warning policy metadata and advisories to Phase 7 artifacts.

**Reasoning:**
Release truth should depend on deterministic contract checks, not on refresh-time metric jitter or local upstream freshness instability.

**Result:**
Phase 7 now reports stable release truth and still captures refresh evidence for follow-up analysis.

### 2026-02-15 — Add Epsilon to Delta Guardrail Comparisons

**Type:** Numerical Robustness  
**Agent:** `superhuman-quality-gate-architect`  
**Autonomy Level:** FINAL_APPROVAL

**What Was Decided:**
Use an epsilon tolerance in benchmark delta comparisons to avoid false failures from floating-point precision artifacts.

**Reasoning:**
Contract gates should detect meaningful regressions, not machine-precision noise.

**Result:**
Benchmark delta guardrail behavior is now mathematically stable and operationally predictable.
