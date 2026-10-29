# GitHub Copilot Instructions: Makefile Workflow

When assisting with code in this repository, follow the Makefile Workflow lifecycle:

1. **Understand Before Editing**: Read target files and their existing tests before proposing changes.
2. **Feature Branching**: Ensure work takes place on a dedicated branch (`ticket/<id>-<slug>`).
3. **Red-Green TDD**: Propose test cases that reproduce the problem before writing the fix.
4. **Hermetic Test Isolation**: Never configure tests to access production databases or live files. Use test databases, in-memory databases, and mock fixtures.
5. **Narrow Blast Radius**: Keep edits small and targeted. Do not refactor unrelated files during bug fixes.
6. **Six Pillars Code Quality**: Evaluate code against Intent, Verification, Architecture, Blast Radius, Reviewer Defense, and Immune Defenses.
7. **Monorepo Awareness**: In multi-language repositories, identify subprojects and run targeted tests in the affected directory before running full test suites.
8. **Simple English**: Write commit messages, documentation, and PR comments using plain English: short sentences, active voice, and clear terminology.
9. **Workflow Configuration**: Check `.workflow/config.json` or `~/.gemini/config/makefile-workflow.json` if present for user settings and model preferences.
10. **Interactive Model Switch Reminder (Target 40)**:
    - At Target 40 (Six Pillars Review): Ask the user in chat:
      "👉 **Please switch the Copilot Chat model picker to Claude 3.5 Sonnet or GPT-4o** to run the Six-Pillar adversarial review."
    - At Target 45 (Review Approval): Inform the user:
      "👉 Review approved. You can switch back to your standard coding model."
