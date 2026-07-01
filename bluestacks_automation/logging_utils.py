from __future__ import annotations

import sys
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path
from typing import TextIO


class TeeStream:
	def __init__(self, *streams: TextIO) -> None:
		self._streams = streams

	@property
	def encoding(self) -> str | None:
		return self._streams[0].encoding if self._streams else None

	def write(self, text: str) -> int:
		for stream in self._streams:
			stream.write(text)
		return len(text)

	def flush(self) -> None:
		for stream in self._streams:
			stream.flush()

	def isatty(self) -> bool:
		return any(stream.isatty() for stream in self._streams)


@contextmanager
def tee_console_to_log(log_dir: Path, log_name: str):
	log_dir.mkdir(parents=True, exist_ok=True)
	log_path = log_dir / log_name

	with log_path.open("w", encoding="utf-8", buffering=1) as log_file:
		stdout_tee = TeeStream(sys.stdout, log_file)
		stderr_tee = TeeStream(sys.stderr, log_file)
		with redirect_stdout(stdout_tee), redirect_stderr(stderr_tee):
			yield log_path
