# GitHub Copilot Instructions: Makefile Workflow

Follow the Makefile Workflow lifecycle when assisting in this repository:

1. Read target files and their existing tests before you propose changes.
2. Do all work on a dedicated branch, such as `feat/<id>-<slug>` or `fix/<id>-<slug>`.
3. Write failing tests that reproduce the bug or specify the feature before you write production code.
4. Point tests to `*_test` databases, configured `database.testDatabases`, in-memory databases, or mock fixtures. Never connect to production databases.
5. Keep edits small and favor object composition. If large datasets outgrow an ORM, encapsulate parameterized SQL or NoSQL queries behind repository methods.
6. Audit every diff against the Six Pillars: Intent, Verification, Architecture, Blast Radius, Readability, and Error Handling.
7. In multi-language repositories, run tests in the affected subproject first, then run the full suite before commit.
8. Write commit messages, documentation, and pull request summaries in Simple English: short sentences, active voice, and clear terms.
9. If `.workflow/config.json` or `~/.gemini/config/makefile-workflow.json` exists, read it to load user configuration.

## Interactive Model Switch Reminder

Prompt the user in Copilot Chat at review boundaries:

1. At Target 40, prompt the user: "Select a deep-reasoning model in Copilot Chat for the Six Pillars review."
2. At Target 45, tell the user: "Review passed. You can switch back to your default coding model."
