# /framework-improve Command

## What This Is

Reviews the current session and extracts learnings into the framework. This is how the framework gets smarter over time — bugs found today become rules that prevent bugs tomorrow.

## How to Use

```
/framework-improve
```

Best run at the end of a session or after fixing a significant bug.

## What Happens

1. **Session Review:** Claude reviews what happened this session
2. **Pattern Detection:** Identifies bugs, fixes, decisions, and discoveries
3. **Learning Extraction:** Converts findings into actionable rules
4. **Smart Routing:** Routes each learning to the right place
5. **Template Evolution:** Suggests updates to project templates
6. **Confirmation:** Shows proposed changes for your approval

## Where Learnings Go

### Project CLAUDE.md
Rules specific to THIS project:
- Domain-specific patterns (golf terms, specific data models)
- This codebase's architectural decisions
- Project-specific edge cases

### Global CLAUDE.md
Rules that apply to ALL projects:
- General coding patterns
- Communication improvements
- Process improvements

### LEARNINGS.md
Full context for every learning:
- What happened
- When it happened
- Why it was a problem
- How it was fixed
- Category tags for searchability

### DESIGN-DECISIONS.md
Design taste memory:
- Approvals with reasoning
- Rejections with reasoning
- Extracted principles

### Template Repository
When learnings are universal enough, suggests updates to your GitHub template so new projects start smarter.

## Example Interaction

```
You: /framework-improve

Claude: Reviewing this session for learnings...

═══════════════════════════════════════════════════════
SESSION ANALYSIS
═══════════════════════════════════════════════════════

Bugs Fixed: 2
Decisions Made: 3
New Patterns Discovered: 1

═══════════════════════════════════════════════════════
PROPOSED LEARNINGS
═══════════════════════════════════════════════════════

LEARNING 1: Dark Mode Color Override
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
What happened: Card backgrounds were invisible in dark mode
Root cause: Using .white instead of design token
Fix: Always use semantic colors from DESIGN-SYSTEM.md

Proposed rule: "Never use .white or .black directly. Always use 
cardBackground, primaryText, etc. from the design system."

Route to: Project CLAUDE.md (SwiftUI-specific)

LEARNING 2: Empty State Check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
What happened: App crashed when leaderboard had no entries
Root cause: Didn't handle empty array case
Fix: Added empty state view

Proposed rule: "Every list view must have an empty state. Check for 
.isEmpty before rendering."

Route to: Global CLAUDE.md (universal pattern)

═══════════════════════════════════════════════════════

Apply these learnings?

A) Yes — add all of them
B) Yes to Learning 1, skip Learning 2
C) Yes to Learning 2, skip Learning 1
D) Edit the rules first — let me refine the wording
E) Skip all — don't add anything this time
```

## Rules This Command Follows

### Extract Actionable Rules
- Not "we fixed a bug" but "always check X to prevent Y"
- Rules should be specific enough to follow
- Include the WHY, not just the WHAT

### Smart Routing
- Project-specific stays in project
- Universal goes global
- When uncertain, ask

### Full Context in LEARNINGS.md
- LEARNINGS.md gets the full story
- CLAUDE.md gets the actionable rule
- Both are connected (LEARNINGS.md references support the rule)

### Template Evolution
- If a learning would help ALL future projects, suggest template update
- Don't auto-update templates — confirm first

## The Learning Formula

```
Bug Found → Fix Applied → Learning Captured → Routed Correctly → Template Updated
                              ↓
              Future projects start smarter
              Current project gets stronger
              Framework evolves automatically
```

## Related Commands

- `/session-end` — Also captures learnings as part of session wrap-up
- `/quick-fix` — Can trigger learning capture for individual fixes
- `/project:verify` — Verification findings can feed into learnings
