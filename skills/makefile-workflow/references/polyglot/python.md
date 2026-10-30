# Polyglot Stack Guide: Python

This guide covers detection markers, test and lint commands, smoke test templates, and database isolation for Python.

## 1. Detection Markers

Look for these files when scanning a Python subproject:

- `pyproject.toml`, `requirements.txt`, `setup.py`, `Pipfile`, `tox.ini`

## 2. Standard Commands

Run these commands inside the Python subproject directory:

- Targeted Test: `pytest <subproject>/tests/ -v` (or `python3 -m unittest discover <subproject>/tests`)
- Format: `ruff format --check .` or `black --check .`
- Lint: `ruff check .` or `flake8 .`

## 3. Smoke Test Template

If the subproject has no test directory, create `tests/test_smoke.py`:

```python
"""Smoke test template for Python subprojects."""


def test_smoke():
  """Makes sure that the test runner executes cleanly."""
  assert True
```

## 4. Test Database and Network Isolation

Follow four isolation rules in Python tests:

1. Use SQLite in-memory connections (`sqlite:///:memory:`) for unit tests.
2. For PostgreSQL or MySQL integration tests, set `TEST_DATABASE_URL=postgres://user:pass@localhost:5432/<app>_test`.
3. Never point `DATABASE_URL` to staging or production hosts.
4. Mock external HTTP requests with `pytest-mock` or `unittest.mock`.
