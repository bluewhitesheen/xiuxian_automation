"""Action helpers for BlueStacks automation."""
from __future__ import annotations

import time
from typing import Final

from bluestacks_automation.adb_utils import run_adb
from bluestacks_automation.executor import tap_pixel


APP_PACKAGE: Final[str] = "com.dustglobal.googleplay.xiuxian"


def restart_game(adb_serial: str) -> None:
	"""Restart the target app by force-stopping it and relaunching from launcher."""
	run_adb(
		adb_serial,
		["shell", "am", "force-stop", APP_PACKAGE],
		capture_output=True,
		text=True,
	)
	time.sleep(5)
	run_adb(
		adb_serial,
		["shell", "monkey", "-p", APP_PACKAGE, "-c", "android.intent.category.LAUNCHER", "1"],
		capture_output=True,
		text=True,
	)
	time.sleep(7)
	tap_pixel(adb_serial, 1080, 4480)
	time.sleep(15)
	tap_pixel(adb_serial, 1080, 4140)
	time.sleep(1)

def click_travel(adb_serial: str) -> None:
	tap_pixel(adb_serial, 1800, 5000)
	time.sleep(1)

def move_to_right_buttom(adb_serial: str) -> None:
	for _ in range(5):
		run_adb(
			adb_serial,
			["shell", "input", "swipe", "1500", "1500", "0", "0", "100"],
		)
	time.sleep(0.5)
