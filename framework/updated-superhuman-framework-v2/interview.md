# /interview Command

## What This Is

A deep-dive conversation to capture exactly what you want for a feature. This command asks questions one at a time, with multiple choice options, until it has everything needed to write a complete specification.

## How to Use

Just type:
```
/interview
```

Claude will start asking questions about your feature. Answer naturally or pick from the options provided.

## What Happens

1. **Opening Question:** Claude asks what feature you want to build
2. **Feature Definition:** Questions about what it does, who it's for, why it matters
3. **UI Details:** Exact layout, every element, colors, typography, spacing
4. **Edge Cases:** What happens when things go wrong, empty states, error handling
5. **Data Model:** What information needs to be stored, relationships, persistence
6. **Integration Points:** How this connects to existing code
7. **Spec Generation:** Creates SPEC-[feature].md with everything captured

## Rules This Command Follows

### Interview Style
- One question at a time (never overwhelming)
- Multiple choice options when appropriate
- Accepts natural language answers
- Asks "What would the superhuman team require?" to surface best practices
- Never finishes until all four areas are covered (UI, edge cases, data, integration)

### Design Integration
- References DESIGN-SYSTEM.md if it exists
- UI questions specify exact design tokens to use
- Visual requirements are concrete, not vague

### Quality Standards
- Edge cases are comprehensive, not just happy path
- Data model is complete with all fields and relationships
- Integration points are explicit about dependencies

## Example Interaction

```
You: /interview

Claude: What feature would you like to build? Describe it however feels natural — 
we'll get into details through our conversation.

You: I want a leaderboard that shows top scores

Claude: Got it — a leaderboard for top scores. Let me understand this better.

Question 1: What type of scores are we tracking?

A) Individual round scores (like golf scores per game)
B) Cumulative scores (total points earned over time)
C) Win/loss records (games won vs lost)
D) Multiple score types that all appear together
E) Other — let me explain

You: A

Claude: Individual round scores, like golf. Makes sense for Links Ledger.

Question 2: How should players be ranked on this leaderboard?
...
```

## Output

Creates a file called `SPEC-[feature-name].md` containing:
- Feature summary
- Detailed UI specification with design token references
- Complete edge case coverage
- Data model with all fields
- Integration requirements
- Acceptance criteria checklist

## What's Next

After the interview completes:
```
/project:plan    # Create execution plan
/project:build   # Build the feature
/project:verify  # Test everything
```

## Related Commands

- `/design-interview` — Establish visual identity before feature interviews
- `/design-audit` — Extract patterns from existing code first
- `/project:spec` — Generate spec from existing notes (skip interview)
