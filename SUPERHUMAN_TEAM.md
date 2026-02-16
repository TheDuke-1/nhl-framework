# NHL Superhuman Team

## Mission
Deliver trustworthy NHL playoff predictions by running a multi-agent, issue-oriented operating model that fixes failures, prevents recurrence, and continuously upgrades team capability.

## Active Mission Teams (2026-02-11)
- Review + Verification Team: `/Users/matthewdukovich/Desktop/NHL Playoff Project/reports/SUPERHUMAN_TEAM_REVIEW_VERIFY_2026-02-11.md`
- Goal-Closure Planning Team: `/Users/matthewdukovich/Desktop/NHL Playoff Project/reports/SUPERHUMAN_TEAM_GOAL_CLOSURE_PLAN_2026-02-11.md`

## Operating Principles
- Outcome-first: prioritize prediction quality and release trust over activity volume.
- Proof-driven: no issue closes without test, metric, and report evidence.
- Learning-required: every resolved issue produces a prevention action and reusable pattern.
- Reuse-by-default: new process improvements are packaged as portable skills.
- Eradication-over-patching: fixes must remove recurrence paths, not only symptoms.

## Core Agent Pool
- `spec-builder`
- `code-reviewer`
- `code-simplifier`
- `test-engineer`
- `verify-app`
- `framework-improver`
- `creative-director`
- `ui-designer`
- `ux-designer`
- `visual-qa`
- `accessibility`
- `motion-designer`
- `design-system`

## Issue Squads

### Squad A - Cup Probability Reliability
- Scope: Cup probability collapse and calibration/normalization integrity.
- Lead: `code-reviewer`
- Support: `test-engineer`, `verify-app`, `code-simplifier`
- Done when:
  - Cup distribution has healthy spread
  - regression tests block probability collapse
  - benchmark impact is reported

### Squad B - Methodology and Evaluation Integrity
- Scope: NHL-rule-consistent evaluation and strict anti-leakage/non-regression standards.
- Lead: `spec-builder`
- Support: `code-reviewer`, `test-engineer`, `framework-improver`
- Done when:
  - playoff-field evaluation mirrors NHL qualification rules
  - release contract reflects true project goal metrics
  - failing goals cannot be masked by aggregate scores

### Squad C - Data and Pipeline Trust
- Scope: stale source handling, source health, and CI gating rigor.
- Lead: `verify-app`
- Support: `test-engineer`, `framework-improver`, `code-reviewer`
- Done when:
  - stale critical sources fail release
  - workflow no longer silently succeeds on core-source failures
  - freshness SLA is visible in reports

### Squad D - Dashboard Trust and UX Accuracy
- Scope: dashboard consistency, freshness transparency, and fallback correctness.
- Lead: `ux-designer`
- Support: `ui-designer`, `visual-qa`, `accessibility`, `design-system`
- Done when:
  - fallback data cannot silently diverge from primary data
  - freshness metadata is source-specific and visible
  - trust messaging accurately reflects release and benchmark state

### Squad E - Skill and Framework Productization
- Scope: convert fixes into reusable, future-project Superhuman skills.
- Lead: `framework-improver`
- Support: `spec-builder`, `code-simplifier`, `test-engineer`
- Done when:
  - new reusable skills are documented and versioned
  - each skill includes adaptation guidance for other projects
  - skill usage is mapped to common failure scenarios

### Squad F - Prevention and Recurrence Eradication
- Scope: ensure each fix ships with durable controls that prevent repeat failures.
- Lead: `framework-improver`
- Support: `superhuman-prevention-loop`, `test-engineer`, `verify-app`
- Done when:
  - each resolved issue has regression tests + gate enforcement
  - release/report/dashboard truth cannot diverge
  - prevention controls are tracked with owners and verification commands

## Execution Loop
1. Intake: rank issues by user impact and risk.
2. Assign: map each issue to a squad with a single accountable lead.
3. Build: implement minimal viable fix with explicit acceptance criteria.
4. Verify: run tests, data validation, and benchmark/release gates.
5. Review: run code, UX, and trust audits for regression risk.
6. Learn: capture what failed, why it failed, and how prevention is enforced.
7. Productize: promote durable workflows into reusable skills.

## Learning and Prevention Contract
Every resolved issue must include:
- root cause statement
- detection gap
- prevention control (test/gate/process)
- owner and verification step
- reusable skill/pattern candidate

## Canonical Verification Gates
- `python3 -m pytest -q`
- `python3 scripts/validate_data.py --strict`
- `python3 -W error::RuntimeWarning scripts/verify_model_performance.py --require-vegas-edge --require-cup-vegas-goal`
- `python3 scripts/run_phase7_release_cycle.py`

## Source of Truth Files
- Team charter: `/Users/matthewdukovich/Desktop/NHL Playoff Project/SUPERHUMAN_TEAM.md`
- Issue swarm board: `/Users/matthewdukovich/Desktop/NHL Playoff Project/reports/SUPERHUMAN_ISSUE_SWARM_BOARD.md`
- Skill catalog: `/Users/matthewdukovich/Desktop/NHL Playoff Project/reports/SUPERHUMAN_REUSABLE_SKILL_CATALOG.md`
