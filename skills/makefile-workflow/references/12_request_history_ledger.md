# 12. Request History Ledger

This manual describes the version-controlled history ledger that records completed tickets over the life of a repository.

## 1. Purpose of the Ledger

Chat sessions end, but the repository remains. The Request History Ledger records four things:

1. Every ticket completed through the Makefile Workflow.
2. Branch names, commit hashes, pull request links, and added test counts.
3. Synthetic Scars (process rules learned from past failures) earned during each task.
4. Next local task numbers when creating branches for ad-hoc chat requests.

## 2. File Locations and Formats

Store both ledger files inside `.workflow/` at the repository root:

- `.workflow/history.json`: Machine-readable JSON array of completed ticket records.
- `.workflow/history.md`: Human-readable markdown summary table.

### JSON Schema (`history.json`)

```json
[
  {
    "id": "#42",
    "issue_url": "https://github.com/owner/repo/issues/42",
    "title": "Fix login redirect timeout on HTTPS",
    "request": "Handle 301 and 308 redirects without dropping authorization header",
    "branch": "fix/42-login-redirect",
    "subprojects": ["backend"],
    "started_at": "2026-10-29T10:00:00Z",
    "completed_at": "2026-10-29T10:45:00Z",
    "commit_sha": "a1b2c3d4e5f6789012345678901234567890abcd",
    "pr_number": 45,
    "pr_url": "https://github.com/owner/repo/pull/45",
    "closes_issue": true,
    "tests_added": 3,
    "scars_earned": [
      "SCAR-AUTH-02: Keep Authorization header on same-origin 308 redirects"
    ]
  },
  {
    "id": "#1",
    "issue_url": null,
    "title": "Add health endpoint",
    "request": "Add /api/health endpoint returning uptime and database ping",
    "branch": "feat/1-health-endpoint",
    "subprojects": ["backend"],
    "started_at": "2026-10-29T11:00:00Z",
    "completed_at": "2026-10-29T11:30:00Z",
    "commit_sha": "f1e2d3c4b5a6789012345678901234567890ef01",
    "pr_number": 46,
    "pr_url": "https://github.com/owner/repo/pull/46",
    "closes_issue": false,
    "tests_added": 2,
    "scars_earned": []
  }
]
```

### Markdown Table Format (`history.md`)

```markdown
# Repository Request History Log

| Date | Ticket | Summary | Branch | PR | Tests | Scars Earned |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-10-29 | [#42](https://github.com/owner/repo/issues/42) | Fix login redirect timeout on HTTPS | `fix/42-login-redirect` | [#45](https://github.com/owner/repo/pull/45) | +3 | `SCAR-AUTH-02` |
| 2026-10-29 | #1 (Local) | Add health endpoint | `feat/1-health-endpoint` | [#46](https://github.com/owner/repo/pull/46) | +2 | - |
```

## 3. Update Steps at Target 90

Run these steps during Target 90 after a pull request merges:

1. Create `.workflow/` if the directory does not exist.
2. Read `.workflow/history.json`, or start with `[]` when the file is new.
3. Append the completed ticket object to `.workflow/history.json`.
4. Add a matching summary row to `.workflow/history.md`.
5. Commit the updated ledger files when the project tracks `.workflow/history.*` in Git.
