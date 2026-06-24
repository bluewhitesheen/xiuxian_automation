from __future__ import annotations

import datetime as _dt
import io
import shutil
import subprocess
import time
from pathlib import Path
from typing import Final

from PIL import Image

from bluestacks_automation.executor import tap_pixel
from bluestacks_automation.iteration import is_verified_clear_grid, run_map_once, verify_current_grid
from bluestacks_automation.logging_utils import tee_console_to_log


WORKSPACE_DIR = Path(__file__).resolve().parent
LOG_DIR = WORKSPACE_DIR / "logs"
ADB_SERIAL: Final[str] = "emulator-5554"
ADB_TIMEOUT_SECONDS: Final[int] = 20
iter_count = 19

# Crop the device screenshot down to the 2D grid region.
GRID_X = 240
GRID_Y = 1280
GRID_WIDTH = 1680
GRID_HEIGHT = 3120


def crop_grid_region(image: Image.Image) -> Image.Image:
	if GRID_WIDTH <= 0 or GRID_HEIGHT <= 0:
		return image

	left = max(0, GRID_X)
	top = max(0, GRID_Y)
	right = min(image.width, left + GRID_WIDTH)
	bottom = min(image.height, top + GRID_HEIGHT)

	if left >= right or top >= bottom:
		raise RuntimeError("GRID_X / GRID_Y / GRID_WIDTH / GRID_HEIGHT is invalid")

	return image.crop((left, top, right, bottom))


def run_adb(args: list[str]) -> subprocess.CompletedProcess[str]:
	adb_path = shutil.which("adb")
	if adb_path is None:
		raise RuntimeError("adb not found. Please install platform-tools and add adb to PATH")

	try:
		return subprocess.run(
			[adb_path, "-s", ADB_SERIAL, *args],
			check=True,
			capture_output=True,
			text=True,
			timeout=ADB_TIMEOUT_SECONDS,
		)
	except subprocess.TimeoutExpired as exc:
		raise RuntimeError(
			f"adb command timed out after {ADB_TIMEOUT_SECONDS}s: {' '.join(args)}"
		) from exc


def capture_screenshot_via_exec_out() -> io.BytesIO:
	adb_path = shutil.which("adb")
	if adb_path is None:
		raise RuntimeError("adb not found. Please install platform-tools and add adb to PATH")

	screenshot_start = time.perf_counter()
	try:
		result = subprocess.run(
			[adb_path, "-s", ADB_SERIAL, "exec-out", "screencap", "-p"],
			check=True,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			timeout=ADB_TIMEOUT_SECONDS,
		)
	except subprocess.TimeoutExpired as exc:
		raise RuntimeError(
			f"adb exec-out screencap timed out after {ADB_TIMEOUT_SECONDS}s"
		) from exc
	screenshot_end = time.perf_counter()
	print(f"capture_device_screenshot: {screenshot_end - screenshot_start:.3f}s")
	return io.BytesIO(result.stdout)


def capture_device_screenshot() -> Image.Image:
	image_buffer = capture_screenshot_via_exec_out()
	with Image.open(image_buffer) as image:
		image = crop_grid_region(image)
		return image.copy()


def validate_adb_connection() -> None:
	run_adb(["devices"])
	device_state = run_adb(["get-state"]).stdout.strip()
	if device_state != "device":
		raise RuntimeError(f"ADB device is not ready (state={device_state!r})")


def main() -> None:
	validate_adb_connection()

	current_time = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
	with tee_console_to_log(LOG_DIR, f"run_{current_time}.txt") as log_path:
		print(f"log file: {log_path}")
		print(f"run started: {current_time}")

		for iteration in range(iter_count):
			print(f"iter {iteration + 1}/{iter_count} clear loop started")
			tap_pixel(1450, 2365, ADB_SERIAL)
			time.sleep(0.3)
			tap_pixel(1120, 3450, ADB_SERIAL)
			time.sleep(1)

			while True:
				_, _ = run_map_once(capture_device_screenshot, ADB_SERIAL)

				verify_grid = verify_current_grid(capture_device_screenshot)
				if is_verified_clear_grid(verify_grid):
					tap_pixel(120, 120, ADB_SERIAL)
					time.sleep(0.5)
					tap_pixel(1400, 2880, ADB_SERIAL)
					time.sleep(0.5)
					break

				_ = verify_grid


if __name__ == "__main__":
	main()
