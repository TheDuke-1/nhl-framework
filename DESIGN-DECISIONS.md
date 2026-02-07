# DESIGN DECISIONS: NHL Playoff Prediction Framework

> **What This Is:** A log of all design decisions, approvals, rejections, and extracted principles. This is Claude's "design memory."

> **How It's Used:** 
> - Claude references this to understand your taste
> - Used for autonomy progression tracking
> - Captures visual evidence and reasoning

> **How It's Updated:** Automatically during design reviews and when you give feedback

---

## Autonomy Tracking

### Overall Status

| Area | Approval Rate | Level | Notes |
|------|---------------|-------|-------|
| Color Usage | _/_ | [CHECKPOINT] | |
| Typography | _/_ | [CHECKPOINT] | |
| Layout | _/_ | [CHECKPOINT] | |
| Components | _/_ | [CHECKPOINT] | |
| Overall UI | _/_ | [CHECKPOINT] | |

### Level Definitions

- **CHECKPOINT (0-5 approvals):** Show milestones, wait for approval
- **FINAL_APPROVAL (5-10 approvals):** Work independently, show final result  
- **AUTONOMOUS (10+ approvals, 90%+ rate):** Ship confidently, escalate when uncertain

---

## Extracted Principles

> Patterns discovered from your feedback

### Principle: [Name]

**Discovered:** [date]
**Source:** [Which decision/feedback]
**Rule:** [The principle in actionable form]

Example:
```
### Principle: Depth Over Flat

**Discovered:** 2025-01-15
**Source:** Rejected flat button design
**Rule:** Always use subtle shadows on interactive elements. 
        Flat design feels "cheap" to this user.
```

---

## Decision Log

### [Date] — [View/Component Name]

**Type:** [New View / Modification / Component]
**Agent:** [UI Designer / Creative Director / etc.]
**Autonomy Level:** [CHECKPOINT / FINAL_APPROVAL / AUTONOMOUS]

**What Was Built:**
[Description of what was created]

**User Verdict:** ✅ APPROVED / ❌ REJECTED / 🔄 REVISION REQUESTED

**User Feedback:**
> "[Exact words from user]"

**Extracted Learning:**
- [What this teaches about user's preferences]

**Design System Impact:**
- [ ] Color update needed
- [ ] Typography update needed
- [ ] Component style update needed
- [ ] Anti-pattern identified
- [ ] No updates needed

**Screenshots:**
- Before: [link/reference]
- After: [link/reference]

---

## Approval History

### Approved Designs

| Date | View/Component | Key Feedback | Principle Extracted |
|------|----------------|--------------|---------------------|
| [date] | [name] | "[feedback]" | [principle] |

### Rejected Designs

| Date | View/Component | Rejection Reason | Fix Applied |
|------|----------------|------------------|-------------|
| [date] | [name] | "[reason]" | [what was changed] |

### Revision Requests

| Date | View/Component | Revision Requested | Final Outcome |
|------|----------------|-------------------|---------------|
| [date] | [name] | "[request]" | [approved/rejected] |

---

## Reference Comparisons

> When user compares to other apps

### Positive Comparisons ("Like this")

| Date | Our Design | Reference App | What User Liked |
|------|------------|---------------|-----------------|
| [date] | [view] | [app name] | "[specific element]" |

### Negative Comparisons ("Not like this")

| Date | Our Design | Reference App | What User Disliked |
|------|------------|---------------|-------------------|
| [date] | [view] | [app name] | "[specific element]" |

---

## Visual Evidence

### Baseline Screenshots

> Approved designs that represent the standard

| View | Status | Screenshot | Approved Date |
|------|--------|------------|---------------|
| [view name] | BASELINE | [link] | [date] |

### Anti-Pattern Examples

> Designs that were rejected — what NOT to do

| Example | Why Rejected | Screenshot |
|---------|--------------|------------|
| [description] | "[reason]" | [link] |

---

## Design Interview Highlights

> Key quotes and preferences from `/design-interview`

### Visual Identity

> "[Quote about overall feel]"

### Color Preferences

> "[Quote about colors]"

### Typography Preferences

> "[Quote about fonts/text]"

### What to Avoid

> "[Quote about what they don't want]"

---

## Trend Analysis

### Improving Areas

- [Area where approval rate is increasing]

### Struggling Areas

- [Area where rejections are common]

### Recommendations

- [What to focus on based on patterns]

---

## Notes for Agents

### For UI Designer

- User prefers: [key preferences]
- User dislikes: [key dislikes]
- Safe choices: [things that consistently get approved]
- Risk areas: [things that often get rejected]

### For Creative Director

- Brand alignment priorities: [what matters most]
- Consistency gaps: [areas needing attention]
- Evolution direction: [how style is evolving]

---

*This document is updated automatically during design workflows. Manual additions are welcome for capturing additional context.*
