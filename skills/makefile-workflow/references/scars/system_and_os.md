# System, Environment, and OS Scars

This reference manual documents operating system, filesystem, and runtime environment scars (`SCAR-SYS-*` and `SCAR-ENV-*`).

## Scars in this Category

| ID | Title | Scope |
| :--- | :--- | :--- |
| `SCAR-ENV-04` | Shared Workspace Umask Permissions | Multi-User Collaboration & File Modes |
| `SCAR-SYS-05` | Cross-User File Promotion | Multi-User File System Operations |
| `SCAR-SYS-06` | Native Runtime Environment Path Pre-Flight | Native Compiled Extensions & Temp Directories |

---

### SCAR-ENV-04: Shared Workspace Umask Permissions

- **Wound**: Collaborator user accounts or paired agents fail to edit or overwrite newly created workspace files with `Permission denied (EACCES)`.
- **Trap**: Creating files with default restrictive umask `0022` (read-only for group) in collaborative multi-user or service-account environments.
- **Permanent Reflex**: Set umask to `0002` in shared group workspaces so team and collaborator accounts retain group write privileges on newly created files.

---

### SCAR-SYS-05: Cross-User File Promotion (`shutil.copyfile` over `copy2` / `copystat`)

- **Wound**: Promoting or syncing files across service accounts or system users crashes with `PermissionError: [Errno 1] EPERM`.
- **Trap**: Assuming standard library helpers like `shutil.copy2` or `shutil.copytree` work across user boundaries. These functions invoke `copystat` (`os.chmod` and `os.utime`). These system calls require ownership privileges on destination files.
- **Permanent Reflex**: When copying files across user accounts, copy file contents only with `shutil.copyfile`. Create destination directories with caller permissions instead of copying file ownership.

---

### SCAR-SYS-06: Native Runtime Environment Path Pre-Flight (`TMPDIR` / `validate_runtime_path`)

- **Wound**: Compiled C and C++ libraries, GPU runtimes, or native database drivers crash with a silent segmentation fault during startup without a Python stack trace.
- **Trap**: Developers assume native compiled extensions validate paths in environment variables like `TMPDIR` or `CACHE_DIR` and raise clean exceptions.
- **Permanent Reflex**: If you launch native runtimes, verify that target cache and temporary directories exist and are writable using `validate_runtime_path`. If an environment path is missing or unwritable, sanitize environment variables using `sanitize_runtime_env` with verified fallback directories.
