---
name: superhuman-quality-gate-architect
description: Design and enforce outcome-based quality gates in CI/CD and local verification workflows.
---

# Superhuman Quality Gate Architect

Use this skill to convert project goals into deterministic release gates.

## Workflow
1. Translate goals into measurable KPIs and non-regression constraints.
2. Define gate tiers:
- hard fail gates
- soft warning gates
- observability-only checks
3. Implement checks in scripts and CI.
4. Ensure gates test user-relevant outcomes, not only internal metrics.
5. Add stale-data/freshness and dependency health gates when applicable.
6. Emit a release contract report with pass/fail rationale.

## Gate Design Rules
- Prefer few high-signal gates over many noisy ones.
- Every gate needs explicit threshold, rationale, and owner.
- Hard gates must block release in both local verify and CI.
- Reports must include deltas vs previous run.

## Required Outputs
- Gate contract document.
- Verification script(s) and CI wiring.
- Human-readable pass/fail report.

## Reuse Guidance
Avoid product-specific metric names in the framework layer. Use parameterized gate templates that can be reused across domains.
