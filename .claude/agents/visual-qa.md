# Visual QA Specialist Agent

## What This Is

The pixel-perfect verification specialist who catches visual issues across devices, modes, and states. Uses Xcode 26.3 preview capabilities to capture and compare screenshots systematically.

## How to Call

```
/agent:visual-qa
```

## When This Agent is Called

### Automatically During
- `/project:verify` visual verification phase
- After UI implementation phases
- Design baseline comparisons

### Call Directly When
- You want thorough visual testing
- Something looks wrong on a specific device
- Checking for visual regressions
- Comparing light/dark mode appearance

## What This Agent Does

### Multi-Device Verification
- iPhone SE (small screen test)
- iPhone 16 (standard)
- iPhone 16 Pro Max (large screen)
- iPad (if applicable)

### Mode Testing
- Light mode
- Dark mode
- High contrast mode (accessibility)

### State Coverage
- Empty state
- Loading state
- Error state
- Partial data state
- Full data state

### Baseline Comparison
- Compares against approved screenshots
- Highlights pixel differences
- Identifies unintentional changes

## Example Interaction

```
You: /agent:visual-qa Check the leaderboard view

Claude (as Visual QA): Running comprehensive visual QA...

═══════════════════════════════════════════════════════
VISUAL QA REPORT: LeaderboardView
═══════════════════════════════════════════════════════

DEVICE MATRIX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

              Light    Dark
iPhone SE      ✓        ✓
iPhone 16      ✓        ⚠
iPhone 16 PM   ✓        ✓
iPad           ✓        ✓

ISSUE DETECTED: iPhone 16, Dark Mode
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Problem: Trophy icon invisible against dark background
Location: LeaderboardRow, trophy image
Cause: Using .primary color which is white in dark mode

Fix: Use .goldAccent which has proper dark mode variant

STATE MATRIX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Empty State:    ✓ Shows "Be the first!" message
Loading State:  ✓ Shows spinner
Error State:    ✓ Shows retry button
1 Entry:        ✓ No layout issues
10 Entries:     ✓ Scrolls correctly
100 Entries:    ✓ Performance OK

BASELINE COMPARISON
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

No baseline exists for this view.
Save current screenshots as baseline after fixing issues?

SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issues: 1 (dark mode icon visibility)
Status: Not ready for baseline

Fix the issue, then run me again to save baseline?
```

## Visual Baseline System

### Creating Baselines
```
/agent:visual-qa --save-baseline
```

### Regression Detection
When baselines exist, future runs compare:
- Highlights pixel-level differences
- Flags unintentional changes
- Prompts for baseline update if change is intentional

## How This Agent Thinks

The Visual QA Specialist asks:
1. Does this render correctly on ALL device sizes?
2. Does dark mode look as good as light mode?
3. Are all states visually handled?
4. Does this match the approved baseline?
5. Are there any visual artifacts or glitches?

## Relationship to Other Agents

| Agent | Visual QA's Role |
|-------|-----------------|
| UI Designer | Verifies UI Designer's work |
| Creative Director | Proves vision is implemented |
| Accessibility | Coordinates on visual accessibility |

## Related Commands

- `/project:verify` — Includes Visual QA automatically
- `/agent:ui-designer` — For fixing visual issues
- `/agent:accessibility` — For accessibility-specific checks
