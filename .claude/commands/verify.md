Run the full verification pipeline on the current changes.

## Pipeline Steps

### Step 1: Build Check
Run the project's build command. Report pass/fail.

### Step 2: Test Suite
Run all tests. Report results with counts (passed/failed/skipped).

### Step 3: Code Review
Use the code-reviewer agent to review all modified files. Report any issues found.

### Step 4: Code Simplification Check
Use the code-simplifier agent to scan for unnecessary complexity. Report findings.

### Step 5: Regression Check
- List all files that were modified.
- For each modified file, check: did this change touch anything that could break existing functionality?
- If yes, run targeted tests for those areas.

### Step 6: Summary Report

Present results in this format:

```
VERIFICATION REPORT
═══════════════════
Build:        ✅ PASS / ❌ FAIL
Tests:        ✅ X passed, X failed, X skipped
Code Review:  ✅ No issues / ⚠️ X issues found
Simplification: ✅ Clean / ⚠️ X suggestions
Regression Risk: ✅ Low / ⚠️ Medium / ❌ High

Issues Found:
1. [issue description + recommended fix]
2. ...

Verdict: READY TO COMMIT / NEEDS FIXES
```

If verdict is NEEDS FIXES, automatically fix what you can and re-run the pipeline. If issues remain after 2 attempts, present them to me for decision.
