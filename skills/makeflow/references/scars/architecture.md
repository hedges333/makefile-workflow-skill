# Architecture and Pattern Scars

This reference manual documents universal architecture and software design pattern scars (`SCAR-ARCH-*`). These rules enforce testability, object-oriented design, decoupling, and lifecycle boundaries across all supported programming languages.

## Scars in this Category

| ID | Title | Scope |
| :--- | :--- | :--- |
| `SCAR-ARCH-05` | Testable Object-Oriented Script Template (BaseScript Pattern) | Script Lifecycles & In-Memory Testability |

---

### SCAR-ARCH-05: Testable Object-Oriented Script Template (BaseScript Pattern)

- **Wound**: Procedural CLI scripts and `main` entry points with sprawling imperative blocks cannot be unit-tested hermetically in memory. Testing them requires spawning slow, fragile OS subprocesses (`exec`, `spawn`, `Popen`) or mutating module-level/global state. In unhandled error scenarios, scripts terminate the entire test runner or subagent process with `sys.exit()`, `process.exit()`, or `os.Exit()`, aborting test execution cascades.
- **Trap**: Writing procedural script files that pass long argument lists through helper functions or rely on global variables. Calling process-terminating exit functions directly inside business logic.
- **Permanent Reflex**: Encapsulate script and entry-point logic in cohesive, testable class objects or lifecycle runners implementing the **Template Method** pattern (`BaseScript`). Structure execution into clear lifecycle hooks: `parse_args`, `setup`, `run`, and `cleanup` with fatal exception trapping. Inject standard I/O streams (`stdout`, `stderr`) to allow in-memory stream assertion without OS stream hijacking. Keep executable CLI files to thin two-line wrappers (`sys.exit(ScriptClass().execute())`, `exit(Script::run())`, etc.).
- **Socratic Probe**: Can this script's execution lifecycle be tested hermetically in memory without invoking subprocesses or relying on module-level globals?
