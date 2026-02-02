Commit the current changes, push, and create a pull request.

## Pre-flight checks (run these via bash, don't ask the model):
```bash
git status
git diff --stat
```

## Process

1. Review the staged and unstaged changes.
2. Stage all relevant changes (only files related to the current task).
3. Write a clear, descriptive commit message:
   - First line: concise summary (under 72 chars)
   - Blank line
   - Body: what changed and why (2-5 lines max)
   - No emoji
4. Commit the changes.
5. Push to the current branch.
6. If the branch is not `main`/`master`, create a pull request:
   - Title: same as commit first line
   - Body: summary of changes with a verification checklist
7. Report the PR URL.

## If there are no changes to commit:
Tell me there's nothing to commit and suggest what to do next.
