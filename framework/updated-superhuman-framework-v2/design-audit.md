# /design-audit Command

## What This Is

An interactive walkthrough of your existing views to extract current design patterns. Claude explores your codebase, shows you what it finds, and asks your opinion on each element. This is NOT just a report — it's a conversation.

## How to Use

Just type:
```
/design-audit
```

Claude will start exploring your project's views and walk through them with you.

## What Happens

1. **Discovery:** Claude finds all view files in your project
2. **Pattern Extraction:** Identifies colors, fonts, spacing, component styles
3. **Interactive Review:** Shows each finding and asks your opinion
4. **Inconsistency Detection:** Points out where patterns don't match
5. **Decision Capture:** Records what to keep, change, or standardize
6. **Audit Report:** Creates summary of current design state

## When to Run This

**For Existing Projects:** Run this BEFORE `/design-interview` to understand your current state.

**Workflow:**
```
/design-audit      # Extract what exists
/design-interview  # Formalize and fill gaps
/interview         # Feature interviews reference the system
```

## Example Interaction

```
You: /design-audit

Claude: I'll walk through your existing views and extract design patterns. 
Let me explore the codebase first.

Found 8 view files. Let's review them together.

═══════════════════════════════════════════════════════
VIEW 1: HomeView.swift
═══════════════════════════════════════════════════════

Current colors found:
- Primary green: #1B4D3E (used for headers, buttons)
- Gold accent: #D4AF37 (used for highlights, scores)
- Background: #F5F5F0 (off-white, cream tone)

Question: Do you want to KEEP these colors as your standard palette?

A) Yes — these are exactly what I want
B) Keep the green and gold, but change the background
C) I want to revise all of these
D) Let me see how they look in context first

You: A

Claude: Locked in: #1B4D3E (green), #D4AF37 (gold), #F5F5F0 (cream background).

Typography found:
- Titles: SF Pro Display, 28pt, semibold
- Body: SF Pro Text, 16pt, regular
- Captions: SF Pro Text, 12pt, regular

Question: Is this hierarchy working for you?
...
```

## Output

Creates an audit summary and prepares context for `/design-interview`:
- List of all colors currently in use (with locations)
- Typography patterns found
- Spacing patterns found
- Component styles identified
- Inconsistencies flagged
- Your decisions on what to keep/change

## Rules This Command Follows

### Interactive, Not Passive
- Don't just generate a report — walk through it together
- Ask opinion on EVERY significant finding
- Pause for confirmation before moving to next view

### Visual When Possible
- Show color swatches (hex codes aren't intuitive)
- Use Xcode previews to show actual rendered views
- Compare similar elements side-by-side

### Capture Decisions
- Record every "keep this" decision
- Record every "change this" decision with context
- Feed into DESIGN-DECISIONS.md

### Flag Inconsistencies
- "This view uses #1B4D3E but that view uses #1A4C3D — same green?"
- "Button radius is 8px here but 12px there — standardize?"
- Help identify unintentional drift

## What's Next

After the design audit:
```
/design-interview  # Formalize findings into complete system
```

## Related Commands

- `/design-interview` — Run after audit to establish formal system
- `/agent:design-system` — Call for design system architecture questions
- `/agent:visual-qa` — Call for detailed visual consistency checks
