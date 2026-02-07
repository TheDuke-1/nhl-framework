# /design-interview Command

## What This Is

A deep conversation to establish your app's visual identity. This creates the foundation that all feature interviews reference. Run this ONCE per project to set up your design system.

## How to Use

Just type:
```
/design-interview
```

Claude will guide you through questions about aesthetics, colors, typography, spacing, and design references.

## What Happens

1. **Vision Capture:** What feeling do you want the app to evoke?
2. **Reference Apps:** What apps do you love the look of? What do you hate?
3. **Color Philosophy:** Primary colors, accents, meanings behind choices
4. **Typography:** Font preferences, hierarchy, readability priorities
5. **Spacing & Layout:** Dense vs airy, how content should breathe
6. **Component Style:** Buttons, cards, inputs — rounded vs sharp, depth vs flat
7. **Anti-Patterns:** What explicitly to avoid (generic, corporate, cluttered)
8. **Design System Generation:** Creates DESIGN-SYSTEM.md

## When to Run This

**For New Projects:** Run before your first `/interview`. Design foundation first, then features.

**For Existing Projects:** Run `/design-audit` first to extract current patterns, THEN run `/design-interview` to formalize and fill gaps.

## Example Interaction

```
You: /design-interview

Claude: Let's establish the visual identity for your app. I'll ask questions 
one at a time to understand your design vision.

Question 1: What feeling should someone have when they open your app?

A) Professional and trustworthy (like a bank or productivity tool)
B) Fun and energetic (like a game or social app)
C) Premium and sophisticated (like a luxury brand)
D) Clean and minimal (like Apple's design language)
E) Warm and personal (like a lifestyle or wellness app)
F) Other — let me describe the feeling

You: C and D combined — premium and sophisticated but also clean

Claude: Premium sophistication with clean minimalism. That's a refined taste.

Question 2: Name 2-3 apps whose visual design you admire. What specifically 
do you like about them?
...
```

## Output

Creates `DESIGN-SYSTEM.md` containing:
- Design philosophy and principles
- Color palette with specific hex values and usage rules
- Typography scale with fonts, sizes, weights
- Spacing system (base unit, standard margins/padding)
- Component specifications (buttons, cards, inputs, etc.)
- Anti-patterns to avoid
- Reference images/apps for context

## Rules This Command Follows

### Never Accept Vague Answers
- "I want it to look nice" → Ask what "nice" means specifically
- "Modern design" → Ask for examples of what modern looks like to you
- "Clean" → Ask what clean means (whitespace? minimal colors? simple shapes?)

### Extract Principles
- When you approve something, capture WHY you like it
- When you reject something, capture what specifically to avoid
- Build a vocabulary of your design taste

### Connect to Reality
- Reference real apps and designs
- Ask for screenshots or links when helpful
- Compare options visually when possible

## What's Next

After the design interview:
```
/interview       # Now feature interviews reference your design system
/project:plan    # Plans include visual requirements
/project:build   # Builds follow design tokens
```

## Related Commands

- `/design-audit` — Extract patterns from existing code first
- `/interview` — Feature interviews that reference this design system
- `/agent:creative-director` — Call for design vision review anytime
