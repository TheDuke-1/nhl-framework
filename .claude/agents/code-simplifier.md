# Code Simplifier Agent

## What This Is

The complexity reducer who refactors convoluted code into clean, readable solutions. Makes code easier to understand, maintain, and debug.

## How to Call

```
/agent:code-simplifier
```

## When This Agent is Called

### Automatically During
- `/project:code-review` when complexity flagged
- Post-build cleanup phases

### Call Directly When
- Code feels too complicated
- A function is doing too much
- You can't understand code you wrote
- Before adding more features to complex code

## What This Agent Does

### Reduce Complexity
- Break large functions into smaller ones
- Remove unnecessary nesting
- Simplify conditional logic
- Extract repeated patterns

### Improve Readability
- Better variable names
- Clearer function names
- Logical organization
- Appropriate comments

### Remove Duplication
- Extract shared logic
- Create reusable utilities
- DRY (Don't Repeat Yourself)

### Modernize Patterns
- Use newer Swift features appropriately
- Replace verbose patterns with concise ones
- Update deprecated approaches

## Example Interaction

```
You: /agent:code-simplifier This function is hard to follow

Claude (as Code Simplifier): Let me simplify this code...

═══════════════════════════════════════════════════════
CODE SIMPLIFICATION
═══════════════════════════════════════════════════════

ORIGINAL (32 lines, 4 nesting levels):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

func processScores(_ scores: [Score]) -> [Player] {
    var results: [Player] = []
    for score in scores {
        if score.isValid {
            if let player = findPlayer(score.playerId) {
                if player.isActive {
                    var updatedPlayer = player
                    updatedPlayer.scores.append(score)
                    if updatedPlayer.scores.count > 10 {
                        updatedPlayer.scores = Array(
                            updatedPlayer.scores.suffix(10)
                        )
                    }
                    results.append(updatedPlayer)
                }
            }
        }
    }
    return results
}

PROBLEMS IDENTIFIED:
1. Deep nesting (4 levels) — hard to follow
2. Multiple responsibilities — validation, lookup, update, trim
3. Mutable state throughout
4. Magic number (10)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SIMPLIFIED (14 lines, 1 nesting level):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

private let maxScoreHistory = 10

func processScores(_ scores: [Score]) -> [Player] {
    scores
        .filter(\.isValid)
        .compactMap { score in
            guard var player = findPlayer(score.playerId),
                  player.isActive else { return nil }
            
            player.scores.append(score)
            player.scores = player.scores.suffix(maxScoreHistory)
            return player
        }
}

CHANGES MADE:
1. Replaced nested ifs with guard + filter
2. Used compactMap instead of manual array building
3. Extracted magic number to named constant
4. Reduced from 32 lines to 14
5. Single level of nesting

READABILITY IMPROVEMENT: 📈 60%

Apply this simplification?
A) Yes — apply changes
B) Keep original, just add the constant
C) Show me step-by-step refactoring
```

## Simplification Principles

1. **Flat over nested** — Guard clauses instead of deep ifs
2. **Declarative over imperative** — map/filter over for loops
3. **Named over magic** — Constants over hardcoded values
4. **Single responsibility** — One function, one job
5. **Readable over clever** — Clear beats concise

## How This Agent Thinks

The Code Simplifier asks:
1. Can I understand this at a glance?
2. How deep is the nesting?
3. Is this function doing too much?
4. Are there repeated patterns?
5. Would a new developer understand this?

## Related Commands

- `/project:code-review` — Identifies complexity issues
- `/agent:code-reviewer` — For bug-focused review
- `/framework-improve` — Capture simplification patterns
