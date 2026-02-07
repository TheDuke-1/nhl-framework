---
name: superhuman-builder-verifier
description: Build and verification skill for this project. Use when implementing planned work and enforcing quality gates before completion.
---

# Superhuman Builder Verifier

## Workflow
1. Execute implementation using `/project:build`.
2. Run `/project:verify`.
3. Run `python3 -m pytest -q`.
4. Run `python3 scripts/validate_data.py`.
5. Generate dashboard outputs with `python3 -m superhuman.dashboard_generator`.

## Rules
- Treat failing tests as blocking.
- Treat stale data as warning unless strict freshness is requested.
- Re-run verification after every fix.
