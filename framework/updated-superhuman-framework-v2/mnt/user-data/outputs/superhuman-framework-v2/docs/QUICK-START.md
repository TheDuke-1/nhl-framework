# SUPERHUMAN FRAMEWORK V2 — QUICK START

> **What This Is:** A one-page cheat sheet for daily use. Print this and keep it handy.

---

## 🚀 ESSENTIAL COMMANDS

### Starting Work
```
/session-start          → Begin session, load previous context
```

### Planning & Building
```
/interview              → Deep interview for new features (40-75 questions)
/design-interview       → Establish visual identity and design system
/design-audit           → Audit existing project (walk through views with you)
/project:plan           → Create implementation plan
/project:build @SPEC    → Build from a spec file
```

### Verification & Quality
```
/project:verify         → Full verification (build, test, visual, review)
/project:visual-verify  → UI-only verification (Xcode previews)
/project:code-review    → Code review only
/project:status         → Show current state (branch, progress, changes)
```

### Shipping & Saving
```
/project:commit-push-pr → Git Autopilot: commit, push, create PR
/session-end            → Save state, summarize, clean handoff
```

### Quick Tasks
```
/quick-fix [issue]      → Fast workflow for small fixes
/framework-improve      → Review sessions, suggest improvements
```

### Call Agents Directly
```
/agent:creative-director    → Design vision review
/agent:ui-designer          → Visual aesthetics
/agent:ux-designer          → Usability/flows
/agent:visual-qa            → Pixel-perfect check
/agent:accessibility        → VoiceOver/Dynamic Type
/agent:code-reviewer        → Code quality check
/agent:code-simplifier      → Reduce complexity
/agent:test-engineer        → Create/improve tests
```

---

## 📋 WORKFLOW CHEAT SHEET

### Quick Fix (5-15 min)
```
/quick-fix [describe issue]
→ Review → Approve → Done
```

### Medium Feature (1-3 hours)
```
SESSION 1:
/interview [describe feature]
→ Answer questions → Get SPEC file

SESSION 2 (fresh):
/project:build @SPEC-feature-name.md
→ Review checkpoints → /project:verify → /project:commit-push-pr
```

### New Project Setup
```
1. Clone from your GitHub template
2. /design-interview → Establish design system
3. /interview → First feature spec
4. /project:build → Start building
```

### Existing Project Onboarding
```
1. Install framework files (see SETUP-GUIDE.md)
2. /design-audit → Walk through existing views
3. /design-interview → Fill gaps
4. Continue with normal workflows
```

---

## 🎯 GOLDEN RULES

| Rule | Why |
|------|-----|
| **Start fresh sessions often** | Prevents confusion from context overload |
| **Always `/session-start`** | Loads previous context |
| **Always `/session-end`** | Saves state for next time |
| **Interview before building** | Better spec = one-shot success |
| **Verify after building** | Catches bugs before you see them |
| **Give design feedback** | "Love it" or "Too generic" — both teach the system |

---

## 🔴 WHEN TO START A NEW SESSION

- ✅ After completing a spec/feature
- ✅ After 30+ back-and-forths
- ✅ When switching tasks
- ✅ When Claude seems confused
- ✅ Start of a new day

---

## 📊 STATUS DASHBOARD EXAMPLE

When you run `/project:status`, you'll see:
```
SESSION STATUS
═══════════════════════════════════════
Project: Links Ledger
Branch: feature/handicap-trends
Phase: Building (2/4)

Progress:
  ✅ Data model created
  ✅ Basic view structure
  🔄 Styling components (in progress)
  ⬜ Edge cases & polish

Files Modified: 3
Uncommitted Changes: Yes
Blockers: None

Last Verified: 2 hours ago
Design System: ✅ Compliant
═══════════════════════════════════════
```

---

## 🗂️ KEY FILES TO KNOW

| File | What It Is |
|------|------------|
| `CLAUDE.md` | Rules Claude follows |
| `DESIGN-SYSTEM.md` | Visual design standards |
| `LEARNINGS.md` | Accumulated wisdom |
| `SESSION-STATE.md` | Last session's handoff |
| `SPEC-*.md` | Feature specifications |

---

## ❓ COMMON QUESTIONS

**Q: Claude seems confused. What do I do?**
A: Run `/session-end`, start a new Claude Code session, run `/session-start`

**Q: How do I give design feedback?**
A: Just say it naturally: "This looks too generic" or "I love how this turned out" — Claude captures it automatically

**Q: Do I need to understand Git?**
A: No. Claude handles Git. Just run `/project:commit-push-pr` when ready to save.

**Q: What if Claude makes a mistake?**
A: Point it out. Claude will fix it AND add a rule to prevent it happening again.

---

## 🆘 HELP

- Full documentation: `MASTER-GUIDE.md`
- Setup instructions: `SETUP-GUIDE.md`
- Xcode integration: `XCODE-INTEGRATION.md`

---

*You handle vision. Claude handles work.*
