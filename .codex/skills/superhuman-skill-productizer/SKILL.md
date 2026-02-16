---
name: superhuman-skill-productizer
description: Convert successful project workflows into reusable Superhuman skills for future projects.
---

# Superhuman Skill Productizer

Use this skill when you want to turn ad-hoc execution knowledge into reusable skill assets.

## Workflow
1. Identify repeated, high-value workflows.
2. Extract invariant steps vs project-specific details.
3. Create reusable assets:
- `SKILL.md`
- `agents/openai.yaml`
- optional templates/references
4. Add adaptation guidance:
- required inputs
- assumptions
- customization points
5. Validate by running the skill against a different scenario.
6. Publish a skill catalog and versioning notes.

## Productization Rules
- Skills must be self-contained.
- Prefer parameterized language over hardcoded paths.
- Include failure modes and fallback behavior.
- Keep setup requirements explicit.

## Required Outputs
- Reusable skill pack.
- Skill catalog with when-to-use guidance.
- Versioned changelog entry.

## Reuse Guidance
Design for transferability first. If a step depends on local project structure, provide a project-agnostic alternative.
