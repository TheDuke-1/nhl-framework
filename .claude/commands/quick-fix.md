# /quick-fix Command

## What This Is

Fast, focused fix for a specific bug or small issue. No planning overhead, no full verification pipeline — just fix the problem and confirm it's resolved.

## How to Use

```
/quick-fix [describe the problem]
```

Or just:
```
/quick-fix
```
And Claude will ask what needs fixing.

## What Happens

1. **Understand:** Claude confirms the problem
2. **Locate:** Finds the relevant code
3. **Fix:** Makes the minimal change needed
4. **Verify:** Confirms the fix works
5. **Learn:** Logs the fix to LEARNINGS.md if it's a pattern worth remembering

## When to Use This

**Good for:**
- Bug that appeared after a recent change
- Small visual issues (color wrong, spacing off)
- Quick logic fixes (wrong calculation, typo)
- UI not matching spec

**Not good for:**
- Adding new features (use `/interview` instead)
- Major refactoring (use `/project:plan` instead)
- Unclear what's wrong (explain the problem first)

## Example Interaction

```
You: /quick-fix the score display is showing negative numbers which shouldn't happen

Claude: Understood — score display is showing negative numbers when it shouldn't.

Let me find where scores are displayed...

Found: ScoreView.swift, line 45

The issue: You're subtracting strokes from par but not handling the case where
strokes > par × 2 (which gives visual negative in this calculation).

Fix: Add a floor of 0 to prevent negative display.

Before:
let displayScore = par - strokes

After:  
let displayScore = max(0, par - strokes)

Applying fix...
✓ Fixed

Verification:
- Built successfully
- Score no longer shows negative (tested with strokes = 50, par = 4)

Want me to log this to LEARNINGS.md as a pattern to watch for?
```

## Rules This Command Follows

### Minimal Changes Only
- Fix the specific issue, don't refactor surrounding code
- If the fix needs larger changes, say so and suggest `/project:plan`

### Always Verify
- Build after the fix
- Test the specific case that was broken
- Confirm visually if it's a UI issue

### Capture Learnings
- Ask if this should be logged to LEARNINGS.md
- Route to appropriate CLAUDE.md if it's a rule worth adding

### Keep It Fast
- This command is for speed
- Don't over-engineer the solution
- Don't gold-plate adjacent code

## What's Different from /project:build

| /quick-fix | /project:build |
|------------|----------------|
| Fix one specific issue | Build from a spec |
| Minimal verification | Full verification pipeline |
| No planning phase | Follows a plan |
| Minutes, not hours | Scaled to task size |

## Related Commands

- `/project:verify` — Full verification if you want more thorough testing
- `/project:plan` — If the fix is bigger than expected
- `/framework-improve` — If this bug reveals a framework gap
