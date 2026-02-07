# /project:code-review Command

## What This Is

Deep code review focusing on bugs, patterns, security, and improvement opportunities. This is more thorough than the verification step — it's a focused specialist review.

## How to Use

```
/project:code-review [file-or-scope]
```

Examples:
```
/project:code-review                    # Review recent changes
/project:code-review LeaderboardView    # Review specific file
/project:code-review Models/            # Review entire directory
```

## What Happens

1. **Scope Identification:** Determines what to review
2. **Bug Hunting:** Looks for potential crashes, logic errors
3. **Pattern Analysis:** Checks against established patterns
4. **Security Check:** Identifies potential vulnerabilities
5. **Simplification Opportunities:** Flags overly complex code
6. **Report Generation:** Detailed findings with recommendations

## Review Categories

### 🐛 Bugs & Crashes
- Force unwraps that could crash
- Unhandled optionals
- Race conditions
- Array index out of bounds risks

### 📐 Patterns & Architecture
- Deviation from established patterns
- Inconsistent naming
- Missing abstractions
- Coupling issues

### 🔒 Security
- Hardcoded sensitive data
- Insecure storage
- Input validation gaps
- Privacy concerns

### 🧹 Code Quality
- Overly complex logic
- Duplication
- Dead code
- Missing comments for "why"

### ⚡ Performance
- Unnecessary recomputation
- Memory leaks
- Inefficient algorithms
- Blocking operations

## Example Interaction

```
You: /project:code-review LeaderboardView

Claude: Reviewing LeaderboardView.swift...

═══════════════════════════════════════════════════════
CODE REVIEW: LeaderboardView.swift
═══════════════════════════════════════════════════════

FINDINGS: 4 issues (1 high, 2 medium, 1 low)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 HIGH: Potential Crash
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Line 45:
let topPlayer = entries.first!

Problem: Force unwrap will crash if entries is empty

Fix:
guard let topPlayer = entries.first else {
    return EmptyLeaderboardView()
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟡 MEDIUM: Pattern Deviation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Line 23:
.foregroundColor(Color(hex: "#D4AF37"))

Problem: Hardcoded color instead of design token

Fix:
.foregroundColor(.goldAccent)

Reference: DESIGN-SYSTEM.md specifies using semantic colors

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟡 MEDIUM: Missing Accessibility
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Line 67-72:
HStack { ... }

Problem: No accessibility label for VoiceOver users

Fix:
HStack { ... }
    .accessibilityElement(children: .combine)
    .accessibilityLabel("\(player.name), score \(player.score)")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 LOW: Simplification Opportunity
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Lines 34-42:
if condition {
    return true
} else {
    return false
}

Simplify to:
return condition

═══════════════════════════════════════════════════════
SUMMARY
═══════════════════════════════════════════════════════

Total Issues: 4
- 🔴 High: 1 (must fix)
- 🟡 Medium: 2 (should fix)
- 🟢 Low: 1 (nice to fix)

Apply fixes?
A) Fix all issues
B) Fix high and medium only
C) Show me each fix in detail
D) I'll fix manually
```

## Agents Involved

| Agent | Role |
|-------|------|
| Code Reviewer | Bug detection, patterns |
| Code Simplifier | Complexity reduction |
| Test Engineer | Test coverage gaps |

## Rules This Command Follows

### Severity Levels Are Meaningful
- 🔴 HIGH: Will cause crashes or data loss
- 🟡 MEDIUM: Deviation from standards, potential issues
- 🟢 LOW: Improvements, not problems

### Provide Exact Fixes
- Show the problem code
- Show the fixed code
- Explain WHY it's better

### Reference Standards
- Link to DESIGN-SYSTEM.md for design issues
- Link to CLAUDE.md for pattern issues
- Link to LEARNINGS.md for past mistakes

### Feed Into Learning System
- High issues → potential CLAUDE.md rules
- Recurring issues → pattern to prevent

## Related Commands

- `/project:verify` — Broader verification including visual
- `/agent:code-reviewer` — Direct access to code reviewer agent
- `/agent:code-simplifier` — Direct access to simplifier agent
- `/quick-fix` — Fix specific issues quickly
