# /project:commit-push-pr Command

## What This Is

Git Autopilot: handles branching, commits, pushing, and PR creation. Claude manages Git so you don't have to — with checkpoint confirmations before major operations.

## How to Use

```
/project:commit-push-pr
```

Or with a message:
```
/project:commit-push-pr "Add leaderboard feature"
```

## What Happens

1. **Status Check:** Reviews current Git state
2. **Branch Management:** Creates/switches branches as needed
3. **Staging:** Identifies and stages relevant changes
4. **Commit:** Creates meaningful commit message
5. **Push:** Pushes to remote with confirmation
6. **PR Creation:** Opens pull request with description

## Checkpoint Confirmations

Claude confirms before major operations:

### Before Creating Branch
```
I'm about to create a branch called 'feature/add-leaderboard'.

Think of a branch like a draft copy — we can experiment here without 
affecting the main version of your app.

👍 Create this branch?
A) Yes — create it
B) Use a different name
C) Stay on current branch
```

### Before Pushing
```
Ready to push these changes to GitHub:

Branch: feature/add-leaderboard
Commits: 3
  • Add LeaderboardEntry model
  • Implement leaderboard view
  • Add tests for leaderboard

This makes your changes visible on GitHub (but not merged yet).

👍 Push now?
A) Yes — push to GitHub
B) Wait — I want to add more changes first
C) Show me the changes in detail
```

### Before Creating PR
```
Ready to create a Pull Request:

Title: Add Leaderboard Feature
From: feature/add-leaderboard → main

Description:
## What This PR Does
Adds a leaderboard showing top 10 players by score.

## Changes
- New LeaderboardEntry model
- LeaderboardView with empty state handling
- Unit tests for sorting logic

## Testing
- Tested on iPhone SE, 16, and Pro Max
- Verified light and dark mode
- All existing tests pass

Create this PR?
A) Yes — create PR
B) Edit the description first
C) Not yet — I want to make more changes
```

## Git Operations Handled

| Operation | What Claude Does |
|-----------|------------------|
| **Branch creation** | Names appropriately (feature/, bugfix/, etc.) |
| **Commit messages** | Clear, descriptive, conventional format |
| **Staging** | Selects relevant files, excludes artifacts |
| **Pushing** | Handles upstream tracking |
| **PR creation** | Writes description, links issues |
| **Conflicts** | Attempts auto-resolve, escalates if complex |

## Example Interaction

```
You: /project:commit-push-pr

Claude: Checking Git status...

═══════════════════════════════════════════════════════
GIT STATUS
═══════════════════════════════════════════════════════

Current branch: feature/add-leaderboard
Status: 3 files modified, 2 files added

Modified:
  • LinksLedger/Models/Player.swift (added relationship)
  • LinksLedger/Views/MainTabView.swift (added tab)
  • LinksLedgerTests/PlayerTests.swift (updated)

Added:
  • LinksLedger/Models/LeaderboardEntry.swift
  • LinksLedger/Views/LeaderboardView.swift

═══════════════════════════════════════════════════════

These changes look like they complete the leaderboard feature.

Proposed commit message:
"Add leaderboard feature with top 10 player display"

Stage and commit these changes?
A) Yes — commit with this message
B) Change the commit message
C) Split into multiple commits
D) Show me the diffs first

You: A

Claude: Committed ✓

Push to GitHub?
A) Yes — push now
B) Not yet

You: A

Claude: Pushed ✓

Create Pull Request?
A) Yes — create PR
B) Not yet

You: A

Claude: Creating PR...

✓ Pull Request created!
URL: https://github.com/yourname/links-ledger/pull/15

The PR is ready for review. You can merge it from GitHub 
when you're ready, or I can help with that too.
```

## Teaching Mode

Claude explains Git concepts as it works:

```
"I'm creating a branch — think of this like making a copy of your 
project where we can experiment. The original (main) stays safe."

"Committing is like saving a checkpoint. If anything goes wrong later, 
we can always come back to this point."

"A Pull Request is how you propose merging your changes into the main 
version. It lets you (or others) review before finalizing."
```

Over time, you'll learn Git naturally through these explanations.

## Session-End Git Summary

At `/session-end`, you'll see a summary:

```
GIT ACTIVITY THIS SESSION
═════════════════════════
Branch: feature/add-leaderboard
Commits: 3
  • Add LeaderboardEntry model
  • Implement LeaderboardView with empty state
  • Add unit tests for leaderboard sorting
Status: Pushed, PR #15 open
```

## Rules This Command Follows

### Always Confirm First
- Never push without confirmation
- Never create PR without confirmation
- Show exactly what will happen

### Meaningful Commit Messages
- Describe WHAT changed and WHY
- Use conventional format when appropriate
- Group related changes logically

### Teach as You Go
- Explain Git concepts in plain English
- Build understanding over time
- Answer questions about what's happening

### Handle Errors Gracefully
- Conflicts get explained, not just error messages
- Provide resolution options
- Never leave Git in a broken state

## Related Commands

- `/project:verify` — Verify before committing
- `/session-end` — Includes Git status summary
- `/project:status` — Check Git state anytime
