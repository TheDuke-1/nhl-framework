# /session-start Command

## What This Is

Resumes work with full context from where you left off. Reads saved state, recent learnings, and design system to get back up to speed instantly.

## How to Use

```
/session-start
```

Run this at the beginning of a new chat when continuing work on a project.

## What Happens

1. **Load State:** Reads SESSION-STATE.md for context
2. **Check Learnings:** Reviews recent LEARNINGS.md entries
3. **Load Design System:** Reads DESIGN-SYSTEM.md for current standards
4. **Summarize:** Shows you where we left off
5. **Confirm:** Asks what you want to work on next

## What Gets Loaded

### From SESSION-STATE.md
- Last task being worked on
- Current progress/phase
- Open items or blockers
- Recent decisions made
- Files that were being modified

### From LEARNINGS.md
- Recent learnings (last 5-10 entries)
- Any patterns relevant to current work

### From DESIGN-SYSTEM.md
- Current design tokens
- Visual standards to maintain

### From CLAUDE.md
- Project rules and context
- Domain-specific knowledge

## Example Interaction

```
You: /session-start

Claude: Loading session context...

═══════════════════════════════════════════════════════
SESSION RESUME
═══════════════════════════════════════════════════════

Last Session: February 3, 2026 at 11:45 PM
Duration: 45 minutes
Task: Adding leaderboard feature

Progress:
✓ Spec completed (SPEC-leaderboard.md)
✓ Data model implemented
◐ UI implementation (60% complete)
○ Testing not started

Open Items:
- LeaderboardView needs empty state handling
- Sort order logic not yet implemented

Recent Learnings Applied:
- Using semantic colors from DESIGN-SYSTEM.md
- Empty state required for all list views

Git Status:
- Branch: feature/leaderboard
- 2 uncommitted changes

═══════════════════════════════════════════════════════

Ready to continue with leaderboard UI implementation?

A) Yes — pick up where we left off
B) Show me the current LeaderboardView code first
C) I want to work on something else
D) Let me review the spec first
```

## When to Use This

**Start of Every New Chat:** If you're continuing work on a project from a previous session.

**After Context Loss:** If the conversation got long and Claude seems to have forgotten things.

**Project Switching:** When coming back to a project after working on something else.

## Rules This Command Follows

### Always Load Core Files
- SESSION-STATE.md (if exists)
- CLAUDE.md (project rules)
- DESIGN-SYSTEM.md (if exists)

### Summarize, Don't Dump
- Show key information, not raw file contents
- Highlight what's relevant for continuing
- Make it easy to pick up where you left off

### Confirm Understanding
- Restate the current task
- Show progress status
- Ask before proceeding

## Related Commands

- `/session-end` — Run at the end of a session to save state
- `/project:status` — See current status without loading full context
- `/framework-improve` — Extract learnings before ending a session
