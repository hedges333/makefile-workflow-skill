#!/usr/bin/env python3
"""POSIX Signal Trapping for Long-Running Workers (SCAR-SYS-07).

Provides SignalTrap context manager and cleanup registry to intercept SIGTERM
and SIGINT, execute cleanup callbacks in LIFO order, safely unlink registered
lockfiles, and exit cleanly.
"""

import argparse
import logging
import os
import signal
import sys
import time
from types import FrameType
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union

logger = logging.getLogger(__name__)

DEFAULT_SIGNALS: Tuple[int, ...] = (signal.SIGTERM, signal.SIGINT)


class SignalTrap:
  """POSIX signal handler and cleanup manager for long-running workers."""

  def __init__(
      self,
      signals: Sequence[int] = DEFAULT_SIGNALS,
      exit_on_signal: bool = True,
      cleanup_on_exit: bool = True,
  ) -> None:
    """Initialize SignalTrap.

    Args:
        signals: Sequence of POSIX signal integers to trap (default SIGTERM, SIGINT).
        exit_on_signal: If True, invoke sys.exit(128 + sig) after handling signal.
        cleanup_on_exit: If True, execute cleanups upon normal context exit.
    """
    self.signals: Tuple[int, ...] = tuple(signals)
    self.exit_on_signal: bool = exit_on_signal
    self.cleanup_on_exit: bool = cleanup_on_exit

    self._original_handlers: Dict[int, Any] = {}
    self._cleanups: List[Tuple[Callable[..., Any], Tuple[Any, ...], Dict[str, Any]]] = []
    self._lockfiles: Set[str] = set()

    self._installed: bool = False
    self._handling_signal: bool = False
    self._cleanups_executed: bool = False
    self.signal_count: int = 0
    self.last_signal: Optional[int] = None
    self.caught_exceptions: List[Tuple[Callable[..., Any], Exception]] = []

  @property
  def is_installed(self) -> bool:
    """Return whether signal handlers are actively installed."""
    return self._installed

  def install(self) -> "SignalTrap":
    """Install signal handlers for configured signals.

    Returns:
        self for chaining.
    """
    if self._installed:
      return self

    self._original_handlers.clear()
    for sig in self.signals:
      try:
        prev = signal.signal(sig, self.handle_signal)
        self._original_handlers[sig] = prev
      except (ValueError, OSError) as exc:
        logger.warning("Could not register signal %s: %s", sig, exc)

    self._installed = True
    return self

  def restore(self) -> None:
    """Restore original signal handlers (idempotent)."""
    if not self._installed and not self._original_handlers:
      return

    for sig, handler in list(self._original_handlers.items()):
      try:
        signal.signal(sig, handler)
      except (ValueError, OSError) as exc:
        logger.warning("Could not restore signal %s: %s", sig, exc)

    self._original_handlers.clear()
    self._installed = False

  def register_cleanup(
      self, callback: Callable[..., Any], *args: Any, **kwargs: Any
  ) -> Callable[..., Any]:
    """Register a cleanup callback to be executed in reverse order (LIFO).

    Args:
        callback: Callable to execute.
        *args: Positional arguments for callback.
        **kwargs: Keyword arguments for callback.

    Returns:
        The registered callback.
    """
    self._cleanups.append((callback, args, kwargs))
    return callback

  def register_lockfile(self, path: Union[str, os.PathLike]) -> str:
    """Register a lockfile path to be removed upon signal or exit.

    Args:
        path: Filesystem path to lockfile.

    Returns:
        Normalized absolute path string.
    """
    norm_path = os.path.abspath(os.fspath(path))
    self._lockfiles.add(norm_path)
    return norm_path

  def remove_lockfiles(self) -> List[Tuple[str, Exception]]:
    """Remove all registered lockfiles if they exist.

    Returns:
        List of (path, exception) tuples for any removal errors.
    """
    errors: List[Tuple[str, Exception]] = []
    lockfiles_to_remove = list(self._lockfiles)
    self._lockfiles.clear()

    for path in lockfiles_to_remove:
      try:
        if os.path.exists(path):
          os.unlink(path)
      except OSError as exc:
        errors.append((path, exc))
        logger.warning("Failed to remove lockfile %s: %s", path, exc)

    return errors

  def execute_cleanups(self) -> List[Tuple[Callable[..., Any], Exception]]:
    """Execute all registered cleanup callbacks in reverse order (LIFO).

    Isolates exceptions so that a failure in one callback does not abort
    subsequent cleanup execution.

    Returns:
        List of (callback, exception) tuples for any caught errors.
    """
    errors: List[Tuple[Callable[..., Any], Exception]] = []

    while self._cleanups:
      callback, args, kwargs = self._cleanups.pop()
      try:
        callback(*args, **kwargs)
      except Exception as exc:  # pylint: disable=broad-except
        errors.append((callback, exc))
        self.caught_exceptions.append((callback, exc))
        logger.warning("Error in cleanup callback %s: %s", callback, exc)

    self.remove_lockfiles()
    self._cleanups_executed = True
    return errors

  def handle_signal(self, sig: int, frame: Optional[FrameType]) -> None:
    """Handle caught POSIX signal, execute cleanups, and exit.

    Args:
        sig: Signal number received.
        frame: Current stack frame.
    """
    self.signal_count += 1
    self.last_signal = sig

    if self._handling_signal:
      # Idempotency guard against repeated re-entrant signals
      return

    self._handling_signal = True
    try:
      self.execute_cleanups()
    finally:
      self.restore()
      if self.exit_on_signal:
        sys.exit(128 + sig)

  def __enter__(self) -> "SignalTrap":
    """Enter context manager, installing signal trap."""
    return self.install()

  def __exit__(
      self,
      exc_type: Optional[type],
      exc_val: Optional[BaseException],
      exc_tb: Optional[Any],
  ) -> None:
    """Exit context manager, running cleanups if configured and restoring handlers."""
    if self.cleanup_on_exit and not self._cleanups_executed:
      self.execute_cleanups()
    self.restore()


def main(argv: Optional[Sequence[str]] = None) -> int:
  """Run signal_trap demo worker CLI for testing and process management."""
  parser = argparse.ArgumentParser(
      description="POSIX Signal Trap Worker (SCAR-SYS-07)"
  )
  parser.add_argument(
      "--lockfile",
      help="Path to lockfile to create and protect with SignalTrap",
  )
  parser.add_argument(
      "--ready-file",
      help="Path to sentinel file to create when signal trap is active",
  )
  args = parser.parse_args(argv)

  with SignalTrap() as trap:
    if args.lockfile:
      lock_path = os.path.abspath(args.lockfile)
      lock_dir = os.path.dirname(lock_path)
      if lock_dir:
        os.makedirs(lock_dir, exist_ok=True)
      with open(lock_path, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))
      trap.register_lockfile(lock_path)

    if args.ready_file:
      ready_path = os.path.abspath(args.ready_file)
      ready_dir = os.path.dirname(ready_path)
      if ready_dir:
        os.makedirs(ready_dir, exist_ok=True)
      with open(ready_path, "w", encoding="utf-8") as f:
        f.write("READY")

    # Keep worker alive until signal arrives
    while True:
      time.sleep(0.1)

  return 0


if __name__ == "__main__":
  sys.exit(main())
