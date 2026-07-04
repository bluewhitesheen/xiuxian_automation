from __future__ import annotations

import io
import time

from PIL import Image

from .adb_utils import ADB_COMMAND_TIMEOUT_SECONDS, run_adb


def capture_screenshot_via_exec_out(
	adb_serial: str,
	*, timeout_seconds: int = ADB_COMMAND_TIMEOUT_SECONDS,
) -> io.BytesIO:
	result = run_adb(
		adb_serial,
		["exec-out", "screencap", "-p"],
		timeout_seconds=timeout_seconds,
		capture_output=True,
	)
	return io.BytesIO(result.stdout)


def crop_grid_region(
	image: Image.Image,
	grid_x: int,
	grid_y: int,
	grid_width: int,
	grid_height: int,
) -> Image.Image:
	if grid_width <= 0 or grid_height <= 0:
		return image

	left = max(0, grid_x)
	top = max(0, grid_y)
	right = min(image.width, left + grid_width)
	bottom = min(image.height, top + grid_height)

	if left >= right or top >= bottom:
		raise RuntimeError("GRID_X / GRID_Y / GRID_WIDTH / GRID_HEIGHT is invalid")

	return image.crop((left, top, right, bottom))


def capture_cropped_screenshot(
	adb_serial: str,
	grid_x: int,
	grid_y: int,
	grid_width: int,
	grid_height: int,
	*, timeout_seconds: int = ADB_COMMAND_TIMEOUT_SECONDS,
) -> Image.Image:
	screenshot_start = time.perf_counter()
	image_buffer = capture_screenshot_via_exec_out(adb_serial, timeout_seconds=timeout_seconds)
	screenshot_end = time.perf_counter()
	# print(f"capture_cropped_screenshot: {screenshot_end - screenshot_start:.3f}s")
	with Image.open(image_buffer) as image:
		image = crop_grid_region(image, grid_x, grid_y, grid_width, grid_height)
		return image.copy()
