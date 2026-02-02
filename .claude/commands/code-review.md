Review the current changes using the code-reviewer agent.

## What to review:
```bash
git diff
```

Use the code-reviewer agent to analyze all changes. Present findings organized by severity:

- 🔴 **Critical**: Bugs, crashes, data loss, security issues
- 🟡 **Warning**: Performance issues, bad patterns, missing edge cases
- 🟢 **Suggestion**: Style improvements, simplification opportunities

For each issue, include:
- File and line number
- What the problem is (in plain language)
- Suggested fix

If no issues found, confirm the code is clean and ready to commit.
