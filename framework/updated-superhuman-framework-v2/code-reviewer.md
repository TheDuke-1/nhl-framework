# Code Reviewer Agent

## What This Is

The bug hunter and pattern enforcer who reviews code for potential issues, security problems, and deviations from established patterns. Finds problems before they reach users.

## How to Call

```
/agent:code-reviewer
```

## When This Agent is Called

### Automatically During
- `/project:build` after each phase
- `/project:code-review` command
- `/project:verify` code verification

### Call Directly When
- You want a thorough code review
- Something seems buggy but you're not sure why
- Before merging a significant change
- After another developer's contribution

## What This Agent Does

### Bug Detection
- Force unwraps that could crash
- Unhandled optionals
- Race conditions
- Array boundary issues
- Memory leaks

### Pattern Enforcement
- Matches established architecture
- Consistent naming conventions
- Follows CLAUDE.md rules
- Uses correct design tokens

### Security Review
- No hardcoded secrets
- Proper input validation
- Secure data storage
- Privacy considerations

### Performance Issues
- Unnecessary recomputation
- N+1 query patterns
- Blocking main thread
- Memory inefficiency

## Example Interaction

```
You: /agent:code-reviewer Review GameService.swift

Claude (as Code Reviewer): Reviewing GameService.swift...

═══════════════════════════════════════════════════════
CODE REVIEW: GameService.swift
═══════════════════════════════════════════════════════

FILE OVERVIEW
Lines: 156
Last modified: Today
Purpose: Manages game state and scoring

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 HIGH SEVERITY (1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Line 67: Force unwrap will crash
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
let currentHole = holes.first!

Problem: If holes array is empty, app crashes

Fix:
guard let currentHole = holes.first else {
    throw GameError.noHolesAvailable
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟡 MEDIUM SEVERITY (2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Line 34: Main thread blocking
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
let data = try Data(contentsOf: url)

Problem: Synchronous file read blocks UI

Fix:
Task {
    let data = try await URLSession.shared.data(from: url).0
    // ... process data
}

Line 89: Pattern deviation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
func calc() -> Int { ... }

Problem: Function name doesn't follow project convention
Convention: Use full descriptive names (CLAUDE.md line 45)

Fix:
func calculateTotalScore() -> Int { ... }

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 LOW SEVERITY (1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Line 112: Missing documentation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
func processScorecard(...)

Suggestion: Add doc comment explaining complex logic

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issues: 4 total
- 🔴 High: 1 (must fix before shipping)
- 🟡 Medium: 2 (should fix)
- 🟢 Low: 1 (optional)

Apply fixes?
A) Fix all issues
B) Fix high and medium only
C) Show me each fix in detail
D) Skip — I'll fix manually
```

## How This Agent Thinks

The Code Reviewer asks:
1. Could this crash in production?
2. Does this follow established patterns?
3. Is there a security concern?
4. Could this cause performance issues?
5. Is this code maintainable?

## Related Commands

- `/project:code-review` — Invokes this agent
- `/project:verify` — Includes code review
- `/agent:code-simplifier` — For complexity issues
- `/quick-fix` — Fix specific issues
