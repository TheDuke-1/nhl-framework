---
name: superhuman-issue-squad-orchestrator
description: Create and run multi-agent issue squads with explicit ownership, dependencies, verification, and learning capture.
---

# Superhuman Issue Squad Orchestrator

Use this skill when a project has multiple high-impact issues and needs parallelized execution by specialist agents.

## Workflow
1. Build an issue register with severity, user impact, and root-risk.
2. Assign a squad per issue:
- one accountable lead agent
- at least two supporting agents from different specialties
3. Define issue-level acceptance criteria and blocking dependencies.
4. Run work in waves: `stabilize -> correctness -> UX/trust -> optimization`.
5. Require verification proof for each issue:
- test proof
- metric/report proof
- failure-mode proof
6. Close each issue only after adding a learning and a prevention action.

## Squad Design Rules
- Every issue has one clear owner.
- No issue may be marked done without measurable evidence.
- Use explicit handoffs between squads when dependencies exist.
- Keep issue status machine-readable: `Not Started`, `In Progress`, `Blocked`, `Done`.

## Required Outputs
- An issue swarm board with:
- issue id
- problem statement
- assigned agents
- acceptance criteria
- dependencies
- current status
- A short release readiness summary across all issues.

## Reuse Guidance
This skill is project-agnostic. Keep squad roles and acceptance criteria template-driven so it can be reused in any repo.
