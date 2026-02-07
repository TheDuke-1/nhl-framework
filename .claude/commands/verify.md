# /project:verify Command

## What This Is

Full verification pipeline: code tests, visual checks, multi-device testing, accessibility audit, and design review. This is how bugs get caught BEFORE you see them.

## How to Use

```
/project:verify [scope]
```

Scope options:
- `full` — Complete verification (default)
- `visual` — Just visual/UI testing
- `code` — Just code tests
- `accessibility` — Just accessibility audit

Or just:
```
/project:verify
```
For full verification.

## What Happens

### 1. Code Verification
- Run existing test suite
- Check for compilation errors
- Static analysis for common issues

### 2. Visual Verification (Using Xcode 26.3 Previews)
- Capture screenshots of all affected views
- Check multiple device sizes:
  - iPhone SE (small)
  - iPhone 16 (standard)
  - iPhone 16 Pro Max (large)
  - iPad (if applicable)
- Verify light AND dark mode
- Compare against baseline (if exists)

### 3. State Verification
- Empty state (no data)
- Loading state
- Error state
- Full data state
- Edge cases from spec

### 4. Design Review
- Compare against DESIGN-SYSTEM.md
- Check colors match tokens
- Verify typography scale
- Confirm spacing consistency

### 5. Accessibility Audit
- VoiceOver labels present
- Dynamic Type scaling
- Color contrast ratios
- Touch targets sized appropriately

### 6. Verification Report
- Summary of all findings
- Issues categorized by severity
- Recommendations for fixes

## Example Interaction

```
You: /project:verify

Claude: Running full verification pipeline...

═══════════════════════════════════════════════════════
VERIFICATION: Leaderboard Feature
═══════════════════════════════════════════════════════

CODE TESTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ 12 tests passed
✓ No compilation warnings
✓ No force unwraps detected

VISUAL VERIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Capturing previews...

iPhone SE (Light):     ✓ Renders correctly
iPhone SE (Dark):      ✓ Renders correctly
iPhone 16 (Light):     ✓ Renders correctly
iPhone 16 (Dark):      ⚠ Issue detected
iPhone 16 Pro Max:     ✓ Renders correctly
iPad:                  ✓ Renders correctly

Issue Found:
━━━━━━━━━━━━━━━━━━━━━━━━
Device: iPhone 16 (Dark mode)
Problem: Gold accent (#D4AF37) has low contrast against dark background
Location: Score labels in LeaderboardRow
Severity: Medium

Recommendation: Use goldAccentDark (#E5C158) for dark mode
Reference: DESIGN-SYSTEM.md line 45

STATE VERIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Empty state shows "No scores yet" message
✓ Loading state shows spinner
✓ Error state shows retry button
✓ Full data (100 entries) renders without lag

DESIGN SYSTEM COMPLIANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Colors match design tokens
✓ Typography follows scale
⚠ Spacing: 12px used but system specifies 16px (minor)

ACCESSIBILITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ VoiceOver labels present
✓ Dynamic Type scales correctly
✓ Contrast ratios pass WCAG AA
✓ Touch targets ≥ 44pt

═══════════════════════════════════════════════════════
SUMMARY
═══════════════════════════════════════════════════════

Issues Found: 2
- 1 Medium (dark mode contrast)
- 1 Minor (spacing variance)

Recommendation: Fix dark mode contrast before shipping.

Fix these issues now?
A) Yes — fix all issues
B) Fix just the medium issue
C) Show me the issues in detail first
D) Skip — I'll fix later
```

## Visual Baseline System

### Creating Baselines
After you approve a design:
```
/project:verify --save-baseline
```
This saves current screenshots as the "approved" state.

### Regression Detection
Future verifications compare against baselines:
- Pixel differences highlighted
- Unintentional changes flagged
- Intentional changes prompt baseline update

## Agents Invoked

| Stage | Agent | Purpose |
|-------|-------|---------|
| Visual | Visual QA Specialist | Pixel-perfect checks |
| Design | UI Designer | Design compliance |
| Design | Creative Director | Brand consistency |
| Accessibility | Accessibility Expert | A11y audit |
| Code | Code Reviewer | Test coverage |

## Rules This Command Follows

### Never Skip Visual Verification
- Code passing tests ≠ UI looks correct
- Screenshots are proof
- Check ALL device sizes

### Always Check Both Modes
- Light mode AND dark mode
- Colors that work in light often fail in dark
- Test semantic colors specifically

### Handle All States
- Empty is just as important as full
- Error states need love too
- Loading states should feel responsive

### Be Specific About Issues
- Exact location (file, line, element)
- Exact problem (not "looks wrong")
- Exact fix (what to change)

### Feed Into Learning System
- Issues found become potential learnings
- Patterns that catch bugs become rules
- Visual baselines evolve over time

## What's Next

After verification:
```
/project:code-review     # Deep code review
/project:commit-push-pr  # Ship it
/framework-improve       # Capture learnings
```

## Related Commands

- `/project:build` — Build before verifying
- `/project:code-review` — Deeper code analysis
- `/agent:visual-qa` — Focused visual QA session
- `/agent:accessibility` — Focused accessibility audit
