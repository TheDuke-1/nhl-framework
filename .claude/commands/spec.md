Read the spec file at $ARGUMENTS and refine it into a final, implementation-ready specification.

## Process

1. Read the spec file thoroughly.
2. Identify any gaps, ambiguities, or contradictions.
3. Present a summary of the spec and any issues found using AskUserQuestionTool.
4. Ask 3-5 targeted follow-up questions to fill gaps.
5. Write the final spec back to the same file with all refinements.
6. At the end, output a one-line command the user can copy to start a new session and build from this spec:
   ```
   claude --resume "Build from spec: [feature name]"
   ```

## Final Spec Must Include
- Numbered requirements (each one testable/verifiable)
- Clear implementation order (what to build first, second, third)
- Verification criteria for each requirement
- Explicit "out of scope" section
