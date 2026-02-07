# Verify App Agent

## What This Is

The end-to-end testing specialist who verifies the app works correctly from a user's perspective. Tests complete flows, not just individual components.

## How to Call

```
/agent:verify-app
```

## When This Agent is Called

### Automatically During
- `/project:verify` end-to-end phase
- Before deployment/release

### Call Directly When
- You want to test a complete user flow
- Something works in isolation but fails together
- Final verification before shipping
- Regression testing after changes

## What This Agent Does

### Flow Testing
- Complete user journeys
- Multiple steps working together
- Real data scenarios

### Integration Verification
- Components connect correctly
- Data persists properly
- Navigation works end-to-end

### State Testing
- App launches correctly
- State survives backgrounding
- Data loads after restart

### Edge Case Flows
- Error recovery paths
- Interruption handling
- Network failure scenarios

## Example Interaction

```
You: /agent:verify-app Test the score entry flow

Claude (as Verify App): Running end-to-end verification...

═══════════════════════════════════════════════════════
E2E VERIFICATION: Score Entry Flow
═══════════════════════════════════════════════════════

FLOW DEFINITION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
User Goal: Enter scores for a complete round
Steps: 7
Estimated time: 2-3 minutes

TEST EXECUTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Launch App
━━━━━━━━━━━━━━━━━━
✓ App launches without crash
✓ Home screen loads in < 2 seconds
✓ Previous data visible (if exists)

Step 2: Start New Round
━━━━━━━━━━━━━━━━━━━━━━━
✓ Tap "New Round" button
✓ Course selection appears
✓ Recent courses shown first

Step 3: Select Course
━━━━━━━━━━━━━━━━━━━━━
✓ Tap "Pebble Beach"
✓ Course details load
✓ Player selection appears

Step 4: Enter Scores (Holes 1-18)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Hole 1: Enter 4 → Auto-advances
✓ Hole 2: Enter 5 → Auto-advances
... (testing all 18 holes)
✓ Hole 18: Enter 3 → Summary appears
✓ Running total accurate throughout

Step 5: Review & Save
━━━━━━━━━━━━━━━━━━━━━
✓ Summary shows all scores
✓ Total matches entered scores
✓ Tap "Save Round"
✓ Confirmation shown

Step 6: Verify Persistence
━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Navigate to History
✓ New round appears
✓ Kill and relaunch app
✓ Round still present

Step 7: Verify Leaderboard Update
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Navigate to Leaderboard
✓ New score reflected
✓ Position calculated correctly

EDGE CASE TESTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Background app mid-entry → Resumes correctly
✓ Back navigation → Warns about unsaved data
⚠ Network loss during save → (See issue below)

ISSUES FOUND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issue: Network failure during save shows generic error
Severity: Medium
Expected: Specific message + offline save option
Location: SaveRoundService.swift

SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Core Flow: ✓ PASSES
Edge Cases: 2/3 pass
Issues: 1 medium

Recommendation: Fix network error handling before shipping

Fix the issue now?
```

## How This Agent Thinks

The Verify App agent asks:
1. Can a user complete this entire flow?
2. What could interrupt them?
3. Does the app recover gracefully?
4. Does data persist correctly?
5. Would a user be satisfied with this experience?

## Related Commands

- `/project:verify` — Includes E2E testing
- `/agent:test-engineer` — For unit tests
- `/agent:ux-designer` — For flow design
