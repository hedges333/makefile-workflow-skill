# 01. Intake, Feature Branching & Readerboard (`Target 00` & `Target 10`)

This manual details the intake protocol, git branch creation, and live readerboard management.

## 1. Target 00: Read State (`read-init-d`)

When an agent turn begins, check if `<workspace>/.workflow/state/` exists (or fallback to `<brain>/state/`):
1. If the directory does not exist, start fresh at Target 10.
2. If the directory exists, read all files in lexical order (`00_governance.md` to `99_next_action.md`).
3. Restore the active ticket identity, branch, and active target.
4. If the user asks for status without starting work, print the readerboard and halt.

## 2. Target 10: Ticket Intake & Git Branching

### Mode A: Active Ticket Assigned
When the user provides a ticket number, URL, or explicit task description:
1. Extract the ticket identifier and scope.
2. Verify that `git status --short` is clean on your current branch. If uncommitted changes exist, pause and ask the user how to handle them.
3. Switch to the default branch (`main` or `master`) and pull the latest commits:
   ```bash
   git checkout main && git pull --ff-only
   ```
4. Create and checkout a dedicated feature branch using industry Git standards:
   - **GitHub Issue (`#<number>`)**:
     - Bug fixes: `fix/<number>-<slug>` (e.g. `fix/42-login-redirect`)
     - New features: `feat/<number>-<slug>` (e.g. `feat/101-csv-export`)
     - General tasks: `ticket/<number>-<slug>` (e.g. `ticket/55-upgrade-deps`)
   - **Jira / Linear Issue (`<PROJECT>-<NUMBER>`)**:
     - `feat/<project>-<number>-<slug>` (e.g. `feat/AUTH-102-jwt-token`)
     - `fix/<project>-<number>-<slug>` (e.g. `fix/PAY-404-stripe-webhook`)
   - **Ad-hoc Chat Requests (No external issue)**:
     - Check `.workflow/history.json` for task count $N$; use `feat/<N+1>-<slug>` or `fix/<N+1>-<slug>` (e.g. `feat/1-healthcheck-endpoint`).
   - **Slug Hygiene Rules**:
     - Lowercase alphanumeric characters and single hyphens (`[a-z0-9-]`).
     - No spaces, underscores, colons, tildes, carets, or double-dots.
     - Maximum 40 characters for the slug portion.
5. Record ticket details in `<workspace>/.workflow/state/10_ticket.md`.

### Mode B: Open Backlog Discovery
When the user asks "What is next on the backlog?":
1. Query open issues using the project issue tracker (e.g. `gh issue list`).
2. Filter out issues already assigned or in progress.
3. Sort open items by priority label (`P0` > `P1` > `P2` > `P3` > unlabeled).
4. Present the top candidates in chat.
5. Use `ask_question` only when offering two or more alternatives ($N \ge 2$).

## 3. The Live Readerboard (`99_next_action.md`)

Maintain `<workspace>/.workflow/state/99_next_action.md` at every target transition.
In Antigravity sessions, also write to `<brain>/readerboard.md` with `UserFacing: true` so the operator sees the live dashboard in the UI.

### Readerboard Template:

```markdown
# ⚡ 99_next_action: Live Memento Readerboard

* **Ticket**: [<ID> — <Title>](<URL>) (`In Progress`)
* **Branch**: `ticket/<ID>-<slug>`
* **Active Target**: Target 15 (`archaeology-verified`)
* **Last Completed Step**: Target 10 (`ticket-assigned`)
* **Next Permitted Action**: Fork archaeology worker to scan subprojects and tests

## 📊 Milestone Progress
- [x] T00: read-init-d
- [x] T10: ticket-assigned
- [>] T15: archaeology-verified
- [ ] T20: approved-plan (Human Pause Gate)
- [ ] T30: implementation-diff (Red-Green TDD)
- [ ] T40: adversarial-review (Six Pillars)
- [ ] T45: review-approved (Human Pause Gate)
- [ ] T50: commit (Human Pause Gate)
- [ ] T60: push (Human Pause Gate)
- [ ] T70: bot-quiescence (180s CI poll)
- [ ] T75: ready-to-land (Human Pause Gate)
- [ ] T80: land (Merge & Prune)
- [ ] T90: finish (History Log)
```
