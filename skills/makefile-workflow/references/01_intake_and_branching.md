# 01. Intake, Feature Branching, and Readerboard (`Target 00` and `Target 10`)

This manual covers state restoration, ticket intake, Git branch setup, and live readerboard updates.

## 1. Target 00: Read State (`read-init-d`)

At the start of every turn, inspect `<workspace>/.workflow/state/`:

1. If `.workflow/state/` does not exist, start at Target 10.
2. If `.workflow/state/` exists, read all `.md` files in alphabetical order (`00_governance.md` through `99_next_action.md`).
3. Restore the active ticket ID, branch name, and active target.
4. If the user only asks for status, print the readerboard in chat and stop.

## 2. Target 10: Ticket Intake and Git Branching

### Mode A: Active Ticket Provided

When the user provides a task description, issue number, or issue URL, run these steps:

1. Extract the ticket ID and scope from the request.
2. Make sure that `git status --short` is clean on the current branch. If uncommitted edits exist, stop and ask the user how to handle them.
3. Switch to the default branch (`main` or `master`) and pull the latest commits:
   ```bash
   git checkout main && git pull --ff-only
   ```
4. Exclude `.workflow/state/` from Git tracking so state cards never pollute `git add -A` or `git status`:
   ```bash
   git check-ignore -q .workflow/state/ || echo ".workflow/state/" >> .git/info/exclude
   ```
5. Create and switch to a feature branch that matches standard Git naming rules:
   - GitHub Bug (`#<number>`): `fix/<number>-<slug>`, for example `fix/42-login-redirect`.
   - GitHub Feature (`#<number>`): `feat/<number>-<slug>`, for example `feat/101-csv-export`.
   - General GitHub Issue (`#<number>`): `ticket/<number>-<slug>`, for example `ticket/55-upgrade-deps`.
   - Jira or Linear Issue (`<PROJECT>-<NUMBER>`): `feat/<project>-<number>-<slug>` or `fix/<project>-<number>-<slug>`.
   - Ad-hoc Chat Task (no external tracker): Read `.workflow/history.json` for count `N`, then use `feat/<N+1>-<slug>` or `fix/<N+1>-<slug>`.
6. Format `<slug>` with lowercase letters, digits, and single hyphens (`[a-z0-9-]`), up to 40 characters.
7. Write the ticket details to `<workspace>/.workflow/state/10_ticket.md` and advance to Target 15.

### Mode B: Open Backlog Discovery

When the user asks what to work on next, run these steps:

1. Query open issues from the issue tracker, for example `gh issue list`.
2. Exclude issues that already have an active branch or assignee.
3. Sort open items by priority label (`P0`, `P1`, `P2`, `P3`, then unlabeled).
4. Print the candidate list in chat.
5. If two or more candidates exist ($N \ge 2$), call `ask_question` so the user can pick one.

## 3. Live Readerboard (`99_next_action.md`)

Update `<workspace>/.workflow/state/99_next_action.md` at every target transition.

```markdown
# 99_next_action: Live Memento Readerboard

- Ticket: [<ID>: <Title>](<URL>) (In Progress)
- Branch: `feat/<ID>-<slug>`
- Active Target: Target 15 (`archaeology-verified`)
- Last Completed Step: Target 10 (`ticket-assigned`)
- Next Action: Fork archaeology-worker to scan subprojects and tests

## Milestone Progress
- [x] T00: read-init-d
- [x] T10: ticket-assigned
- [>] T15: archaeology-verified
- [ ] T20: approved-plan (Human Pause Gate)
- [ ] T30: implementation-diff (Red-Green TDD)
- [ ] T40: adversarial-review (Six Pillars)
- [ ] T45: approved-review (Human Pause Gate)
- [ ] T50: commit (Human Pause Gate)
- [ ] T60: push (Human Pause Gate)
- [ ] T70: bot-quiescence (180s CI poll)
- [ ] T75: ready-to-land (Human Pause Gate)
- [ ] T80: land (Merge and Cleanup)
- [ ] T90: finish (History Ledger)
```
