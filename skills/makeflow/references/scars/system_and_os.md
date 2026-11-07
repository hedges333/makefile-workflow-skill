# System, Environment, and OS Scars

This reference manual documents operating system, filesystem, and runtime environment scars (`SCAR-SYS-*` and `SCAR-ENV-*`).

## Scars in this Category

| ID | Title | Scope |
| :--- | :--- | :--- |
| `SCAR-ENV-04` | Shared Workspace Umask Permissions | Multi-User Collaboration & File Modes |
| `SCAR-SYS-05` | Cross-User File Promotion | Multi-User File System Operations |
| `SCAR-SYS-06` | Native Runtime Environment Path Pre-Flight | Native Compiled Extensions & Temp Directories |
| `SCAR-SYS-07` | POSIX Signal Trapping for Long-Running Workers | Signal Handling, Worker Cleanup & Lockfiles |
| `SCAR-SYS-08` | Atomic Directory-Based Mutual Exclusion Locks | Inter-Process Concurrency & Mutual Exclusion |

---

### SCAR-ENV-04: Shared Workspace Umask Permissions

- **Wound**: Collaborator user accounts or paired agents fail to edit or overwrite newly created workspace files with `Permission denied (EACCES)`.
- **Trap**: Creating files with default restrictive umask `0022` (read-only for group) in collaborative multi-user or service-account environments.
- **Permanent Reflex**: Set umask to `0002` in shared group workspaces so team and collaborator accounts retain group write privileges on newly created files.
- **Socratic Probe**: If you create files with default restrictive permissions, will collaborator accounts or paired agents be unable to edit them? Would setting a group-writable umask allow seamless collaboration without permission errors?

---

### SCAR-SYS-05: Cross-User File Promotion (`shutil.copyfile` over `copy2` / `copystat`)

- **Wound**: Promoting or syncing files across service accounts or system users crashes with `PermissionError: [Errno 1] EPERM`.
- **Trap**: Assuming standard library helpers like `shutil.copy2` or `shutil.copytree` work across user boundaries. These functions invoke `copystat` (`os.chmod` and `os.utime`). These system calls require ownership privileges on destination files.
- **Permanent Reflex**: When copying files across user accounts, copy file contents only with `shutil.copyfile`. Create destination directories with caller permissions instead of copying file ownership.
- **Socratic Probe**: When copying files across different system users, will copying ownership metadata trigger permission errors? Would streaming content bytes with `shutil.copyfile` allow safe file promotion under caller permissions?

---

### SCAR-SYS-06: Native Runtime Environment Path Pre-Flight (`TMPDIR` / `validate_runtime_path`)

- **Wound**: Compiled C and C++ libraries, GPU runtimes, or native database drivers crash with a silent segmentation fault during startup without a Python stack trace.
- **Trap**: Developers assume native compiled extensions validate paths in environment variables like `TMPDIR` or `CACHE_DIR` and raise clean exceptions.
- **Permanent Reflex**: If you launch native runtimes, verify that target cache and temporary directories exist and are writable using `validate_runtime_path`. If an environment path is missing or unwritable, sanitize environment variables using `sanitize_runtime_env` with verified fallback directories.
- **Socratic Probe**: If a native compiled library encounters an invalid or missing temporary directory, could it crash with a silent segmentation fault? Have you verified that environment paths exist and are writable before spawning native processes?

---

### SCAR-SYS-07: POSIX Signal Trapping for Long-Running Workers (SIGTERM / SIGINT)

- **Wound**: Background worker processes, daemons, and test harnesses leave orphaned lockfiles, unclosed sockets, and zombie child processes when killed by SIGTERM or SIGINT. Workers deadlock during shutdown if cleanup hangs on child processes.
- **Trap**: Assuming processes always terminate through normal language exit handlers (`atexit` or `finally` blocks). Signals bypass `finally` blocks unless intercepted. Cleanup handlers can also deadlock if child processes ignore termination or become zombies.
- **Permanent Reflex**: Intercept POSIX termination signals (`SIGTERM`, `SIGINT`) in long-running workers using `SignalTrap`. Register cleanup callbacks in reverse order (LIFO), unlink lockfiles, terminate child processes with timeout escalation to kill, reap zombies with non-blocking waitpid, and force-exit immediately if repeated signals arrive during shutdown.
- **Socratic Probe**: If this worker receives an asynchronous SIGTERM or SIGINT, will it leave orphaned lockfiles, deadlocked child processes, or zombie processes? Have you trapped POSIX signals, registered LIFO cleanup routines, added child process escalation, reaped zombies, and enabled repeated-signal force-exit fallbacks?

---

### SCAR-SYS-08: Atomic Directory-Based Mutual Exclusion Locks (`mkdir` over lockfile)

- **Wound**: Concurrent worker processes enter critical sections simultaneously or corrupt state because lockfile existence checks race with creation.
- **Trap**: Using regular file checks like `os.path.exists` followed by `open(..., "w")`. Non-atomic lockfile creation allows race conditions across processes.
- **Permanent Reflex**: Use atomic directory creation with `os.mkdir` for mutual exclusion locks. Catch `FileExistsError` to detect lock contention. Clean up the lock directory with `os.rmdir` on exit or signal.
- **Socratic Probe**: If multiple workers check and create a lockfile simultaneously, will race conditions cause state corruption? Would atomic directory creation with `os.mkdir` guarantee exclusive mutual exclusion?
