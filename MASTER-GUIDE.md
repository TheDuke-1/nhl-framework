# Superhuman Framework V2 — Master Guide

## What This Is

This is your complete system for building apps with Claude Code at a superhuman level. The framework is designed so Claude can one-shot entire features (or even entire projects) while you focus on vision and decisions instead of debugging.

**The Philosophy:** You describe what you want in plain English. Claude builds it, tests it, verifies it looks right, and learns from every interaction. Over time, the framework gets smarter — your projects start at 90% quality on day one because everything Claude learned flows into templates.

---

## Quick Reference Card

### Global Commands (Type These Anywhere)
| Command | What It Does |
|---------|--------------|
| `/interview` | Deep-dive conversation to capture exactly what you want for a feature |
| `/design-interview` | Establish your app's visual identity, colors, typography, aesthetic preferences |
| `/design-audit` | Walk through existing views together to extract current design patterns |
| `/quick-fix` | Fast fix for a specific bug or small issue (no planning overhead) |
| `/framework-improve` | Review the session and extract learnings into the framework |
| `/session-start` | Resume work with full context from where you left off |
| `/session-end` | Clean handoff — saves state and summarizes what happened |

### Project Commands (Type `/project:command`)
| Command | What It Does |
|---------|--------------|
| `/project:plan` | Create an execution plan for implementing a spec |
| `/project:build` | Execute the plan and build the feature |
| `/project:verify` | Full verification: tests, visual checks, multi-device, light/dark mode |
| `/project:spec` | Generate a spec file from interview notes |
| `/project:code-review` | Deep review focusing on bugs, patterns, and improvement opportunities |
| `/project:commit-push-pr` | Git autopilot: branch, commit, push, and create PR |
| `/project:status` | Dashboard showing current state: files, progress, blockers |

### Agent Commands (Type `/agent:name`)
| Agent | What It Does |
|-------|--------------|
| `/agent:creative-director` | Guards the design vision, ensures brand consistency |
| `/agent:ui-designer` | Focuses on aesthetics: colors, typography, polish |
| `/agent:ux-designer` | Flows, usability, information architecture |
| `/agent:visual-qa` | Pixel-perfect verification across devices |
| `/agent:accessibility` | VoiceOver, Dynamic Type, contrast ratios |
| `/agent:motion-designer` | Animations, micro-interactions, transitions |
| `/agent:design-system` | Maintains tokens, components, documentation |
| `/agent:code-reviewer` | Finds bugs, bad patterns, security issues |
| `/agent:code-simplifier` | Reduces complexity, improves readability |
| `/agent:test-engineer` | Creates and runs comprehensive tests |
| `/agent:verify-app` | End-to-end testing, all states, all paths |
| `/agent:framework-improver` | Extracts learnings, improves rules |
| `/agent:spec-builder` | Creates comprehensive specifications |

---

## How the System Works

### The Core Loop

```
1. INTERVIEW → Capture exactly what you want (feature + design + edge cases)
       ↓
2. PLAN → Claude creates step-by-step execution plan
       ↓
3. BUILD → Claude implements with checkpoints for visibility
       ↓
4. VERIFY → Full testing: code, visual, accessibility, all states
       ↓
5. REVIEW → Design and code review by specialist agents
       ↓
6. LEARN → Extract learnings, update rules, improve templates
       ↓
7. COMMIT → Git autopilot handles branches, commits, PRs
```

### What Makes It "Superhuman"

**Learning System:** Every bug fixed, every design approved, every pattern discovered gets captured and routed to the right place:
- Project-specific learnings → your project's CLAUDE.md
- Universal patterns → global CLAUDE.md
- Full context → LEARNINGS.md (searchable history)
- Design decisions → DESIGN-DECISIONS.md (taste memory)
- Templates → GitHub template repo (new projects start smarter)

**Visual Testing Pipeline:** Using Xcode 26.3's preview capture:
- Multi-device screenshots (iPhone SE → Pro Max → iPad)
- Light/dark mode verification
- All states: empty, loading, error, full data
- Baseline comparisons to catch visual regressions
- Design review by specialist agents (not just "does it work" but "does it look premium")

**Earned Autonomy:** Claude starts with checkpoints at every stage. As it earns your trust through successful builds:
- Stage 1: Checkpoint approval at every design decision
- Stage 2: Final approval only (intermediate steps autonomous)
- Stage 3: Full autonomy with escalation for edge cases

---

## Installation

### Step 1: Install Global Commands

Copy the `global/commands/` folder to your Claude Code global commands location:

**macOS:**
```bash
cp -r global/commands/* ~/.claude/commands/
```

**Windows:**
```powershell
Copy-Item -Recurse global\commands\* $env:USERPROFILE\.claude\commands\
```

After this, commands like `/interview`, `/design-interview`, `/quick-fix` work anywhere.

### Step 2: Set Up Your Global CLAUDE.md

Copy `global/CLAUDE.md` to your global Claude settings:

```bash
cp global/CLAUDE.md ~/.claude/CLAUDE.md
```

This contains universal rules that apply to all your projects.

### Step 3: For Each New Project

Copy the `template/` folder contents into your project's `.claude/` directory:

```bash
# From your project root:
cp -r /path/to/superhuman-framework-v2/template/.claude .
cp /path/to/superhuman-framework-v2/template/CLAUDE.md .
cp /path/to/superhuman-framework-v2/template/*.md .
```

This gives you:
- Project-specific commands (`/project:plan`, `/project:build`, etc.)
- All 13 agents ready to use
- Template CLAUDE.md to customize
- DESIGN-SYSTEM.md to fill in
- LEARNINGS.md for session history
- DESIGN-DECISIONS.md for taste memory

