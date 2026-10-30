# Makefile Workflow Plugin Rules

These rules apply when the `makefile-workflow` plugin is active.

## 1. Chat Presentation and Input Rules

The chat stream is the main presentation surface. The `ask_question` tool is an input prompt, not a display surface.

1. If the user must choose between two or more alternatives ($N \ge 2$), call `ask_question`.
2. If a gate has one approval action ($N = 1$), do not call `ask_question`. Print the full proposal in chat with `file://` links and stop tool calls. This rule covers Plan Approval (Target 20), Review Approval (Target 45), Commit Approval (Target 50), Push Approval (Target 60), and Landing Approval (Target 75).
3. Before you ask for a decision, print the full facts in the chat message.
4. Add a `file://` markdown link for every file, diff, plan, or review card that you name.

## 2. Production Data Protection Rules

Never connect tests or agent commands to live systems.

1. Do not connect to live production databases, cloud storage, or mutable production files.
2. Point tests to isolated test databases (for example `*_test` or configured `database.testDatabases`), in-memory databases, or mock fixtures. If live versus test database names are unclear, ask the user before running tests.
3. Run file operations during tests inside temporary directories or mocked file systems.

## 3. Code Edit and Architecture Rules

Keep each code change small and within ticket scope.

1. Read target files and their type contracts before you edit them.
2. Apply minimal edits that solve the active ticket. Favor object composition over deep class inheritance.
3. Use an ORM (a library that maps database rows to objects) by default. If large datasets slow down the ORM, encapsulate parameterized SQL or NoSQL queries behind repository methods.
4. If you find unrelated defects during a ticket, do not edit them. Record them in ticket notes for a separate task.

## 4. Simple English Documentation Rules

Apply the rules of the `simple-english` plugin to documentation, plans, changelogs, and pull request descriptions:

1. Keep procedural sentences at 20 words or fewer, with one instruction per sentence.
2. Keep descriptive sentences at 25 words or fewer, in simple tenses and active voice.
3. Put the condition before the command with a comma: "If the build fails, read the log."
4. Define each technical concept term in under ten words at first use.
5. Delete filler words, contractions, semicolons, and em-dashes.
