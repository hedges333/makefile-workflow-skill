# Testing and Verification Scars

This reference manual documents testing and verification scars (`SCAR-TEST-*`). These rules govern test environment isolation, hermetic execution, and test execution discipline.

## Scars in this Category

| ID | Title | Scope |
| :--- | :--- | :--- |
| `SCAR-TEST-05` | Isolated Test Environments | Test Database & Environment Safety |
| `SCAR-TEST-08` | Two-Tier Test Isolation | Hermetic Unit vs Integration Fixtures |
| `SCAR-TEST-09` | Fail-Fast Targeted TDD Loop | Red-Green Test Iteration (`-x -v`) |

---

### SCAR-TEST-05: Isolated Test Environments

- **Wound**: Automated tests connect to a shared or production database and alter live rows.
- **Trap**: Running test suites with default environment variables instead of dedicated test database credentials.
- **Permanent Reflex**: Point all tests to `*_test` databases, in-memory stores, or mock fixtures. Never connect tests to production databases.

### SCAR-TEST-08: Two-Tier Test Isolation (Hermetic Unit vs Integration Fixtures)

- **Wound**: An unprivileged test runner or CI container fails session-level database DDL or network initialization in a root fixture, causing the entire test suite to crash before running any pure unit tests.
- **Trap**: Attaching database connections, socket initialization, or schema migrations to global `autouse=True` session fixtures instead of isolating them behind explicit markers.
- **Permanent Reflex**: Partition test suites into two tiers: Tier 1 hermetic unit tests with zero external daemon or socket dependencies (allowing self-contained ephemeral loopback sockets such as `127.0.0.1:0` or temporary Unix domain sockets in `tmp_path`), and Tier 2 marked integration tests that verify external dependencies during pre-flight. Never attach live database connections or unmanaged network sockets to un-isolated session fixtures.

### SCAR-TEST-09: Fail-Fast Targeted TDD Loop (pytest -x -v)

- **Wound**: Running a large test suite during active debugging generates hundreds of cascading tracebacks, exhausting context limits and obscuring the initial defect.
- **Trap**: Running broad test suites without fail-fast flags while attempting to iterate on a single failing test.
- **Permanent Reflex**: Use fail-fast flags (`pytest -x -v` or language equivalent) during active Red-Green TDD cycles. Iterate exclusively on the targeted failing test until green before running the full regression suite.
