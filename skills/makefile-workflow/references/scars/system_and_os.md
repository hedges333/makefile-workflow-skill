# System, Environment, and OS Scars

This reference manual documents operating system, filesystem, and runtime environment scars (`SCAR-SYS-*` and `SCAR-ENV-*`).

## Scars in this Category

| ID | Title | Scope |
| :--- | :--- | :--- |
| `SCAR-ENV-04` | Shared Workspace Umask Permissions | Multi-User Collaboration & File Modes |

---

### SCAR-ENV-04: Shared Workspace Umask Permissions

- **Wound**: Collaborator user accounts or paired agents fail to edit or overwrite newly created workspace files with `Permission denied (EACCES)`.
- **Trap**: Creating files with default restrictive umask `0022` (read-only for group) in collaborative multi-user or service-account environments.
- **Permanent Reflex**: Set umask to `0002` in shared group workspaces so team and collaborator accounts retain group write privileges on newly created files.
