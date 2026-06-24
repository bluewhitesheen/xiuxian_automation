from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable


@dataclass
class TimerResult:
	elapsed_seconds: float | None = None


@contextmanager
def timed_block(label: str, log: Callable[[str], None] = print):
	result = TimerResult()
	start = time.perf_counter()
	log(f"[timer] {label} started")
	try:
		yield result
	finally:
		result.elapsed_seconds = time.perf_counter() - start
		log(f"[timer] {label} finished in {result.elapsed_seconds:.3f}s")
