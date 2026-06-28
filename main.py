from __future__ import annotations

import datetime as _dt
import io
import configparser
import time
from pathlib import Path
from typing import Final

from PIL import Image

from bluestacks_automation.executor import tap_pixel
from bluestacks_automation.actions import restart_game, click_travel, move_to_right_buttom
from bluestacks_automation.adb_utils import ADB_COMMAND_TIMEOUT_SECONDS, run_adb
from bluestacks_automation.iteration import is_verified_clear_grid, run_map_once, verify_current_grid
from bluestacks_automation.logging_utils import tee_console_to_log


WORKSPACE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = WORKSPACE_DIR / "bluestack.conf"
LOG_DIR = WORKSPACE_DIR / "logs"
ADB_SERIAL: Final[str] = "emulator-5554"

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


def capture_screenshot_via_exec_out() -> io.BytesIO:
	screenshot_start = time.perf_counter()
	result = run_adb(
		ADB_SERIAL,
		["exec-out", "screencap", "-p"],
		timeout_seconds=ADB_COMMAND_TIMEOUT_SECONDS,
		capture_output=True,
	)
	screenshot_end = time.perf_counter()
	# print(f"capture_device_screenshot: {screenshot_end - screenshot_start:.3f}s")
	return io.BytesIO(result.stdout)


def capture_device_screenshot() -> Image.Image:
	image_buffer = capture_screenshot_via_exec_out()
	with Image.open(image_buffer) as image:
		image = crop_grid_region(image)
		return image.copy()


def validate_adb_connection() -> None:
	run_adb(ADB_SERIAL, ["devices"])
	device_state = run_adb(ADB_SERIAL, ["get-state"], capture_output=True, text=True).stdout.strip()
	if device_state != "device":
		raise RuntimeError(f"ADB device is not ready (state={device_state!r})")


def load_runtime_config(config_path: Path = CONFIG_PATH) -> tuple[int, int]:
	if not config_path.exists():
		raise RuntimeError(f"Config file not found: {config_path}")

	parser = configparser.ConfigParser()
	parser.read(config_path, encoding="utf-8")
	if not parser.has_option("automation", "iter_count"):
		raise RuntimeError(f"Missing 'iter_count' in section [automation] in {config_path}")
	if not parser.has_option("automation", "patch_count"):
		raise RuntimeError(f"Missing 'patch_count' in section [automation] in {config_path}")

	try:
		iter_count = parser.getint("automation", "iter_count")
		patch_count = parser.getint("automation", "patch_count")
	except ValueError as exc:
		raise RuntimeError(f"Invalid config value in {config_path}") from exc

	return patch_count, iter_count


def main() -> None:
	validate_adb_connection()
	patch_count, iter_count = load_runtime_config()

	current_time = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
	with tee_console_to_log(LOG_DIR, f"run_{current_time}.txt") as log_path:
		print(f"log file: {log_path}")
		print(f"run started: {current_time}")

		for patch in range(patch_count):
			print(f"patch {patch + 1}/{patch_count} started")
			for iteration in range(iter_count):
				print(f"iter {iteration + 1}/{iter_count} clear loop started")
				tap_pixel(ADB_SERIAL, 360, 1600)
				time.sleep(0.3)
				tap_pixel(ADB_SERIAL, 1120, 3450)
				time.sleep(1)

				while True:
					_, _ = run_map_once(capture_device_screenshot, ADB_SERIAL)

					verify_grid = verify_current_grid(capture_device_screenshot)
					if is_verified_clear_grid(verify_grid):
						tap_pixel(ADB_SERIAL, 120, 120)
						time.sleep(0.5)
						tap_pixel(ADB_SERIAL, 1400, 2880)
						time.sleep(0.5)
						break

					_ = verify_grid

			restart_game(ADB_SERIAL)
			click_travel(ADB_SERIAL)
			move_to_right_buttom(ADB_SERIAL)



if __name__ == "__main__":
	main()
