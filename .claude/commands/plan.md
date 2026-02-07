# /project:plan Command

## What This Is

Creates a step-by-step execution plan for implementing a spec. This is the bridge between "what you want" (spec) and "how to build it" (plan).

## How to Use

```
/project:plan [spec-name]
```

Or just:
```
/project:plan
```
And Claude will ask which spec to plan for, or use the most recent one.

## What Happens

1. **Load Spec:** Reads the specified SPEC-[feature].md file
2. **Analyze Dependencies:** Identifies what existing code needs to be modified
3. **Design Integration:** Checks DESIGN-SYSTEM.md for visual requirements
4. **Create Phases:** Breaks work into logical, verifiable phases
5. **Estimate Effort:** Notes complexity and potential blockers
6. **Output Plan:** Creates PLAN-[feature].md

## Plan Structure

```markdown
# Execution Plan: [Feature Name]

## Spec Reference
SPEC-[feature].md

## Prerequisites
- [x] DESIGN-SYSTEM.md exists
- [x] Data model understood
- [ ] API endpoint ready (blocker)

## Phases

### Phase 1: Data Model (15 min)
Files: Models/[Name].swift
Tasks:
- Create model with required properties
- Add relationships to existing models
- Verify with SwiftData

### Phase 2: Core Logic (30 min)
Files: Services/[Name]Service.swift
Tasks:
- Implement business logic
- Handle edge cases from spec
- Unit tests

### Phase 3: UI Implementation (45 min)
Files: Views/[Name]View.swift
Tasks:
- Build layout per spec
- Apply design tokens
- Handle all states (empty, loading, error, data)

### Phase 4: Integration (15 min)
Files: [Various]
Tasks:
- Connect to navigation
- Wire up data flow
- Integration test

### Phase 5: Verification (20 min)
Tasks:
- Multi-device check
- Light/dark mode
- Accessibility audit
- Visual regression check

## Estimated Total: ~2 hours

## Risks & Blockers
- None identified
```

## Example Interaction

```
You: /project:plan

Claude: I see SPEC-leaderboard.md was created recently. Create execution plan 
for the leaderboard feature?

A) Yes — plan for leaderboard
B) Different spec — let me specify

You: A

Claude: Creating execution plan for leaderboard...

Reading spec...
Checking DESIGN-SYSTEM.md...
Analyzing existing codebase...

═══════════════════════════════════════════════════════
EXECUTION PLAN: Leaderboard Feature
═══════════════════════════════════════════════════════

Phase 1: Data Model (20 min)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Create LeaderboardEntry model:
- playerName: String
- score: Int
- date: Date
- gameType: GameType

Relationship: Links to existing Player model

Phase 2: Query Logic (15 min)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Fetch top 10 by score
- Filter by game type
- Sort descending

...

Plan saved to PLAN-leaderboard.md

Ready to execute?
/project:build to start building
```

## Rules This Command Follows

### Always Check Design System
- Every UI phase references specific design tokens
- No "make it look nice" — specific colors, fonts, spacing

### Phases Must Be Verifiable
- Each phase has a clear "done" state
- Build should succeed after each phase
- No massive phases that can't be checked incrementally

### Include Time Estimates
- Realistic estimates for each phase
- Total estimate for the feature
- Helps set expectations

### Flag Risks Early
- Dependencies that might block
- Unknowns that need research
- Areas likely to need iteration

## What's Next

After planning:
```
/project:build    # Execute the plan
```

## Related Commands

- `/interview` — Create the spec this plan is based on
- `/project:build` — Execute this plan
- `/project:status` — See current progress through the plan
