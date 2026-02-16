---
name: superhuman-prevention-loop
description: Convert each failure into durable controls by linking root cause, tests, gates, ownership, and reusable playbooks.
---

# Superhuman Prevention Loop

Use this skill when the team must deliver permanent fixes instead of temporary patches.

## Workflow
1. Reconstruct failure evidence with exact commands, files, and timestamps.
2. Identify root cause, trigger, and detection gap separately.
3. Implement layered controls:
- code correction
- regression test coverage
- release gate enforcement
- dashboard/report truth alignment
4. Assign owner and closure SLA for each control.
5. Verify with full project gate suite.
6. Capture learning in memory and update reusable skills/catalog.

## Prevention Rules
- No issue is closed on code change alone; test and gate proof are required.
- If release is FAIL, no report may represent the surface as PASS.
- Treat stale critical inputs as release blockers.
- Prefer structural fixes (architecture/contract/process) over threshold hacks.

## Required Outputs
- Issue closure checklist with proof links.
- Prevention controls table (owner, control type, verification command).
- Learning log entry and design-decision update.

## Reuse Guidance
This skill is project-agnostic. Replace metric names and thresholds with the target project's objective contract while preserving the prevention workflow.
