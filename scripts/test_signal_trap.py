#!/usr/bin/env python3
"""Unit tests for signal_trap.py (SCAR-SYS-07)."""

import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest

# Ensure scripts directory is on sys.path for direct execution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from signal_trap import SignalTrap


class TestSignalTrap(unittest.TestCase):
  """Comprehensive test suite for POSIX signal trapping and cleanup."""

  def setUp(self):
    self.temp_dir = tempfile.TemporaryDirectory()
    self.test_root = self.temp_dir.name
    # Save original handlers for test signals to guarantee restoration
    self._orig_sigterm = signal.getsignal(signal.SIGTERM)
    self._orig_sigint = signal.getsignal(signal.SIGINT)

  def tearDown(self):
    # Ensure signal handlers are restored even if a test failed
    try:
      signal.signal(signal.SIGTERM, self._orig_sigterm)
    except (ValueError, OSError):
      pass
    try:
      signal.signal(signal.SIGINT, self._orig_sigint)
    except (ValueError, OSError):
      pass
    self.temp_dir.cleanup()

  def test_initialization_and_signal_registration(self):
    """TestCase 1: SignalTrap initialization and registration of SIGTERM / SIGINT."""
    trap = SignalTrap()
    self.assertIn(signal.SIGTERM, trap.signals)
    self.assertIn(signal.SIGINT, trap.signals)
    self.assertFalse(trap.is_installed)

    trap.install()
    self.assertTrue(trap.is_installed)
    self.assertEqual(signal.getsignal(signal.SIGTERM), trap.handle_signal)
    self.assertEqual(signal.getsignal(signal.SIGINT), trap.handle_signal)

    trap.restore()
    self.assertFalse(trap.is_installed)

  def test_restoration_of_original_signal_handlers(self):
    """TestCase 2: Restoration of original signal handlers upon exit or restore()."""
    def custom_handler(_sig, _frame):
      pass

    signal.signal(signal.SIGTERM, custom_handler)
    self.assertEqual(signal.getsignal(signal.SIGTERM), custom_handler)

    with SignalTrap() as trap:
      self.assertEqual(signal.getsignal(signal.SIGTERM), trap.handle_signal)

    # Upon context exit, custom handler must be restored
    self.assertEqual(signal.getsignal(signal.SIGTERM), custom_handler)

  def test_cleanup_callbacks_lifo_order(self):
    """TestCase 3: Cleanup callbacks execute in reverse registration order (LIFO)."""
    execution_order = []

    trap = SignalTrap(exit_on_signal=False)
    trap.register_cleanup(lambda: execution_order.append("first"))
    trap.register_cleanup(lambda: execution_order.append("second"))
    trap.register_cleanup(lambda: execution_order.append("third"))

    errors = trap.execute_cleanups()
    self.assertEqual(errors, [])
    self.assertEqual(execution_order, ["third", "second", "first"])

  def test_exception_isolation_in_cleanups(self):
    """TestCase 4: Exception in one callback does not abort remaining cleanups."""
    execution_order = []

    def failing_callback():
      execution_order.append("failing")
      raise RuntimeError("Cleanup failure simulation")

    trap = SignalTrap(exit_on_signal=False)
    trap.register_cleanup(lambda: execution_order.append("first"))
    trap.register_cleanup(failing_callback)
    trap.register_cleanup(lambda: execution_order.append("third"))

    errors = trap.execute_cleanups()
    # All callbacks must have executed in LIFO order despite the exception
    self.assertEqual(execution_order, ["third", "failing", "first"])
    self.assertEqual(len(errors), 1)
    self.assertEqual(errors[0][0], failing_callback)
    self.assertIsInstance(errors[0][1], RuntimeError)

  def test_lockfile_removal_on_context_exit(self):
    """TestCase 5: Lockfile registration and automatic removal upon context exit."""
    lockfile_path = os.path.join(self.test_root, "worker.lock")
    with open(lockfile_path, "w", encoding="utf-8") as f:
      f.write("12345")
    self.assertTrue(os.path.exists(lockfile_path))

    with SignalTrap() as trap:
      trap.register_lockfile(lockfile_path)
      self.assertTrue(os.path.exists(lockfile_path))

    # Lockfile must be deleted on context exit
    self.assertFalse(os.path.exists(lockfile_path))

  def test_lockfile_removal_on_signal(self):
    """TestCase 6: Lockfile removal on signal delivery."""
    lockfile_path = os.path.join(self.test_root, "worker_sig.lock")
    with open(lockfile_path, "w", encoding="utf-8") as f:
      f.write("54321")

    trap = SignalTrap(exit_on_signal=False)
    trap.install()
    trap.register_lockfile(lockfile_path)

    # Deliver simulated SIGTERM
    trap.handle_signal(signal.SIGTERM, None)
    self.assertFalse(os.path.exists(lockfile_path))
    self.assertEqual(trap.signal_count, 1)
    self.assertEqual(trap.last_signal, signal.SIGTERM)
    trap.restore()

  def test_signal_idempotency(self):
    """TestCase 7: Idempotency when multiple signals arrive."""
    calls = []
    trap = SignalTrap(exit_on_signal=False)
    trap.register_cleanup(lambda: calls.append("cleanup"))

    trap.handle_signal(signal.SIGTERM, None)
    trap.handle_signal(signal.SIGTERM, None)
    trap.handle_signal(signal.SIGINT, None)

    # Cleanups must run exactly once
    self.assertEqual(calls, ["cleanup"])
    self.assertEqual(trap.signal_count, 3)

  def test_restore_idempotency(self):
    """TestCase 8: restore() is safe to call multiple times."""
    trap = SignalTrap()
    trap.install()
    trap.restore()
    # Calling restore again must not raise any error
    trap.restore()
    self.assertFalse(trap.is_installed)

  def test_missing_lockfile_removal_graceful(self):
    """TestCase 9: Missing lockfile does not cause errors during cleanup."""
    lockfile_path = os.path.join(self.test_root, "nonexistent.lock")
    trap = SignalTrap(exit_on_signal=False)
    trap.register_lockfile(lockfile_path)
    errors = trap.remove_lockfiles()
    self.assertEqual(errors, [])

  def test_subprocess_end_to_end_sigterm(self):
    """TestCase 10: End-to-end subprocess signal trapping with SIGTERM."""
    lockfile_path = os.path.join(self.test_root, "subproc_term.lock")
    ready_file_path = os.path.join(self.test_root, "subproc_term.ready")
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "signal_trap.py")

    cmd = [
        sys.executable,
        script_path,
        "--lockfile",
        lockfile_path,
        "--ready-file",
        ready_file_path,
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
      # Wait for ready sentinel file
      for _ in range(50):
        if os.path.exists(ready_file_path) and os.path.exists(lockfile_path):
          break
        time.sleep(0.1)

      self.assertTrue(os.path.exists(ready_file_path), "Subprocess did not signal readiness")
      self.assertTrue(os.path.exists(lockfile_path), "Lockfile was not created")
      self.assertIsNone(proc.poll(), "Subprocess exited prematurely")

      # Send SIGTERM to child process
      proc.send_signal(signal.SIGTERM)

      # Wait for child process to terminate cleanly
      retcode = proc.wait(timeout=5)
      # POSIX convention: 128 + 15 = 143, or -SIGTERM (-15)
      self.assertIn(retcode, (143, -signal.SIGTERM, 0))

      # Verify lockfile was removed by SignalTrap handler
      self.assertFalse(
          os.path.exists(lockfile_path),
          "Lockfile must be unlinked upon SIGTERM",
      )
    finally:
      if proc.stdout:
        proc.stdout.close()
      if proc.stderr:
        proc.stderr.close()
      if proc.poll() is None:
        proc.kill()
        proc.wait()

  def test_subprocess_end_to_end_sigint(self):
    """TestCase 11: End-to-end subprocess signal trapping with SIGINT."""
    lockfile_path = os.path.join(self.test_root, "subproc_int.lock")
    ready_file_path = os.path.join(self.test_root, "subproc_int.ready")
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "signal_trap.py")

    cmd = [
        sys.executable,
        script_path,
        "--lockfile",
        lockfile_path,
        "--ready-file",
        ready_file_path,
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
      for _ in range(50):
        if os.path.exists(ready_file_path) and os.path.exists(lockfile_path):
          break
        time.sleep(0.1)

      self.assertTrue(os.path.exists(ready_file_path), "Subprocess did not signal readiness")
      self.assertTrue(os.path.exists(lockfile_path), "Lockfile was not created")
      self.assertIsNone(proc.poll(), "Subprocess exited prematurely")

      # Send SIGINT to child process
      proc.send_signal(signal.SIGINT)

      retcode = proc.wait(timeout=5)
      # POSIX convention: 128 + 2 = 130, or -SIGINT (-2)
      self.assertIn(retcode, (130, -signal.SIGINT, 0))

      self.assertFalse(
          os.path.exists(lockfile_path),
          "Lockfile must be unlinked upon SIGINT",
      )
    finally:
      if proc.stdout:
        proc.stdout.close()
      if proc.stderr:
        proc.stderr.close()
      if proc.poll() is None:
        proc.kill()
        proc.wait()


if __name__ == "__main__":
  unittest.main()
