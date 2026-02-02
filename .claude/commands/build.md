Read the spec or plan at $ARGUMENTS and implement it completely.

## Execution Rules

1. **Read the entire spec first.** Do not start coding until you've read and understood every requirement.

2. **Follow the implementation order specified in the spec.** Don't skip ahead or reorder unless you have a technical reason (explain it if so).

3. **After each major step**, briefly state what you just completed (one line).

4. **Verify as you go**:
   - After creating/modifying a file: run the build to check compilation.
   - After implementing a feature: run relevant tests.
   - If a build or test fails: fix it before moving on.

5. **When done**, run the full verification pipeline:
   - Build the project
   - Run all tests
   - Review your own changes (use the code-reviewer agent)
   - Present a summary of everything built

6. **Final output** should include:
   - ✅ List of requirements completed (reference spec numbers)
   - ⚠️ Any requirements that couldn't be completed (with explanation)
   - 📋 Files created or modified
   - 🧪 Test results

## IMPORTANT
- Do NOT deviate from the spec without telling me.
- Do NOT add features not in the spec (scope creep is the enemy).
- If you discover the spec has a problem or contradiction, STOP and ask me.
- If you encounter an error you can't resolve in 3 attempts, STOP and ask me.
