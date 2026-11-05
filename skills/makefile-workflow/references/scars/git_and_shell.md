# Git and Shell Execution Scars

This reference manual documents Git operations and shell execution scars (`SCAR-GIT-*` and `SCAR-SH-*`). These rules protect repository trees, history integrity, and shell command tokenization.

## Scars in this Category

| ID | Title | Scope |
| :--- | :--- | :--- |
| `SCAR-SH-01` | Prefer Temporary Script Files Over Complex Shell Quoting | Command Quoting & Script Isolation |
| `SCAR-SH-03` | Shell Redirection and Comment Stripping | Pre-Tool Guard Parsing |
| `SCAR-GIT-20` | Pre-Push Merge Check | Branch Conflict Prevention |
| `SCAR-GIT-25` | Destructive Git Command Protection | Working Tree & Branch Safety |
| `SCAR-GIT-30` | Pure Git Mode and Tool Discovery | Non-GitHub / Offline Workflows |

---

### SCAR-SH-01: Prefer Temporary Script Files Over Complex Shell Quoting

- **Wound**: An agent attempts complex multiline or quoted shell invocations (`bash -c "..."` or inline pipes), leading to syntax errors, unescaped variable expansion, or corrupted arguments.
- **Trap**: Trying to escape layers of quotes inline inside shell command strings instead of writing the logic to an executable script file.
- **Permanent Reflex**: If shell commands require complex string escaping or multiple quoting layers, write the script to a file in a temporary directory (or scratch directory) and execute that file directly. Prefer Dart when available, falling back to Python.
- **Socratic Probe**: Does this command involve fragile nested quotes or shell escapes that should be extracted into a temporary script?

### SCAR-SH-03: Shell Redirection and Comment Stripping

- **Wound**: Complex shell commands containing redirections (`> /dev/null`) or inline comments fail parsing checks or bypass subcommand inspection guards.
- **Trap**: Naively tokenizing raw shell strings without stripping trailing redirections and comments before checking subcommands.
- **Permanent Reflex**: Strip shell redirections and unquoted comments before tokenizing command lines for Git and database safety checks.
- **Socratic Probe**: If you tokenize a raw shell string without stripping inline comments or redirections, could command safety checks be bypassed or fail? Will stripping unquoted comments and redirects reveal the true commands being executed?

### SCAR-GIT-20: Pre-Push Merge Check

- **Wound**: An agent pushes a branch that conflicts with `main`, breaks CI, and requires history rewrites.
- **Trap**: Assuming that passing local unit tests means a clean merge with `origin/main`.
- **Permanent Reflex**: Run `git fetch origin main` and `git merge-tree $(git merge-base HEAD origin/main) HEAD origin/main` before every push.
- **Socratic Probe**: Even if local tests pass, has the remote target branch moved ahead since you branched? Will testing `git merge-tree` before pushing ensure your changes merge cleanly without breaking CI?

### SCAR-GIT-25: Destructive Working-Tree and History Guards

- **Wound**: An agent runs `git reset --hard`, `git clean -fd`, or `git checkout --` after a test failure and destroys uncommitted work.
- **Trap**: Blocking only `git push --force` to `main` while trusting prompt rules to stop other destructive Git commands.
- **Permanent Reflex**: Block work-discarding and force-push Git commands in hooks and MCP. Require explicit human approval before `git rebase` and `git branch -D`.
- **Socratic Probe**: If you run destructive Git commands to reset state, could you wipe out uncommitted user work? Would it be safer to isolate changes non-destructively and require human approval before altering history?

### SCAR-GIT-30: Pure Git Mode and Hosting Tool Discovery

- **Wound**: An agent attempts to run `gh pr create` or `gh pr checks` in an SSH-only or non-GitHub repository and stalls at Target 60 or Target 70 even though Git push succeeded.
- **Trap**: Assuming every repository uses authenticated GitHub CLI tooling instead of checking whether `gh` is authenticated.
- **Permanent Reflex**: Check `gh auth status` at Target 15. If `gh` is unavailable or unauthenticated, use Pure Git Mode: skip remote PR creation at Target 60, run full local repository tests at Target 70, present local landing readiness at Target 75, and squash-merge on `main` at Target 80 using standard Git commands.
- **Socratic Probe**: If the environment lacks authenticated GitHub CLI tooling, will commands like `gh pr create` stall the workflow? Can you detect tool availability early and fall back smoothly to pure Git operations?
