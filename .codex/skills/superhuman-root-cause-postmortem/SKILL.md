---
name: superhuman-root-cause-postmortem
description: Run evidence-based root cause analysis and prevention loops after bugs, regressions, or failed gates.
---

# Superhuman Root Cause Postmortem

Use this skill when the team needs to learn from failures and prevent repeats.

## Workflow
1. Reconstruct the failure timeline with concrete evidence.
2. Identify primary and contributing causes using `5 Whys`.
3. Separate symptom, trigger, root cause, and detection gap.
4. Define corrective actions by layer:
- code fix
- test/gate fix
- process/ownership fix
5. Add regression guards and release checks.
6. Capture learnings in project memory files and reusable patterns.

## Postmortem Rules
- Evidence over assumptions.
- No blame language; focus on system design and controls.
- Every root cause must map to:
- owner
- due action
- verification method

## Required Outputs
- One-page postmortem summary.
- Prevention checklist with owners.
- Updated regression tests or verification gate.

## Reuse Guidance
Keep terminology and checklist generic so this skill can be reused in any software project.
