"""Action helpers for BlueStacks automation."""
from __future__ import annotations

from io import BytesIO
import time
from typing import Final
from PIL import Image

from core.adb_utils import run_adb


APP_PACKAGE: Final[str] = "com.dustglobal.googleplay.xiuxian"


def tap_pixel(adb_serial: str, x: int, y: int) -> None:
	"""Tap absolute pixel coordinate on device."""
	run_adb(
		adb_serial,
		["shell", "input", "tap", str(x), str(y)],
	)


def read_pixel_rgb(adb_serial: str, x: int, y: int) -> tuple[int, int, int]:
	"""Capture device screenshot and return the RGB tuple at (x, y)."""
	screenshot = run_adb(
		adb_serial,
		["exec-out", "screencap", "-p"],
		capture_output=True,
	)

	raw = screenshot.stdout
	if not isinstance(raw, (bytes, bytearray)):
		raw = str(raw).encode()

	with Image.open(BytesIO(raw)) as image:
		image_rgb = image.convert("RGB")
		width, height = image_rgb.size
		if not (0 <= x < width and 0 <= y < height):
			raise ValueError(f"Pixel coordinate ({x}, {y}) out of bounds for screenshot {width}x{height}")
		return image_rgb.getpixel((x, y))


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
	tap_pixel(adb_serial, 270, 1120)
	time.sleep(15)
	tap_pixel(adb_serial, 270, 1035)
	time.sleep(1)

def click_travel(adb_serial: str) -> None:
	tap_pixel(adb_serial, 450, 1250)
	time.sleep(1)

def move_to_right_buttom(adb_serial: str) -> None:
	for _ in range(5):
		run_adb(
			adb_serial,
			["shell", "input", "swipe", "500", "500", "0", "0", "100"],
		)
	time.sleep(0.5)
