"""Minimal, safe wrapper for running the real ``nxpcrypto`` executable.

Design rules:
* commands are argument lists, never shell strings (no ``shell=True``);
* stdout, stderr, return code and duration are always captured;
* every call has a timeout;
* no secret material (key contents, passwords) is ever passed on the command line or logged.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TIMEOUT_S = 60.0
_MAX_DIAGNOSTIC_CHARS = 2000


class HarnessError(Exception):
    """The test harness could not run the tool under test (not a security verdict)."""


class ExecutableNotFoundError(HarnessError):
    """``nxpcrypto`` is not installed in the active environment."""


class CommandTimeoutError(HarnessError):
    """``nxpcrypto`` did not finish within the allowed time."""


@dataclass(frozen=True)
class CommandResult:
    """Immutable record of one CLI invocation."""

    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    duration_s: float

    @property
    def output(self) -> str:
        """stdout and stderr combined (SPSDK prints some messages to each)."""
        return f"{self.stdout}\n{self.stderr}"

    def describe(self) -> str:
        """Readable diagnostic block for assertion messages."""

        def clip(text: str) -> str:
            text = text.strip()
            if len(text) > _MAX_DIAGNOSTIC_CHARS:
                return text[:_MAX_DIAGNOSTIC_CHARS] + " ...[truncated]"
            return text or "<empty>"

        return (
            f"command   : {' '.join(self.command)}\n"
            f"returncode: {self.returncode}\n"
            f"duration  : {self.duration_s:.2f}s\n"
            f"stdout    : {clip(self.stdout)}\n"
            f"stderr    : {clip(self.stderr)}"
        )


def locate_nxpcrypto() -> Path:
    """Find ``nxpcrypto`` next to the running interpreter (venv first), then on PATH.

    Works with both Windows (``Scripts\\nxpcrypto.exe``) and POSIX (``bin/nxpcrypto``) layouts.
    """
    exe_name = "nxpcrypto.exe" if os.name == "nt" else "nxpcrypto"
    beside_interpreter = Path(sys.executable).parent / exe_name
    if beside_interpreter.is_file():
        return beside_interpreter
    found = shutil.which("nxpcrypto")
    if found:
        return Path(found)
    raise ExecutableNotFoundError(
        "nxpcrypto executable not found. Activate the virtual environment and run "
        "'python -m pip install -e .[dev]'."
    )


def run_nxpcrypto(
    args: Sequence[str | os.PathLike[str]],
    *,
    executable: Path | None = None,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    cwd: Path | None = None,
) -> CommandResult:
    """Run ``nxpcrypto <args>`` and return the captured result.

    A non-zero return code is *not* raised: deciding whether it is expected is the test's job.
    Only harness-level problems (missing executable, timeout) raise ``HarnessError``.
    """
    exe = executable or locate_nxpcrypto()
    command = (str(exe), *(os.fspath(a) for a in args))
    # Force UTF-8 output from the Python-based CLI so decoding is identical on Windows and Linux.
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
            cwd=cwd,
            env=env,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ExecutableNotFoundError(f"Could not execute {exe}: {exc}") from exc
    except OSError as exc:  # e.g. permission denied or not a valid executable
        raise HarnessError(f"Could not execute {exe}: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise CommandTimeoutError(f"Timed out after {timeout_s}s: {' '.join(command)}") from exc
    return CommandResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_s=time.perf_counter() - start,
    )
