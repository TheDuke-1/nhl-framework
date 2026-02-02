Give me a quick status update on this project.

## Check and report:

1. **Git Status**: Current branch, uncommitted changes, unpushed commits
2. **Recent Activity**: Last 5 commits (one line each)
3. **Open PRs**: Any open pull requests (if gh is available)
4. **Build Health**: Run the build command and report pass/fail
5. **Test Health**: Run the test suite and report results

## Format:

```
PROJECT STATUS: [project name]
═══════════════════════════════
Branch:     [current branch]
Changes:    [X files modified, X staged, X unstaged]
Last Commit: [date — message]

Recent Commits:
  • [message] (date)
  • ...

Build:  ✅ / ❌
Tests:  X passed, X failed

Open PRs: [count or "none"]
```

Keep it brief. This is a dashboard, not a report.
