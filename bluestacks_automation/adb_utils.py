"""Shared adb helpers for this repo."""
from __future__ import annotations

import subprocess
import shutil
from typing import Final, Sequence


ADB_COMMAND_TIMEOUT_SECONDS: Final[int] = 10


def _adb_path() -> str:
	adb_path = shutil.which("adb")
	if adb_path is None:
		raise RuntimeError("adb not found. Please install platform-tools and add adb to PATH")
	return adb_path


def run_adb(
	adb_serial: str,
	args: Sequence[str],
	*,
	timeout_seconds: int = ADB_COMMAND_TIMEOUT_SECONDS,
	check: bool = True,
	capture_output: bool = False,
	text: bool = False,
	stdout: object = None,
	stderr: object = None,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
	"""Run an adb command for the selected serial and args."""
	if capture_output and (stdout is not None or stderr is not None):
		raise ValueError("capture_output=True cannot be used with explicit stdout/stderr")

	command = [_adb_path(), "-s", adb_serial, *args]

	run_kwargs: dict[str, object] = {
		"check": check,
		"timeout": timeout_seconds,
		"text": text,
	}
	if capture_output:
		run_kwargs["capture_output"] = True
	else:
		run_kwargs["stdout"] = stdout
		run_kwargs["stderr"] = stderr

	try:
		return subprocess.run(command, **run_kwargs)  # type: ignore[arg-type]
	except subprocess.TimeoutExpired as exc:
		raise RuntimeError(f"adb command timed out after {timeout_seconds}s: {' '.join(args)}") from exc
	except subprocess.CalledProcessError as exc:
		stdout_text = (exc.stdout or "").strip() if exc.stdout is not None else ""
		stderr_text = (exc.stderr or "").strip() if exc.stderr is not None else ""
		raise RuntimeError(
			f"adb command failed: {' '.join(args)} (return code={exc.returncode}, stdout={stdout_text!r}, stderr={stderr_text!r})"
		) from exc


def run_adb_with_output(
	adb_serial: str,
	args: Sequence[str],
	*,
	timeout_seconds: int = ADB_COMMAND_TIMEOUT_SECONDS,
	text: bool = False,
) -> bytes | str:
	"""Run adb and always capture stdout."""
	result = run_adb(adb_serial, args, timeout_seconds=timeout_seconds, capture_output=True, text=text)
	return result.stdout
