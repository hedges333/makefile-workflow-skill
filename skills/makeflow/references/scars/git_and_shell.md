# Git and Shell Execution Scars

This reference manual documents Git operations and shell execution scars (`SCAR-GIT-*` and `SCAR-SH-*`). These rules protect repository trees, history integrity, and shell command tokenization.

## Scars in this Category

| ID | Title | Scope |
| :--- | :--- | :--- |
| `SCAR-SH-01` | Prefer Temporary Script Files Over Complex Shell Quoting | Command Quoting & Script Isolation |
| `SCAR-SH-03` | Shell Redirection and Comment Stripping | Pre-Tool Guard Parsing |
| `SCAR-GIT-20` | Pre-Push Merge Check | Branch Conflict Prevention |
| `SCAR-GIT-25` | Destructive Git Command Protection | Working Tree & Branch Safety |
| `SCAR-GIT-30` | Pure Git Mode and Repository-Scoped Hosting Discovery | Non-GitHub / Offline Workflows |

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

### SCAR-GIT-30: Pure Git Mode and Repository-Scoped Hosting Discovery

- **Wound**: An agent checks global `gh auth status` on a machine where GitHub CLI is logged in. The agent treats a local checkout or non-GitHub repository as a GitHub repo. The agent then stalls at Target 60 or Target 70 on failing `gh pr create` calls.
- **Trap**: Relying on global `gh auth status` rather than verifying repository remote origin and reachability.
- **Permanent Reflex**: At Target 15, discover hosting mode for the current repository. Verify that `git remote get-url origin` points to GitHub. Check that `gh auth status` succeeds. Verify repository reachability with `gh repo view`. If any check fails, record `HOSTING_MODE: PURE_GIT`. Skip remote PR creation at Target 60. Run full local test sweeps at Target 70. Present local test results at Target 75. Squash-merge locally on `main` at Target 80.
- **Socratic Probe**: Does this repository have a remote pointing to GitHub with working `gh repo view` access? If `gh` is globally logged in, will checking repository remote origin prevent failing downstream GitHub CLI calls?
