# NHL Superhuman Team

## Mission
Use a specialist multi-agent workflow to keep the NHL Playoff Prediction Framework one-shot executable from `HANDOFF.md`, with zero ambiguity and verifiable quality gates.

## Team Roster
- `spec-builder`: converts requirements into testable implementation specs.
- `code-reviewer`: catches bugs, regressions, and risk before release.
- `code-simplifier`: removes unnecessary complexity while preserving behavior.
- `test-engineer`: drives unit/integration/edge-case coverage.
- `verify-app`: validates end-to-end functional behavior.
- `framework-improver`: extracts lessons into reusable operating rules.
- `creative-director`: enforces product vision coherence.
- `ui-designer`: visual hierarchy, polish, spacing, and typography quality.
- `ux-designer`: flow and information architecture.
- `visual-qa`: multi-state visual regression checks.
- `accessibility`: contrast, semantics, and assistive usability.
- `motion-designer`: purposeful transitions and interaction timing.
- `design-system`: token and component consistency.

## One-Shot Operating Loop
1. `Handoff Intake`: parse `HANDOFF.md` into requirements and constraints.
2. `Plan`: produce explicit phases with acceptance criteria.
3. `Build`: execute in order with no scope drift.
4. `Verify`: run data validation, model generation, and tests.
5. `Review`: code, UX, UI, accessibility, and simplification audits.
6. `Learn`: update memory files (`LEARNINGS.md`, `DESIGN-DECISIONS.md`, `SESSION-STATE.md`).

## NHL Project Execution Contract
- Canonical spec source: `HANDOFF.md`.
- Canonical runtime checks:
  - `python3 -m pytest -q`
  - `python3 scripts/refresh_data.py`
  - `python3 -m superhuman.dashboard_generator`
- Blocking criteria:
  - missing required handoff file paths
  - failing tests
  - invalid data merge for 32 teams
  - generation failure for `dashboard_data.json`

## Current Integration Status
- Framework command set installed in `/Users/matthewdukovich/Desktop/NHL Playoff Project/.claude/commands`.
- Framework agent set installed in `/Users/matthewdukovich/Desktop/NHL Playoff Project/.claude/agents`.
- Project memory/design artifacts created:
  - `/Users/matthewdukovich/Desktop/NHL Playoff Project/DESIGN-SYSTEM.md`
  - `/Users/matthewdukovich/Desktop/NHL Playoff Project/DESIGN-DECISIONS.md`
  - `/Users/matthewdukovich/Desktop/NHL Playoff Project/LEARNINGS.md`
  - `/Users/matthewdukovich/Desktop/NHL Playoff Project/SESSION-STATE.md`
