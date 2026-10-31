# Git and Shell Execution Scars

This reference manual documents Git operations and shell execution scars (`SCAR-GIT-*` and `SCAR-SH-*`). These rules protect repository trees, history integrity, and shell command tokenization.

## Scars in this Category

| ID | Title | Scope |
| :--- | :--- | :--- |
| `SCAR-SH-03` | Shell Redirection and Comment Stripping | Pre-Tool Guard Parsing |
| `SCAR-GIT-20` | Pre-Push Merge Check | Branch Conflict Prevention |
| `SCAR-GIT-25` | Destructive Git Command Protection | Working Tree & Branch Safety |
| `SCAR-GIT-30` | Pure Git Mode and Tool Discovery | Non-GitHub / Offline Workflows |

---

### SCAR-SH-03: Shell Redirection and Comment Stripping

- **Wound**: Complex shell commands containing redirections (`> /dev/null`) or inline comments fail parsing checks or bypass subcommand inspection guards.
- **Trap**: Naively tokenizing raw shell strings without stripping trailing redirections and comments before checking subcommands.
- **Permanent Reflex**: Strip shell redirections and unquoted comments before tokenizing command lines for Git and database safety checks.

### SCAR-GIT-20: Pre-Push Merge Check

- **Wound**: An agent pushes a branch that conflicts with `main`, breaks CI, and requires history rewrites.
- **Trap**: Assuming that passing local unit tests means a clean merge with `origin/main`.
- **Permanent Reflex**: Run `git fetch origin main` and `git merge-tree $(git merge-base HEAD origin/main) HEAD origin/main` before every push.

### SCAR-GIT-25: Destructive Working-Tree and History Guards

- **Wound**: An agent runs `git reset --hard`, `git clean -fd`, or `git checkout --` after a test failure and destroys uncommitted work.
- **Trap**: Blocking only `git push --force` to `main` while trusting prompt rules to stop other destructive Git commands.
- **Permanent Reflex**: Block work-discarding and force-push Git commands in hooks and MCP. Require explicit human approval before `git rebase` and `git branch -D`.

### SCAR-GIT-30: Pure Git Mode and Hosting Tool Discovery

- **Wound**: An agent attempts to run `gh pr create` or `gh pr checks` in an SSH-only or non-GitHub repository and stalls at Target 60 or Target 70 even though Git push succeeded.
- **Trap**: Assuming every repository uses authenticated GitHub CLI tooling instead of checking whether `gh` is authenticated.
- **Permanent Reflex**: Check `gh auth status` at Target 15. If `gh` is unavailable or unauthenticated, use Pure Git Mode: skip remote PR creation at Target 60, run full local repository tests at Target 70, present local landing readiness at Target 75, and squash-merge on `main` at Target 80 using standard Git commands.
