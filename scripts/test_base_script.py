#!/usr/bin/env python3
"""Hermetic unit tests for BaseScript lifecycle (SCAR-ARCH-05)."""

import io
import os
import sys
import unittest

# Ensure scripts directory and repo root are on sys.path for direct execution
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
  sys.path.insert(0, _SCRIPTS_DIR)
_REPO_ROOT = os.path.dirname(_SCRIPTS_DIR)
if _REPO_ROOT not in sys.path:
  sys.path.insert(0, _REPO_ROOT)

from base_script import BaseScript


class ConcreteSuccessScript(BaseScript):

  def __init__(self):
    super().__init__()
    self.log = []

  def parse_args(self, args=None):
    super().parse_args(args)
    self.log.append("parse_args")

  def setup(self):
    self.log.append("setup")

  def run(self):
    self.log.append("run")
    self.stdout.write("Operation complete\n")
    return 0

  def cleanup(self, exit_code: int):
    self.log.append(f"cleanup:{exit_code}")


class ConcreteCustomExitScript(BaseScript):

  def __init__(self, exit_code: int = 42):
    super().__init__()
    self.target_code = exit_code
    self.cleaned_with = None

  def run(self):
    return self.target_code

  def cleanup(self, exit_code: int):
    self.cleaned_with = exit_code


class ConcreteFailingRunScript(BaseScript):

  def __init__(self):
    super().__init__()
    self.cleaned_with = None

  def run(self):
    raise RuntimeError("Intentional failure in run()")

  def cleanup(self, exit_code: int):
    self.cleaned_with = exit_code


class ConcreteFailingSetupScript(BaseScript):

  def __init__(self):
    super().__init__()
    self.cleaned_with = None

  def setup(self):
    raise ValueError("Intentional failure in setup()")

  def cleanup(self, exit_code: int):
    self.cleaned_with = exit_code


class CustomExitError(Exception):
  exit_code = 7


class NonIntegerExitError(Exception):
  exit_code = "not-an-integer"


class NoneExitError(Exception):
  exit_code = None


class ConcreteCustomExceptionScript(BaseScript):

  def run(self):
    raise CustomExitError("Custom exception with exit code 7")


class ConcreteNonIntegerExceptionScript(BaseScript):

  def __init__(self, exc):
    super().__init__()
    self.exc = exc

  def run(self):
    raise self.exc


class TestBaseScript(unittest.TestCase):

  def test_default_lifecycle_execution(self):
    """Verifies that execute() runs parse_args, setup, run, and cleanup in order."""
    script = ConcreteSuccessScript()
    out = io.StringIO()
    err = io.StringIO()

    exit_code = script.execute(args=["--test"], stdout=out, stderr=err)

    self.assertEqual(exit_code, 0)
    self.assertEqual(
        script.log, ["parse_args", "setup", "run", "cleanup:0"]
    )
    self.assertEqual(out.getvalue(), "Operation complete\n")
    self.assertEqual(err.getvalue(), "")

  def test_stream_redirection_isolation(self):
    """Verifies output goes exclusively to injected streams without leaking to OS streams."""
    out = io.StringIO()
    err = io.StringIO()
    script = ConcreteSuccessScript()

    orig_stdout = sys.stdout
    orig_stderr = sys.stderr
    try:
      # Poison OS streams to guarantee neither is touched
      sys.stdout = None
      sys.stderr = None
      code = script.execute(args=[], stdout=out, stderr=err)
    finally:
      sys.stdout = orig_stdout
      sys.stderr = orig_stderr

    self.assertEqual(code, 0)
    self.assertIn("Operation complete", out.getvalue())

  def test_custom_exit_code_handling(self):
    """Verifies custom exit codes are returned by execute() and passed to cleanup()."""
    script = ConcreteCustomExitScript(exit_code=42)
    out = io.StringIO()
    err = io.StringIO()

    exit_code = script.execute(args=[], stdout=out, stderr=err)

    self.assertEqual(exit_code, 42)
    self.assertEqual(script.cleaned_with, 42)

  def test_run_returning_none_defaults_to_zero(self):
    """Verifies run() returning None is treated as exit code 0."""
    class NoneScript(BaseScript):
      def __init__(self):
        super().__init__()
        self.cleaned_with = None

      def run(self):
        return None

      def cleanup(self, exit_code: int):
        self.cleaned_with = exit_code

    script = NoneScript()
    exit_code = script.execute(args=[], stdout=io.StringIO(), stderr=io.StringIO())
    self.assertEqual(exit_code, 0)
    self.assertEqual(script.cleaned_with, 0)

  def test_exception_in_run_trapped(self):
    """Verifies exceptions in run() are trapped, written to stderr, and cleanup is executed."""
    script = ConcreteFailingRunScript()
    out = io.StringIO()
    err = io.StringIO()

    exit_code = script.execute(args=[], stdout=out, stderr=err)

    self.assertEqual(exit_code, 1)
    self.assertEqual(script.cleaned_with, 1)
    self.assertIn("Intentional failure in run()", err.getvalue())

  def test_exception_in_setup_trapped(self):
    """Verifies exceptions in setup() are trapped, written to stderr, and cleanup is executed."""
    script = ConcreteFailingSetupScript()
    out = io.StringIO()
    err = io.StringIO()

    exit_code = script.execute(args=[], stdout=out, stderr=err)

    self.assertEqual(exit_code, 1)
    self.assertEqual(script.cleaned_with, 1)
    self.assertIn("Intentional failure in setup()", err.getvalue())

  def test_custom_exception_exit_code(self):
    """Verifies exception with exit_code attribute is mapped correctly."""
    script = ConcreteCustomExceptionScript()
    out = io.StringIO()
    err = io.StringIO()

    exit_code = script.execute(args=[], stdout=out, stderr=err)

    self.assertEqual(exit_code, 7)
    self.assertIn("Custom exception with exit code 7", err.getvalue())

  def test_custom_exception_non_integer_exit_code(self):
    """Verifies non-integer exit_code attributes safely fall back to 1 as int."""
    for bad_exc in (
        NonIntegerExitError("String exit code"),
        NoneExitError("None exit code"),
    ):
      script = ConcreteNonIntegerExceptionScript(bad_exc)
      out = io.StringIO()
      err = io.StringIO()

      exit_code = script.execute(args=[], stdout=out, stderr=err)

      self.assertIsInstance(exit_code, int)
      self.assertEqual(exit_code, 1)

  def test_parse_args_custom_list(self):
    """Verifies custom arguments list is received by parse_args()."""
    class ArgScript(BaseScript):
      def parse_args(self, args=None):
        super().parse_args(args)
        self.parsed = args

      def run(self):
        return len(self.parsed)

    script = ArgScript()
    exit_code = script.execute(
        args=["alpha", "beta", "gamma"],
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    self.assertEqual(exit_code, 3)
    self.assertEqual(script.parsed, ["alpha", "beta", "gamma"])

  def test_fallback_to_sys_argv(self):
    """Verifies execute() falls back to sys.argv[1:] when args is None."""
    class ArgScript(BaseScript):
      def run(self):
        return 0

    script = ArgScript()
    orig_argv = sys.argv
    try:
      sys.argv = ["script.py", "foo", "bar"]
      script.execute(stdout=io.StringIO(), stderr=io.StringIO())
      self.assertEqual(script.raw_args, ["foo", "bar"])
    finally:
      sys.argv = orig_argv


if __name__ == "__main__":
  unittest.main()