### Step 4: For SwiftUI Projects (Optional)

If building iOS/macOS apps with SwiftUI, also copy the SwiftUI-specific files:

```bash
cp -r /path/to/superhuman-framework-v2/swiftui/.claude/* .claude/
cp /path/to/superhuman-framework-v2/swiftui/CLAUDE.md ./CLAUDE-SWIFTUI.md
```

Then add this to your project's CLAUDE.md:
```markdown
<!-- Include SwiftUI-specific rules -->
See CLAUDE-SWIFTUI.md for SwiftUI patterns and requirements.
```

---

## Your First Session

### For a New Project

1. **Run the Design Interview First**
   ```
   /design-interview
   ```
   This establishes your visual identity: colors, typography, spacing, aesthetic preferences, reference apps you love/hate. Creates `DESIGN-SYSTEM.md`.

2. **Then Interview for Your First Feature**
   ```
   /interview
   ```
   Deep conversation about what you want. Covers functionality, UI details, edge cases, data model. Creates `SPEC-[feature].md`.

3. **Build It**
   ```
   /project:plan
   /project:build
   /project:verify
   ```
   Claude plans, executes, and verifies — with visibility at each checkpoint.

### For an Existing Project

1. **Start with a Design Audit**
   ```
   /design-audit
   ```
   Claude walks through your existing views with you, extracts current patterns, identifies inconsistencies. Interactive — not just a report.

2. **Then the Design Interview**
   ```
   /design-interview
   ```
   Review audit findings, confirm what to keep, change what you don't like, fill gaps. Creates `DESIGN-SYSTEM.md`.

3. **Continue with Features**
   ```
   /interview
   /project:plan
   /project:build
   /project:verify
   ```

---

## What Each File Does

### In Your Project Root

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Rules and context for this specific project |
| `DESIGN-SYSTEM.md` | Visual identity: colors, typography, spacing, components |
| `LEARNINGS.md` | Full history of what Claude learned (searchable) |
| `DESIGN-DECISIONS.md` | Record of design approvals/rejections with context |
| `SESSION-STATE.md` | Auto-saved state for resuming work across sessions |
| `SPEC-[feature].md` | Detailed specifications for each feature |

### In .claude/commands/

| File | Purpose |
|------|---------|
| `plan.md` | Instructions for how `/project:plan` works |
| `build.md` | Instructions for how `/project:build` works |
| `verify.md` | Instructions for how `/project:verify` works |
| `spec.md` | Instructions for how `/project:spec` works |
| `code-review.md` | Instructions for how `/project:code-review` works |
| `commit-push-pr.md` | Git autopilot instructions |
| `status.md` | Dashboard generation instructions |

### In .claude/agents/

Each agent file contains the specialist's role, expertise, and instructions. Agents are both auto-invoked during workflows AND directly callable via `/agent:name`.

---

## Git Autopilot

Claude handles Git almost entirely. Here's what to expect:

**Before Major Operations:** Claude asks for confirmation:
> "I'm about to create a branch called 'feature/add-leaderboard'. Think of a branch like a draft copy where we can experiment safely. 👍 to proceed?"

**Teaches As It Goes:** Plain English explanations build your understanding over time.

**Session-End Summary:**
```
GIT ACTIVITY THIS SESSION
═════════════════════════
Branch: feature/add-leaderboard (created)
Commits: 3
  • Initial leaderboard UI implementation
  • Add score calculation logic
  • Fix dark mode colors
Status: Ready to merge (all tests passing)
```

---

## Visibility System

Claude provides visibility scaled to task complexity:

**For Small Tasks:** Light updates
```
✓ Fixed the color issue in ScoreView.swift
```

**For Large Tasks:** Dashboard + Checkpoints
```
SESSION STATUS
══════════════════════════════════════
Task: Add leaderboard feature
Phase: Building (2/4)
Files Modified: GameModel.swift, LeaderboardView.swift
Files Remaining: 2
Current: Implementing sort logic
Blockers: None
══════════════════════════════════════

Phase 1 complete: Data model ready.
Moving to Phase 2: UI implementation.
Questions before I continue?
```

---

## Troubleshooting

### "I don't see my commands"

Commands must be in the correct location:
- Global commands: `~/.claude/commands/` (called as `/commandname`)
- Project commands: `your-project/.claude/commands/` (called as `/project:commandname`)

Check: `ls ~/.claude/commands/` should show your global commands.

### "Claude isn't following the rules"

Make sure CLAUDE.md is in the right place:
- Global rules: `~/.claude/CLAUDE.md`
- Project rules: `your-project/CLAUDE.md`

Claude reads both files — global rules apply everywhere, project rules are additive.

### "The session feels degraded"

After ~30 exchanges or when Claude seems to lose context, start fresh:
```
/session-end
```
Then start a new chat and run:
```
/session-start
```
This loads saved state from `SESSION-STATE.md`.

---

## Success Criteria

The framework is working when:
- [ ] You describe features in plain English → Claude one-shots them
- [ ] UI looks premium without tweaking
- [ ] Bugs get caught before you see them
- [ ] The framework gets smarter every week
- [ ] You spend time on decisions, not debugging
- [ ] New projects start at 90% quality

---

## Need Help?

- **Quick issues:** Use `/quick-fix` for fast, focused fixes
- **Framework problems:** Use `/framework-improve` to analyze what went wrong
- **Starting fresh:** Use `/session-end` then `/session-start` in a new chat

Remember: The goal is Claude handles the work, you handle the vision. If you're debugging more than deciding, something in the workflow needs adjustment.
