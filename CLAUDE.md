# Claude Code Guidelines: Makefile Workflow

This repository uses the Makefile Workflow. Follow these rules for every coding task.

## Core Rules

1. If `.workflow/state/` exists, read all `.md` files in alphabetical order (`cat .workflow/state/*.md`) to restore the active target.
2. Before you write code, make sure that `git status --short` is clean on `main`, then create a ticket branch.
3. Read target files before you edit them, apply small edits, and leave unrelated files unchanged.
4. Point tests to isolated `*_test` databases, in-memory databases, or mock fixtures. Never touch production data.
5. Write failing unit tests before you write feature code, and run tests in the active subproject directory.
6. Stop and wait for explicit user approval at all six pause gates:
   - Target 20: Plan approval.
   - Target 42: Blocker triage, when review finds blockers.
   - Target 45: Review sign-off.
   - Target 50: Commit approval.
   - Target 60: Push approval.
   - Target 75: Pull request merge approval.
7. Run targeted subproject tests at Target 30, and run the full repository test suite at Target 50 and Target 75.
8. Write documentation, commit messages, and pull request summaries in Simple English with short sentences and active voice.

## Model Selection and Configuration

Read `.workflow/config.json` or `~/.gemini/config/makefile-workflow.json` when present to load user model preferences.
Use your session model for standard implementation tasks.
At Target 40, run the Six-Pillar review with a high-reasoning model:

```bash
claude -p --model claude-3-opus-20240229 "Run Six-Pillar review on $(git merge-base HEAD origin/main)..HEAD"
```

## Target Summary

- `T00`: Read `.workflow/state/*.md` state cards.
- `T10`: Record ticket scope and create branch `feat/<id>-<slug>` or `fix/<id>-<slug>`.
- `T15`: Scan subprojects, detect languages, and build the Belnap fact table.
- `T20`: Write `.workflow/state/20_plan.md`, state test changes, and wait for Target 20 plan approval.
- `T30`: Run Red-Green-Refactor test-driven development and targeted subproject tests.
- `T40`: Run the Six Pillars code review.
- `T42`: Present blockers and wait for triage approval.
- `T45`: Present zero-blocker review and wait for sign-off.
- `T50`: Format, lint, run full tests, wait for Target 50 commit approval, and commit.
- `T60`: Check clean merge with `git merge-tree`, wait for push approval, push, and open a pull request.
- `T70`: Poll CI checks and wait 180 seconds for review bots to finish.
- `T75`: Present policy checks and wait for merge approval.
- `T80`: Squash-merge the pull request, delete the ticket branch, and update `main`.
- `T90`: Record lessons and append the task to `.workflow/history.json` and `.workflow/history.md`.
