# Superhuman Framework V2 — Quick Start

## What This Is

A fast-track guide to get the Superhuman Framework running in under 5 minutes. For full details, see MASTER-GUIDE.md.

---

## 60-Second Setup

### 1. Install Global Commands (30 seconds)

```bash
# macOS/Linux
cp -r global/commands/* ~/.claude/commands/
cp global/CLAUDE.md ~/.claude/CLAUDE.md
```

Now `/interview`, `/design-interview`, `/quick-fix` work anywhere.

### 2. Set Up Your Project (30 seconds)

```bash
# From your project's root folder
cp -r /path/to/superhuman-framework-v2/template/.claude .
cp /path/to/superhuman-framework-v2/template/*.md .
```

Now `/project:plan`, `/project:build`, `/project:verify` and all agents work.

---

## Your First Commands

### Start a New Project
```
/design-interview     # Set up visual identity first
/interview           # Then capture your first feature
/project:plan        # Create execution plan
/project:build       # Build it
/project:verify      # Test everything
```

### Continue an Existing Project
```
/session-start       # Load context from last session
/project:status      # See where you are
```

### Fix a Quick Bug
```
/quick-fix          # Fast, focused fix (no planning overhead)
```

### End Your Session
```
/session-end        # Saves state, summarizes what happened
```

---

## Key Commands to Remember

| What You Want | Command to Use |
|---------------|----------------|
| Build a new feature | `/interview` → `/project:plan` → `/project:build` |
| Fix a small bug | `/quick-fix` |
| Set up visual identity | `/design-interview` |
| Check existing design patterns | `/design-audit` |
| See current status | `/project:status` |
| Push changes to git | `/project:commit-push-pr` |
| Call a specific specialist | `/agent:name` (e.g., `/agent:ui-designer`) |
| Improve the framework itself | `/framework-improve` |

---

## That's It!

For detailed explanations of every command, agent, and workflow, see MASTER-GUIDE.md.

The framework learns from every session, so it gets better over time. Just use it.
