---
name: superhuman-dashboard-trust-polisher
description: Improve dashboard trust UX by separating model quality vs release readiness, surfacing goal gaps, and showing concrete blockers.
---

# Superhuman Dashboard Trust Polisher

Use this skill when dashboard quality must be upgraded without drifting from release truth.

## Workflow
1. Regenerate data and grade artifacts.
2. Verify mission/control surfaces show:
- model quality status
- release readiness status
- goal gap runway
- explicit blocker reasons
3. Validate freshness states and source trust rows.
4. Run dashboard tests (`python3 -m pytest tests/test_dashboard.py -q` and interaction tests).
5. Document what changed and why it improves user trust.

## Rules
- Never represent release as healthy when gate status is `FAIL`.
- Keep benchmark and release timestamps visible.
- If grades are capped, show the cap reason explicitly.
- Prefer clear failure language over optimistic summaries.
