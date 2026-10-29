# 12. Request History Ledger

This manual details the persistent history ledger that records completed work over time.

## 1. Purpose of the Request History Ledger

Conversations end, but repositories endure. The Request History Ledger provides:
1. A permanent record of tickets resolved by AI agents.
2. An index of branches, commits, pull requests, and tests added.
3. A catalog of failure vaccines codified during work.
4. A quick way for users to ask "What tasks have we completed so far?"

## 2. Location & File Formats

Maintain history inside the `.workflow/` directory at the repository root:
- `.workflow/history.json`: Machine-readable array of task records.
- `.workflow/history.md`: Human-readable markdown log.

### Machine-Readable Schema (`history.json`)

```json
[
  {
    "id": "#42",
    "issue_url": "https://github.com/owner/repo/issues/42",
    "title": "Fix login redirect timeout on HTTPS",
    "request": "Handle 301/308 redirects without dropping authorization header",
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
      "SCAR-AUTH-02: Preserve Authorization header on same-origin 308 redirects"
    ]
  },
  {
    "id": "#1",
    "issue_url": null,
    "title": "Add health check endpoint",
    "request": "Implement /api/health endpoint returning uptime and database ping",
    "branch": "feat/1-health-check",
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

### Human-Readable Log Format (`history.md`)

```markdown
# Repository Request History Log

| Date | Ticket / Issue | Summary | Branch | PR | Tests | Scars Earned |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-10-29 | [#42](https://github.com/owner/repo/issues/42) | Fix login redirect timeout on HTTPS | `fix/42-login-redirect` | [#45](https://github.com/owner/repo/pull/45) | +3 | `SCAR-AUTH-02` |
| 2026-10-29 | #1 (Local) | Add health check endpoint | `feat/1-health-check` | [#46](https://github.com/owner/repo/pull/46) | +2 | - |
```

## 3. Maintenance Protocol (Target 90)

During Target 90 post-mortems:
1. Create the `.workflow/` directory if it does not exist.
2. Read existing `.workflow/history.json` (or initialize with `[]`).
3. Append the completed task record.
4. Prepend or append the summary row in `.workflow/history.md`.
5. Stage both files and include them in the terminal commit or release documentation.
