# /project:build Command

## What This Is

Executes the plan and builds the feature. This is where code gets written, following the phases defined in your execution plan.

## How to Use

```
/project:build [plan-name]
```

Or just:
```
/project:build
```
And Claude will use the most recent plan.

## What Happens

1. **Load Plan:** Reads PLAN-[feature].md
2. **Load Design System:** Ensures visual requirements are followed
3. **Execute Phases:** Builds each phase with checkpoints
4. **Verify Per Phase:** Confirms build succeeds after each phase
5. **Progress Updates:** Dashboard-style status as work progresses
6. **Agent Integration:** Automatically invokes relevant agents

## Visibility During Build

### For Small Tasks (1-2 phases)
Brief updates:
```
✓ Phase 1 complete: Model created
✓ Phase 2 complete: View implemented
```

### For Large Tasks (3+ phases)
Dashboard + Checkpoints:
```
BUILD STATUS
══════════════════════════════════════
Feature: Leaderboard
Phase: 2 of 5 (Core Logic)
Progress: ████████░░░░░░░░ 40%
Files Modified: 2
Current: LeaderboardService.swift
Blockers: None
══════════════════════════════════════

Phase 1 complete ✓
- LeaderboardEntry.swift created
- Model compiles, relationships verified

Moving to Phase 2: Core Logic
- Creating LeaderboardService.swift
- Implementing fetch and sort logic

Questions before I continue?
```

## Agent Integration

These agents are automatically invoked during build:

| Phase Type | Agent Called | Purpose |
|------------|--------------|---------|
| Data Model | Code Reviewer | Verify model design |
| UI | UI Designer | Check design compliance |
| UI | Visual QA | Verify rendering |
| Any | Test Engineer | Create/run tests |

You can also manually invoke agents during build:
```
/agent:code-simplifier  # If code is getting complex
/agent:accessibility    # For accessibility check
```

## Example Interaction

```
You: /project:build

Claude: Loading plan for leaderboard feature...

═══════════════════════════════════════════════════════
STARTING BUILD: Leaderboard
═══════════════════════════════════════════════════════

Phase 1 of 5: Data Model
Estimated: 20 minutes

Creating LeaderboardEntry.swift...

import SwiftData

@Model
final class LeaderboardEntry {
    var playerName: String
    var score: Int
    var date: Date
    var gameType: GameType
    
    @Relationship(inverse: \Player.leaderboardEntries)
    var player: Player?
    
    init(playerName: String, score: Int, date: Date, gameType: GameType) {
        self.playerName = playerName
        self.score = score
        self.date = date
        self.gameType = gameType
    }
}

Verifying...
✓ Build succeeds
✓ Model integrates with SwiftData

Code Reviewer check:
✓ Properties are appropriate types
✓ Relationship correctly defined
✓ Init is complete

Phase 1 complete ✓

═══════════════════════════════════════════════════════

Moving to Phase 2: Query Logic

Continue?
A) Yes — proceed
B) Wait — I have a question about Phase 1
C) Stop — I want to review the code first
```

## Rules This Command Follows

### Follow the Plan
- Execute phases in order
- Don't skip verification steps
- Don't add scope not in the plan

### Checkpoint Between Phases
- Build must succeed after each phase
- Ask before proceeding to next phase (for large tasks)
- Show progress clearly

### Apply Design System
- Use exact design tokens from DESIGN-SYSTEM.md
- Never hardcode colors, fonts, or spacing
- Visual elements match the spec

### Quality Throughout
- Clean code from the start (not "fix it later")
- Tests written alongside implementation
- Edge cases handled as specified

### Handle Blockers
- If something doesn't work, stop and diagnose
- Don't proceed with broken foundation
- Offer alternatives if stuck

## What's Next

After building:
```
/project:verify   # Full verification
```

## Related Commands

- `/project:plan` — Create the plan this builds from
- `/project:verify` — Full verification after building
- `/project:status` — See progress during build
- `/quick-fix` — Fix specific issues that arise during build
