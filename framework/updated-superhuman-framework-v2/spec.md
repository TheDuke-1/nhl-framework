# /project:spec Command

## What This Is

Generates a specification file from interview notes or a description. Use this when you've already discussed a feature and just need it formatted as a spec, or when you want to write a spec directly.

## How to Use

```
/project:spec [feature-name]
```

Or with a description:
```
/project:spec leaderboard "Show top 10 players sorted by score"
```

## What Happens

1. **Gather Input:** Uses interview notes or your description
2. **Check Design System:** Incorporates DESIGN-SYSTEM.md requirements
3. **Structure Spec:** Formats into standard specification
4. **Gap Analysis:** Identifies any missing information
5. **Output:** Creates SPEC-[feature].md

## Spec Structure

```markdown
# Specification: [Feature Name]

## Summary
One-paragraph description of what this feature does.

## User Story
As a [user type], I want to [action] so that [benefit].

## UI Specification

### Layout
- Exact element positions
- Hierarchy and grouping
- Responsive behavior

### Design Tokens (from DESIGN-SYSTEM.md)
- Background: `cardBackground`
- Title: `titleText`, 24pt, semibold
- Body: `bodyText`, 16pt, regular
- Accent: `primaryAccent`

### States
1. Empty State: [description]
2. Loading State: [description]
3. Error State: [description]
4. Data State: [description]

## Data Model

### [ModelName]
| Property | Type | Description |
|----------|------|-------------|
| id | UUID | Unique identifier |
| name | String | Display name |
| ... | ... | ... |

### Relationships
- [Model] has many [OtherModel]
- [Model] belongs to [OtherModel]

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Empty data | Show empty state message |
| Network error | Show retry button |
| Invalid input | Show inline validation |
| ... | ... |

## Integration Points
- Connects to: [existing components]
- Modifies: [existing files]
- Depends on: [prerequisites]

## Acceptance Criteria
- [ ] User can [action]
- [ ] UI matches design system
- [ ] All edge cases handled
- [ ] Accessibility requirements met
- [ ] Tests pass
```

## Example Interaction

```
You: /project:spec leaderboard

Claude: I'll create a spec for the leaderboard feature.

Do you have interview notes, or should I ask some quick questions?

A) Use our interview notes from earlier
B) Ask me quick questions to fill gaps
C) I'll describe it — just format what I say

You: B

Claude: Quick questions to complete the spec:

1. How many players should appear on the leaderboard?
   A) Top 5
   B) Top 10
   C) Top 20
   D) Configurable

You: B

Claude: Top 10 players. 

2. What score type are we displaying?
...

[After questions]

Spec created: SPEC-leaderboard.md

Review summary:
- Shows top 10 players by round score
- Includes player name, score, date, game type
- Uses existing design tokens
- Handles empty state with encouragement message

Ready to plan?
/project:plan to create execution plan
```

## Difference from /interview

| /interview | /project:spec |
|------------|---------------|
| Deep exploration | Quick formatting |
| Many questions | Few questions |
| Discovers requirements | Documents known requirements |
| Creates spec as output | Creates spec as output |

Use `/interview` when you're still figuring out what you want.
Use `/project:spec` when you already know and just need it documented.

## Rules This Command Follows

### Always Check Design System
- Reference specific tokens, not generic descriptions
- Include exact values when relevant

### Complete All Sections
- Don't leave sections empty or "TBD"
- If information is missing, ask for it
- Spec should be buildable as-is

### Acceptance Criteria Are Testable
- Each criterion can be verified
- No vague language like "works well"
- Checkboxes that can be checked

## Related Commands

- `/interview` — Full interview process for complex features
- `/project:plan` — Create plan from spec
- `/project:build` — Build from spec
