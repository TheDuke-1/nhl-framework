# /session-end Command

## What This Is

Clean handoff ritual that saves state, summarizes what happened, and prepares for the next session. Run this before ending your chat.

## How to Use

```
/session-end
```

## What Happens

1. **State Capture:** Saves current progress to SESSION-STATE.md
2. **Learning Check:** Asks if there are learnings to capture
3. **Git Summary:** Shows git activity this session
4. **Session Summary:** Overview of what was accomplished
5. **Handoff:** Clear context for next session

## What Gets Saved

### To SESSION-STATE.md
```markdown
# Session State

## Last Updated
February 4, 2026 at 2:30 AM

## Current Task
Adding leaderboard feature

## Progress
- [x] Spec completed
- [x] Data model implemented
- [ ] UI implementation (60%)
- [ ] Testing

## Open Items
- Empty state handling needed
- Sort order logic pending

## Recent Decisions
- Using @Query for live updates
- Showing top 10 players only

## Files Modified This Session
- Models/LeaderboardEntry.swift (created)
- Views/LeaderboardView.swift (in progress)

## Notes for Next Session
Start with empty state, then add sort toggle
```

## Example Interaction

```
You: /session-end

Claude: Preparing session handoff...

═══════════════════════════════════════════════════════
SESSION SUMMARY
═══════════════════════════════════════════════════════

Duration: ~45 minutes
Task: Adding leaderboard feature

Accomplished:
✓ Created LeaderboardEntry model with SwiftData
✓ Built basic LeaderboardView layout
✓ Integrated with existing GameModel

Remaining:
○ Empty state handling
○ Sort order toggle
○ Testing

═══════════════════════════════════════════════════════
GIT ACTIVITY
═══════════════════════════════════════════════════════

Branch: feature/leaderboard
Commits: 2
  • Add LeaderboardEntry model
  • Initial LeaderboardView layout
Status: 1 uncommitted change (LeaderboardView in progress)

═══════════════════════════════════════════════════════
LEARNINGS
═══════════════════════════════════════════════════════

Potential learnings from this session:
1. @Query automatically updates when data changes
2. Need to handle empty array before accessing .first

Capture these learnings?
A) Yes — add to LEARNINGS.md
B) Skip — nothing worth capturing

═══════════════════════════════════════════════════════

State saved to SESSION-STATE.md.

To resume next time, start a new chat and run:
/session-start
```

## When to Run This

### Always Run Before
- Closing the chat
- Taking a long break
- Switching to a different project
- Context getting long (30+ exchanges)

### Signs You Should End Session
- Claude starts forgetting earlier decisions
- Responses seem slower or less coherent
- You're about to switch tasks entirely
- You've completed a natural milestone (spec done, feature done)

## Rules This Command Follows

### Save Everything Needed to Resume
- Current task and progress
- Open items and blockers
- Recent decisions (so we don't re-debate them)
- Files being worked on

### Prompt for Learnings
- Don't auto-capture without asking
- Highlight potential learnings
- Let you decide what's worth keeping

### Clear Git Status
- Show what was committed
- Show what's uncommitted
- Confirm branch state

### Make Handoff Explicit
- Clear summary of where things stand
- Explicit instructions for resuming
- No ambiguity about next steps

## Session Health Signals

The command also monitors for signs of session degradation:

**Healthy Session:**
- Context is clear
- Responses are accurate
- Decisions are remembered

**Degraded Session:**
- Repeating explanations
- Forgetting earlier decisions
- Responses getting slower

If degradation is detected, Claude will recommend ending sooner.

## Related Commands

- `/session-start` — Resume with context in new chat
- `/framework-improve` — Deep learning extraction (more thorough than session-end)
- `/project:status` — See status without ending session
