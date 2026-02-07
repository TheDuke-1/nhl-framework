# SUPERHUMAN FRAMEWORK V2 — MASTER GUIDE

> **What This Is:** Your complete playbook for the Superhuman Claude Code Framework. This guide explains everything: what each file does, how all the pieces work together, and how to use the system to build projects at a superhuman level.

> **Who This Is For:** A smart professional who wants to leverage AI for coding without needing to understand programming deeply. Everything is explained in plain English.

---

## TABLE OF CONTENTS

1. [The Big Picture](#the-big-picture)
2. [Core Philosophy](#core-philosophy)
3. [How The Framework Is Organized](#how-the-framework-is-organized)
4. [The Command System](#the-command-system)
5. [The Agent Organization](#the-agent-organization)
6. [The Learning System](#the-learning-system)
7. [The Design System](#the-design-system)
8. [Workflows — How To Actually Use This](#workflows)
9. [Session Management](#session-management)
10. [Git Autopilot](#git-autopilot)
11. [File Reference — Every File Explained](#file-reference)
12. [Glossary — Technical Terms Defined](#glossary)

---

## THE BIG PICTURE

### What Is This Framework?

This framework is a set of rules, commands, and AI agents that make Claude Code work at a "superhuman" level — meaning:

- You describe what you want in plain English
- Claude builds it correctly the first time (one-shot)
- The code is high quality, well-tested, and beautiful
- Mistakes are caught automatically before you see them
- The system learns from every project, getting smarter over time
- New projects start at 90% quality because they inherit past learnings

### The Core Promise

**You handle the vision. Claude handles the work.**

Your job is to:
- Decide what you want to build
- Answer Claude's interview questions
- Approve or give feedback on results
- Make business/creative decisions

Claude's job is to:
- Ask the right questions to understand your vision
- Write high-quality code
- Test everything thoroughly
- Catch and fix bugs before you see them
- Make the UI look premium without you tweaking
- Learn from mistakes so they never happen again
- Manage all the technical details (Git, files, builds, etc.)

---

## CORE PHILOSOPHY

### 1. Planning Beats Improvising

A 30-minute interview saves 3 hours of back-and-forth fixing. The framework front-loads the thinking so execution is smooth.

### 2. One-Shot Is The Goal

Every spec should be detailed enough that Claude can build it correctly in one attempt. If Claude needs to ask clarifying questions during building, the spec wasn't good enough.

### 3. Quality Is Testable

"Looks good" isn't enough. Quality means:
- Code compiles without errors
- Tests pass
- UI looks correct on all devices, in light/dark mode, in all states
- Design matches the established system
- Code is clean and simple

The framework tests ALL of these automatically.

### 4. Learning Compounds

Every mistake fixed becomes a rule that prevents future mistakes. Every preference expressed becomes a pattern Claude follows. The framework gets smarter with every session.

### 5. Earned Autonomy

Early on, Claude checks in frequently to learn your preferences. As trust is established, Claude works more independently, only escalating when uncertain.

---

## HOW THE FRAMEWORK IS ORGANIZED

### Three Layers

```
┌─────────────────────────────────────────────────────────┐
│  GLOBAL LAYER (~/.claude/)                              │
│  Rules and commands that apply to ALL your projects     │
│  Examples: /interview, /quick-fix, /session-start       │
└─────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│  PROJECT LAYER (your-project/.claude/)                  │
│  Rules, commands, and agents for THIS specific project  │
│  Examples: /project:build, /project:verify, agents      │
└─────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│  TECH-SPECIFIC LAYER (optional overlays)                │
│  Additional rules for specific technologies             │
│  Examples: SwiftUI rules, React rules, Python rules     │
└─────────────────────────────────────────────────────────┘
```

### What Lives Where

| Location | What It Contains | When It's Used |
|----------|------------------|----------------|
| `~/.claude/CLAUDE.md` | Universal rules for all projects | Every Claude Code session |
| `~/.claude/commands/` | Global commands like `/interview` | Any project |
| `project/.claude/CLAUDE.md` | Project-specific rules + design system | This project only |
| `project/.claude/commands/` | Project commands like `/project:build` | This project only |
| `project/.claude/agents/` | Specialist AI agents | Called during workflows |
| `project/DESIGN-SYSTEM.md` | Visual design rules | UI-related work |
| `project/LEARNINGS.md` | Accumulated wisdom | Referenced during building |
| `project/DESIGN-DECISIONS.md` | History of design choices | Autonomy progression |

---

## THE COMMAND SYSTEM

### What Are Commands?

Commands are shortcuts that trigger specific workflows. Instead of typing long instructions, you type a short command like `/interview` and Claude knows exactly what to do.

### Global Commands (Work Everywhere)

These live in `~/.claude/commands/` and work in any project:

| Command | What It Does | When To Use |
|---------|--------------|-------------|
| `/interview` | Asks 40-75 questions to deeply understand what you want to build | Starting a new feature or project |
| `/design-interview` | Deep dive on visual identity, colors, typography, design preferences | Establishing or refining design system |
| `/design-audit` | Walks through existing views, asks your opinion, documents current state | First time setting up framework on existing project |
| `/quick-fix` | Fast workflow for small bugs or tweaks | Something small is broken |
| `/framework-improve` | Reviews recent sessions and suggests framework improvements | End of week or after major milestones |
| `/session-start` | Loads previous session state, asks what you want to work on | Beginning of any session |
| `/session-end` | Saves state, summarizes progress, prepares clean handoff | Ending any session |

### Project Commands (Specific To Each Project)

These live in `project/.claude/commands/` and are called with the `/project:` prefix:

| Command | What It Does | When To Use |
|---------|--------------|-------------|
| `/project:plan` | Creates implementation plan from a spec or request | Before building anything |
| `/project:build` | Executes a plan or builds from a spec | After plan is approved |
| `/project:verify` | Runs full verification pipeline (build, test, visual, review) | After building |
| `/project:visual-verify` | Captures and analyzes UI in Xcode previews | Checking UI quality |
| `/project:commit-push-pr` | Git Autopilot: commits, pushes, creates PR | Ready to save/share work |
| `/project:status` | Shows current state: branch, changes, progress | When you want visibility |
| `/project:code-review` | Gets code reviewed by Code Reviewer agent | Want feedback on code |

### Agent Commands (Call Specialists Directly)

These call specific specialist agents:

| Command | What It Does | When To Use |
|---------|--------------|-------------|
| `/agent:creative-director` | Reviews overall design vision and consistency | Design direction questions |
| `/agent:ui-designer` | Focuses on visual aesthetics | Styling specific components |
| `/agent:ux-designer` | Reviews usability and user flows | Flow and interaction questions |
| `/agent:visual-qa` | Pixel-perfect verification | Checking precise alignment |
| `/agent:accessibility` | Checks VoiceOver, Dynamic Type, contrast | Accessibility review |
| `/agent:code-reviewer` | Reviews code for bugs, patterns, security | Code quality check |
| `/agent:code-simplifier` | Reduces complexity, improves readability | Code is working but messy |
| `/agent:test-engineer` | Creates and improves tests | Need better test coverage |

---

## THE AGENT ORGANIZATION

### What Are Agents?

Agents are specialists — like having a team of experts who each focus on one area. Instead of Claude being a generalist, agents let Claude "put on different hats" with specific expertise and evaluation criteria.

### The Design Studio

Think of this as your creative agency:

| Agent | Role | Expertise |
|-------|------|-----------|
| **Creative Director** | Guards the overall vision | Brand consistency, design direction, final approval |
| **UI Designer** | Makes things look beautiful | Color, typography, spacing, shadows, polish |
| **UX Designer** | Makes things work well | User flows, usability, tap targets, information architecture |
| **Visual QA Specialist** | Catches every visual defect | Pixel alignment, consistency across states/devices |
| **Accessibility Expert** | Ensures everyone can use it | VoiceOver, Dynamic Type, color contrast |
| **Motion Designer** | Brings the UI to life | Animations, transitions, micro-interactions |
| **Design System Architect** | Maintains consistency at scale | Design tokens, component patterns, documentation |

### The Code Team

Think of this as your engineering department:

| Agent | Role | Expertise |
|-------|------|-----------|
| **Code Reviewer** | Finds problems in code | Bugs, security issues, anti-patterns |
| **Code Simplifier** | Makes code cleaner | Reducing complexity, improving readability |
| **Test Engineer** | Ensures code works | Creating tests, improving coverage |
| **Verify App** | End-to-end testing | Full application testing |

### The Framework Team

These agents improve the framework itself:

| Agent | Role | Expertise |
|-------|------|-----------|
| **Framework Improver** | Makes the system smarter | Extracting learnings, updating rules |
| **Spec Builder** | Creates detailed specifications | Interview synthesis, comprehensive specs |

### How Agents Work Together

**During a typical `/project:verify`:**

1. Build Check → Basic compilation test
2. Test Suite → Test Engineer runs and evaluates tests
3. Visual Preview → Visual QA Specialist checks all states/modes/devices
4. Design Review → UI Designer evaluates aesthetics against design system
5. Code Review → Code Reviewer checks for bugs and issues
6. Code Simplification → Code Simplifier looks for ways to clean up
7. Report → All findings compiled into one summary

**You see:** A single status report
**Behind the scenes:** A full team evaluated the work

---

## THE LEARNING SYSTEM

### The Problem This Solves

Without a learning system:
- Claude makes the same mistakes repeatedly
- Every new project starts from zero
- Your preferences have to be re-explained constantly
- Good patterns get forgotten

### How Learning Works

```
┌─────────────────────────────────────────────────────────┐
│  SOMETHING HAPPENS                                      │
│  (Bug fixed, preference expressed, mistake made)        │
└─────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│  SMART ROUTING DECISION                                 │
│  Is this project-specific or universal?                 │
└─────────────────────────────────────────────────────────┘
            ▼                           ▼
┌─────────────────────┐     ┌─────────────────────────────┐
│  PROJECT-SPECIFIC   │     │  UNIVERSAL                  │
│  Goes to project's  │     │  Goes to global CLAUDE.md   │
│  CLAUDE.md          │     │  AND updates template       │
└─────────────────────┘     └─────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│  LEARNINGS.md                                           │
│  Full context saved (what happened, when, what fixed)   │
└─────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│  TEMPLATE EVOLUTION                                     │
│  Universal patterns update your GitHub template         │
│  New projects inherit all past learnings                │
└─────────────────────────────────────────────────────────┘
```

### Example Learning Flow

1. **Bug Found:** Claude creates a SwiftData model that crashes because it deletes a property without a migration
2. **Fix Applied:** Claude adds the migration
3. **Learning Captured:** "SwiftData model changes require migration for existing user data"
4. **Routing:** This is SwiftUI/SwiftData specific → goes to project CLAUDE.md
5. **LEARNINGS.md:** Full context saved with date, what broke, how it was fixed
6. **Template Check:** Not universal enough for global template
7. **Result:** This project will never have this bug again, and Claude can reference the learning if a similar situation arises

### The Files Involved

| File | Purpose | How It's Used |
|------|---------|---------------|
| `LEARNINGS.md` | Detailed log of everything learned | Searchable history, periodic review |
| `project/CLAUDE.md` | Active rules Claude follows | Checked every response |
| `~/.claude/CLAUDE.md` | Universal rules for all projects | Checked every response |
| `template/CLAUDE.md` | Starting point for new projects | Copied when creating new project |

---

## THE DESIGN SYSTEM

### Why Design Needs Its Own System

Code either works or it doesn't — easy to test. But design is subjective. "Does this look premium?" can't be answered by running a test.

The design system solves this by:
1. **Capturing your taste** — Through interviews and feedback
2. **Documenting standards** — In DESIGN-SYSTEM.md
3. **Tracking decisions** — In DESIGN-DECISIONS.md
4. **Testing against standards** — Design Review Agent compares output to documented system
5. **Learning over time** — Feedback improves future outputs

### Design System Components

**DESIGN-SYSTEM.md contains:**
- Philosophy — The overall feel ("premium golf app, not mini-golf scorecard")
- Color Palette — Exact colors with hex codes and when to use each
- Typography — Fonts, sizes, weights for each use case
- Spacing — Base units and how to apply them
- Component Styles — Corner radius, shadows, button styles, card styles
- Anti-Patterns — What to never do ("no gradient backgrounds")

**DESIGN-DECISIONS.md contains:**
- Approval History — "Approved scorecard layout because it feels clean"
- Rejection History — "Rejected button style because too flat"
- Reference Comparisons — "This looks like Dark Sky weather app which I love"
- Extracted Principles — "Matt prefers depth over flat design"
- Visual Evidence — Links to screenshots of approved/rejected designs
- Autonomy Scores — Track record per agent

### The Earned Autonomy System

**Phase 1 — Learning (First 2-4 weeks):**
- Claude shows checkpoints frequently
- Every approval/rejection teaches the system your taste
- Design system document gets refined

**Phase 2 — Calibrated (After design system is solid):**
- Claude iterates internally
- You only see final output
- Rejections are rare because system knows your taste

**Phase 3 — Proven (Mature system):**
- Claude ships confidently
- Only escalates when uncertain or when stakes are high
- You're interrupted rarely

### The Design Workflow

```
PROJECT START
     ▼
┌─────────────────────────────────────────────────────────┐
│  /design-audit (for existing projects)                  │
│  Claude explores existing views, walks through each     │
│  with you, documents current patterns                   │
└─────────────────────────────────────────────────────────┘
     ▼
┌─────────────────────────────────────────────────────────┐
│  /design-interview                                      │
│  Deep questions about visual identity, preferences,     │
│  reference apps, anti-patterns                          │
│  OUTPUT: DESIGN-SYSTEM.md                               │
└─────────────────────────────────────────────────────────┘
     ▼
FEATURE BUILDING
     ▼
┌─────────────────────────────────────────────────────────┐
│  /project:build                                         │
│  ┌─────────────────┐                                    │
│  │ Checkpoint 1    │ Structure review                   │
│  │ Checkpoint 2    │ Component styling review           │
│  │ Checkpoint 3    │ Full view review (all states)      │
│  │ Checkpoint 4    │ Design diff (if changing existing) │
│  └─────────────────┘                                    │
└─────────────────────────────────────────────────────────┘
     ▼
┌─────────────────────────────────────────────────────────┐
│  /project:verify                                        │
│  Design Review Agent evaluates against DESIGN-SYSTEM.md │
│  Compares to reference images if available              │
│  Checks all devices, modes, states                      │
└─────────────────────────────────────────────────────────┘
     ▼
┌─────────────────────────────────────────────────────────┐
│  YOUR FEEDBACK                                          │
│  "Love it" → Captured in DESIGN-DECISIONS.md            │
│  "Too generic" → Captured + principle extracted         │
│  Updates DESIGN-SYSTEM.md, informs future work          │
└─────────────────────────────────────────────────────────┘
```

---

## WORKFLOWS

### Workflow 1: Small Quick Fix

**When:** Something small is broken or needs a tweak

```
You: /quick-fix The score total is wrong on the leaderboard

Claude:
1. Understands the issue
2. Creates minimal plan
3. Makes the fix
4. Runs quick verification
5. Shows you the result
6. Commits if approved
```

**Time:** 5-15 minutes

---

### Workflow 2: Medium Feature

**When:** Adding a new feature or making significant changes

```
SESSION 1:
You: /interview I want to add a feature that shows player handicap trends over time

Claude:
- Asks 30-50 questions about the feature
- Covers UI details, edge cases, data model, integration
- OUTPUT: SPEC-handicap-trends.md

SESSION 2 (new session for clean context):
You: /project:build @SPEC-handicap-trends.md

Claude:
- Reads the spec
- Shows implementation plan (checkpoints)
- Builds with visibility into progress
- Runs verification automatically
- Shows you the result

You: /project:commit-push-pr
Claude: Creates commit, pushes, makes PR, explains what happened
```

**Time:** 1-3 hours total

---

### Workflow 3: Large Feature / New Project

**When:** Major new functionality or starting from scratch

```
SESSION 1 — DESIGN FOUNDATION:
You: /design-interview

Claude:
- Deep questions about visual identity
- References, preferences, anti-patterns
- OUTPUT: DESIGN-SYSTEM.md

SESSION 2 — FEATURE SPEC:
You: /interview [describe the feature]

Claude:
- 40-75 questions
- UI details, edge cases, data model, integration
- References design system
- OUTPUT: SPEC-[feature].md

SESSION 3+ — BUILDING (may span multiple sessions):
You: /project:build @SPEC-[feature].md

Claude:
- Builds incrementally
- Checkpoints for approval
- Full verification after each major piece
- Learns from your feedback

COMPLETION:
You: /project:verify (full final check)
You: /project:commit-push-pr
You: /session-end
```

**Time:** Multiple sessions over days/weeks

---

### Workflow 4: Existing Project Onboarding

**When:** Adding the framework to a project you've already been building

```
SESSION 1 — SETUP:
1. Install framework files (see SETUP-GUIDE.md)
2. You: /design-audit

Claude:
- Explores entire codebase
- Walks through each existing view with you
- Documents what exists
- Identifies inconsistencies
- OUTPUT: Initial DESIGN-SYSTEM.md based on current state

SESSION 2 — DESIGN REFINEMENT:
You: /design-interview

Claude:
- Reviews audit findings
- Deep dive on vision
- Fills gaps
- OUTPUT: Complete DESIGN-SYSTEM.md

ONGOING:
You: /interview [for new features]
Use standard workflows from here
```

---

## SESSION MANAGEMENT

### The Problem With Long Sessions

Claude's "memory" within a conversation degrades over time. After 30+ back-and-forths or complex work, Claude can:
- Forget earlier context
- Become confused
- Make mistakes it wouldn't normally make

### The Solution: Session Lifecycle

**Starting a Session:**
```
You: /session-start

Claude:
- Reads SESSION-STATE.md from last session
- Reads project status (branch, uncommitted changes)
- Summarizes: "Last time we completed X and were working on Y"
- Asks: "Ready to continue, or different task today?"
```

**During a Session:**
- Claude monitors its own "health"
- If confusion detected, Claude says: "I'm getting fuzzy — recommend we start fresh. Let me write a handoff first."

**Ending a Session:**
```
You: /session-end

Claude:
- Saves SESSION-STATE.md (what was done, what's in progress, what's next)
- Updates LEARNINGS.md with any new learnings
- Summarizes Git activity
- Prepares clean handoff for next session
```

### When To Start Fresh

**Always start a new session:**
- After completing a spec
- After 30+ back-and-forths
- When switching to a different task
- When Claude seems confused
- At the start of a new day

**It's okay to continue:**
- In the middle of implementing a spec
- When following up on recent changes
- Quick fixes that build on previous context

---

## GIT AUTOPILOT

### What Git Is (Simple Explanation)

Git is a system that tracks changes to your code. Think of it like:
- **Commits** = Save points (like saving a video game)
- **Branches** = Parallel timelines (experiment without breaking main)
- **Push** = Upload your save points to the cloud
- **Pull Request (PR)** = Asking to merge your changes into the main version

### How Git Autopilot Works

**Claude handles everything:**
- Creating branches with good names
- Making commits with clear messages
- Pushing to GitHub
- Creating pull requests with descriptions
- Handling merge conflicts

**Claude checks with you before:**
- Creating a new branch
- Merging into main
- Pushing to remote

**Claude teaches as it goes:**
- "I'm creating a branch — think of it like a draft copy where we can experiment safely"
- "This commit saves our progress with the message 'Add handicap trends view'"

**At session end, Claude summarizes:**
- "Git Summary: Created branch 'feature/handicap-trends', made 3 commits, pushed to remote. Ready to merge when you approve."

---

## FILE REFERENCE

### Documentation Files (You Read These)

| File | What It Is | When To Read |
|------|------------|--------------|
| `MASTER-GUIDE.md` | This file — complete system explanation | Getting started, reference |
| `QUICK-START.md` | One-page cheat sheet | Quick reference |
| `SETUP-GUIDE.md` | Step-by-step installation instructions | First-time setup |
| `XCODE-INTEGRATION.md` | How to use Xcode 26.3's Claude features | Setting up Xcode integration |

### Global Files (~/.claude/)

| File | What It Is | How It's Used |
|------|------------|---------------|
| `CLAUDE.md` | Universal rules for all projects | Claude reads this every session |
| `commands/interview.md` | The interview command | Run with `/interview` |
| `commands/design-interview.md` | Design-focused interview | Run with `/design-interview` |
| `commands/design-audit.md` | Existing project audit | Run with `/design-audit` |
| `commands/quick-fix.md` | Fast fix workflow | Run with `/quick-fix` |
| `commands/framework-improve.md` | Framework improvement | Run with `/framework-improve` |
| `commands/session-start.md` | Session start ritual | Run with `/session-start` |
| `commands/session-end.md` | Session end ritual | Run with `/session-end` |

### Project Files (your-project/.claude/)

| File | What It Is | How It's Used |
|------|------------|---------------|
| `CLAUDE.md` | Project-specific rules + design system | Claude reads this every session |
| `settings.json` | Permissions and hooks | Automatic behaviors |
| `commands/plan.md` | Create implementation plan | Run with `/project:plan` |
| `commands/build.md` | Execute plan/spec | Run with `/project:build` |
| `commands/verify.md` | Full verification pipeline | Run with `/project:verify` |
| `commands/visual-verify.md` | UI/visual verification | Run with `/project:visual-verify` |
| `commands/commit-push-pr.md` | Git Autopilot | Run with `/project:commit-push-pr` |
| `commands/status.md` | Show current state | Run with `/project:status` |
| `commands/code-review.md` | Request code review | Run with `/project:code-review` |
| `agents/*.md` | All specialist agents | Called by workflows or directly |

### Project Root Files

| File | What It Is | How It's Used |
|------|------------|---------------|
| `DESIGN-SYSTEM.md` | Visual design standards | Referenced during UI work |
| `DESIGN-DECISIONS.md` | Design choice history | Autonomy progression, learning |
| `LEARNINGS.md` | Accumulated wisdom | Referenced during building |
| `SESSION-STATE.md` | Last session's handoff | Read at session start |
| `.mcp.json` | MCP server configuration | Xcode preview integration |

---

## GLOSSARY

**Agent** — A specialist AI persona with specific expertise. Like having different experts on your team.

**Branch (Git)** — A parallel version of your code. Lets you experiment without affecting the main version.

**CLAUDE.md** — A file that tells Claude how to behave. Contains rules, preferences, and context.

**Commit (Git)** — A saved snapshot of your code at a point in time. Like a save point in a game.

**Compaction** — When Claude summarizes earlier conversation to free up memory. Can cause context loss.

**Design System** — A documented set of visual rules (colors, fonts, spacing) that ensure consistency.

**Design Tokens** — The specific values in a design system (e.g., "primary green is #1B4D3E").

**DXA** — A unit of measurement in documents. 1440 DXA = 1 inch.

**Earned Autonomy** — The system where Claude gains more independence as it proves it understands your preferences.

**Edge Case** — An unusual situation that might break the code. Good specs cover edge cases.

**Git** — A system for tracking code changes over time. Essential for professional development.

**Global (Commands/Rules)** — Things that apply to ALL your projects, stored in ~/.claude/.

**Hook** — An automatic action triggered by something Claude does (e.g., format code after every edit).

**Integration Point** — Where a new feature connects to existing features. A common source of bugs.

**MCP (Model Context Protocol)** — A system that lets Claude connect to external tools like Xcode previews.

**One-Shot** — Building something correctly on the first try, without back-and-forth corrections.

**PR (Pull Request)** — A request to merge changes from one branch into another. Usually reviewed before merging.

**Project (Commands/Rules)** — Things specific to one project, stored in that project's .claude/ folder.

**Push (Git)** — Upload your local commits to a remote server (like GitHub).

**Session** — One continuous conversation with Claude Code. Context can degrade in long sessions.

**Spec (Specification)** — A detailed document describing exactly what to build. Good specs enable one-shots.

**SwiftUI** — Apple's modern framework for building iOS app interfaces.

**Template** — A starting point for new projects. Your template inherits all past learnings.

**Verification Pipeline** — The series of checks that run after building: tests, visual checks, code review, etc.

**Visual Regression** — When a UI change accidentally breaks something that looked correct before.

---

## WHAT'S NEXT?

1. **If setting up for the first time:** Read `SETUP-GUIDE.md`
2. **If adding to Links Ledger:** Follow the existing project onboarding workflow
3. **If you want a quick reference:** Print `QUICK-START.md`
4. **If setting up Xcode 26.3:** Read `XCODE-INTEGRATION.md`

---

*This framework was built to make you superhuman. Use it, give feedback, and watch it evolve.*
