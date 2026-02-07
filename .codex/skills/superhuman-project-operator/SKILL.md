---
name: superhuman-project-operator
description: End-to-end orchestration skill for this NHL project using the full Superhuman Framework. Use when the user asks the team to plan, build, verify, review, improve, or hand off work using installed slash commands, agents, and process docs.
---

# Superhuman Project Operator

Execute this workflow for any feature, bugfix, review, or full-project request.

## Workflow
1. Read project context from `CLAUDE.md`, `HANDOFF.md`, and `TEAM_SKILLS.md`.
2. Pick the correct entry process:
- New scope: run discovery flow from `references/process-map.md`.
- Existing code update: run build + verify flow from `references/process-map.md`.
- Quality request: run review flow from `references/process-map.md`.
3. Use project commands from `references/commands.md`.
4. Use specialist agents from `references/agents.md`.
5. Run verification gates before finalizing:
- `python3 -m pytest -q`
- `python3 scripts/validate_data.py`
- `python3 -m superhuman.dashboard_generator` (or direct script fallback)
6. Capture updates in `LEARNINGS.md`, `DESIGN-DECISIONS.md`, and `SESSION-STATE.md` when relevant.

## Execution Rules
- Prefer deterministic execution over narrative planning.
- Keep scope aligned to explicit user request; no silent scope expansion.
- Treat test failures as blockers.
- Treat data freshness warnings as non-blocking unless strict mode is requested.
- Use strict data gate only when needed:
`python3 scripts/validate_data.py --strict`

## References
- Commands: `references/commands.md`
- Agents: `references/agents.md`
- Processes: `references/process-map.md`
- Framework files: `references/framework-files.md`
