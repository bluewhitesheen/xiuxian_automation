"""Action helpers for BlueStacks automation."""
from __future__ import annotations

import time
from typing import Final

from bluestacks_automation.adb_utils import run_adb


APP_PACKAGE: Final[str] = "com.dustglobal.googleplay.xiuxian"
ADB_TIMEOUT_SECONDS: Final[int] = 10


def restart_game(adb_serial: str, timeout_seconds: int = ADB_TIMEOUT_SECONDS) -> None:
	"""Restart the target app by force-stopping it and relaunching from launcher."""
	run_adb(
		adb_serial,
		["shell", "am", "force-stop", APP_PACKAGE],
		timeout_seconds=timeout_seconds,
		capture_output=True,
		text=True,
	)
	time.sleep(1)
	run_adb(
		adb_serial,
		["shell", "monkey", "-p", APP_PACKAGE, "-c", "android.intent.category.LAUNCHER", "1"],
		timeout_seconds=timeout_seconds,
		capture_output=True,
		text=True,
	)
	time.sleep(7)
	run_adb(
		adb_serial,
		["shell", "input", "tap", "1080", "4480"],
		timeout_seconds=timeout_seconds,
	)
	time.sleep(15)
	run_adb(
		adb_serial,
		["shell", "input", "tap", "1080", "4140"],
		timeout_seconds=timeout_seconds,
	)
