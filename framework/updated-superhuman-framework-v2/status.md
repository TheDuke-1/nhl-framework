# /project:status Command

## What This Is

Dashboard showing current state: progress on current task, files touched, Git status, and any blockers. Quick visibility without interrupting your flow.

## How to Use

```
/project:status
```

## What It Shows

### Task Progress
- Current task being worked on
- Phase progress (if building from plan)
- What's done vs. what's remaining

### Files State
- Recently modified files
- Uncommitted changes
- Files with issues

### Git Status
- Current branch
- Commits ahead/behind
- Uncommitted changes count

### Blockers
- Any issues preventing progress
- Decisions needed
- External dependencies

## Example Output

```
You: /project:status

Claude: 
═══════════════════════════════════════════════════════
PROJECT STATUS: Links Ledger
═══════════════════════════════════════════════════════

CURRENT TASK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Feature: Leaderboard
Phase: 3 of 5 (UI Implementation)
Progress: ████████████░░░░░░░░ 60%

Completed:
  ✓ Phase 1: Data model
  ✓ Phase 2: Query logic
  ◐ Phase 3: UI implementation (in progress)
  ○ Phase 4: Integration
  ○ Phase 5: Verification

FILES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Modified this session:
  • Models/LeaderboardEntry.swift ✓
  • Services/LeaderboardService.swift ✓
  • Views/LeaderboardView.swift (in progress)

Uncommitted: 3 files

GIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Branch: feature/leaderboard
Commits: 2 (ahead of main)
Uncommitted changes: 3 files

BLOCKERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
None

NEXT STEP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Complete LeaderboardView empty state handling

═══════════════════════════════════════════════════════
```

## When to Use This

- **Mid-task check:** Where am I in the build?
- **Session resume:** Quick context before `/session-start`
- **Before committing:** What's changed?
- **Feeling lost:** Get oriented

## Status vs. Other Commands

| Command | Use For |
|---------|---------|
| `/project:status` | Quick dashboard, no action |
| `/session-start` | Full context load, ready to work |
| `/session-end` | Wrap up, save state |
| `/project:verify` | Active testing, not just viewing |

## Rules This Command Follows

### Quick and Non-Disruptive
- Just shows information
- Doesn't change any state
- Fast to run

### Show What Matters
- Focus on current task context
- Highlight blockers prominently
- Clear next step

### Accurate Git State
- Always check actual Git status
- Don't rely on cached information
- Show real file states

## Related Commands

- `/session-start` — Full context load
- `/project:verify` — Active verification
- `/project:commit-push-pr` — Act on Git status
