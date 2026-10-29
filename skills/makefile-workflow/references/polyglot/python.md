# Polyglot Stack Guide: Python

This manual details toolchains, test scaffolding, and database isolation for Python.

## 1. Detection Markers
- `pyproject.toml`, `requirements.txt`, `setup.py`, `Pipfile`, `tox.ini`

## 2. Standard Commands
- **Targeted Test**: `pytest <subproject>/tests/ -v` (fallback: `python -m unittest discover <subproject>/tests`)
- **Format**: `ruff format .` or `black .`
- **Lint**: `ruff check .` or `flake8 .`

## 3. Boilerplate Test Scaffolding
If no test directory exists, create `tests/test_smoke.py`:
```python
"""Smoke test scaffold for Python projects."""


def test_smoke():
  """Verifies that the test harness runs and basic imports succeed."""
  assert True
```

## 4. Test Database Isolation
1. Use SQLite in-memory databases (`sqlite:///:memory:`) for fast unit tests.
2. For PostgreSQL/MySQL integration tests, set `TEST_DATABASE_URL=postgres://user:pass@localhost:5432/<app>_test`.
3. Never point `DATABASE_URL` to production or staging hosts.
4. Use `pytest-mock` or `unittest.mock` to mock external API requests.
