## Summary
<!-- Describe what changed and why in short active sentences. -->

## Linked Issue
Closes #<!-- Issue number -->

---

## Six Pillars Checklist

Make sure that every item passes before you request merge:

- [ ] Pillar 1 (Intent and Scope): Changes match the ticket scope with no unrelated edits.
- [ ] Pillar 2 (Verification): Failing tests ran before code edits, and the full test suite passes.
- [ ] Pillar 3 (Architecture): New code matches existing patterns, names, and type contracts.
- [ ] Pillar 4 (Blast Radius): Zero production databases or live files are touched, and subproject boundaries hold.
- [ ] Pillar 5 (Readability): The diff is clear and has no debug output or commented-out code.
- [ ] Pillar 6 (Error Handling): The code handles null pointers, empty inputs, timeouts, and cleanup.

---

## Test Commands Run
<!-- Paste the exact commands that you ran, for example `make test` or `pytest`. -->
```bash
make test
```
