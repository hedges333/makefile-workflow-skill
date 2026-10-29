# Makefile Workflow Plugin Rules

These rules apply whenever the `makefile-workflow` plugin is enabled.

## 1. The Sovereign Presentation Surface Rule

The chat stream is the primary presentation surface. The interactive modal (`ask_question`) is strictly an ergonomic input tool, never a replacement for chat presentation.

1. **Only use `ask_question` for two or more choices ($N \ge 2$)**.
   Use `ask_question` only when the user must choose between two or more described options (such as selecting a ticket or choosing an architectural alternative).
2. **Never use `ask_question` for unary approval gates ($N = 1$)**.
   For single-option approvals (Plan Approval at Target 20, Review Approval at Target 45, Commit Approval at Target 50, Push Approval at Target 60, Landing Approval at Target 75), do not invoke `ask_question`. Instead, print the complete proposal directly in chat with clickable links (`👉 [Inspect Full Plan: plan.md](file:///...)`), and pause with empty tool calls.
3. **Never ask blind questions**.
   Never ask the user to make a decision without rendering the full substance of what is being decided directly in the chat message.
4. **Clickable links required**.
   Every referenced file, diff, plan, or review card must include a clickable markdown link using the `file://` scheme.

## 2. The Production Data Protection Rule

1. **Zero production database access**.
   Test suites and automated agents must never connect to live production databases, production cloud storage, or mutable production files.
2. **Mandatory test isolation**.
   Tests must point to dedicated test databases (such as `*_test`), in-memory databases, or mock fixtures.
3. **Hermetic directories**.
   File operations during tests must use temporary directories or mocked file systems.

## 3. Review Before Edit and Small Edits

1. **Inspect before edit**.
   Read target files and understand their types and contracts before making modifications.
2. **Narrow blast radius**.
   Apply minimal, confident edits that solve the ticket.
3. **Ignore out-of-scope code smells**.
   If you find unrelated defects or style issues during a ticket, do not edit them. Record them in ticket notes for a future task.

## 4. Simple English Documentation Standard

When you write documentation, plan summaries, changelogs, or PR descriptions:
1. Apply the rules of the `simple-english` plugin.
2. Use short sentences (at most 20 words for instructions, at most 25 words for descriptions).
3. Use active voice and simple tenses.
4. Put conditions before commands with a comma: "If the build fails, read the log."
5. Define technical terms at first use.
6. Delete marketing fluff and vague filler words.
