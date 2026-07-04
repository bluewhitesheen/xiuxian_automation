from __future__ import annotations

import datetime as _dt
from functools import partial
import configparser
import time
from pathlib import Path
import sys
from typing import Final

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from map_module._bootstrap import ensure_repo_root_on_path
from map_automation.executor import tap_pixel
from core.capture import capture_cropped_screenshot
from core.actions import click_travel, move_to_right_buttom, restart_game
from core.adb_utils import ADB_COMMAND_TIMEOUT_SECONDS, run_adb
from map_automation.iteration import is_verified_clear_grid, run_map_once, verify_current_grid
from core.logging_utils import tee_console_to_log


def _bootstrap() -> tuple[Path, Path]:
    workspace = Path(__file__).resolve().parent
    project_root = ensure_repo_root_on_path()
    return workspace, project_root


WORKSPACE_DIR, PROJECT_ROOT = _bootstrap()
CONFIG_PATH = PROJECT_ROOT / "bluestack.conf"
LOG_DIR = PROJECT_ROOT / "logs"
ADB_SERIAL: Final[str] = "emulator-5554"

# Crop the device screenshot down to the 2D grid region.
GRID_X = 60
GRID_Y = 320
GRID_WIDTH = 420
GRID_HEIGHT = 780


def validate_adb_connection() -> None:
	run_adb(ADB_SERIAL, ["devices"])
	device_state = run_adb(ADB_SERIAL, ["get-state"], capture_output=True, text=True).stdout.strip()
	if device_state != "device":
		raise RuntimeError(f"ADB device is not ready (state={device_state!r})")


def load_runtime_config(config_path: Path = CONFIG_PATH) -> tuple[int, int, int, int]:
	if not config_path.exists():
		raise RuntimeError(f"Config file not found: {config_path}")

	parser = configparser.ConfigParser()
	parser.read(config_path, encoding="utf-8")
	if not parser.has_option("automation", "iter_count"):
		raise RuntimeError(f"Missing 'iter_count' in section [automation] in {config_path}")
	if not parser.has_option("automation", "patch_count"):
		raise RuntimeError(f"Missing 'patch_count' in section [automation] in {config_path}")
	if not parser.has_option("automation", "stage"):
		raise RuntimeError(f"Missing 'stage' in section [automation] in {config_path}")
	if not parser.has_section("level_positions"):
		raise RuntimeError(f"Missing section [level_positions] in {config_path}")

	try:
		iter_count = parser.getint("automation", "iter_count")
		patch_count = parser.getint("automation", "patch_count")
		stage = parser.getint("automation", "stage")
	except ValueError as exc:
		raise RuntimeError(f"Invalid config value in {config_path}") from exc

	if not parser.has_option("level_positions", str(stage)):
		raise RuntimeError(f"Missing coordinate for stage '{stage}' in [level_positions] in {config_path}")

	raw_position = parser.get("level_positions", str(stage), fallback="").strip()
	parts = [p.strip() for p in raw_position.split(",", 1)]
	if len(parts) != 2:
		raise RuntimeError(
			f"Invalid coordinate format for stage '{stage}' in [level_positions], expected 'x,y' in {config_path}"
		)

	try:
		stage_x = int(parts[0])
		stage_y = int(parts[1])
	except ValueError as exc:
		raise RuntimeError(
			f"Invalid coordinate values for stage '{stage}' in [level_positions], expected integers in {config_path}"
		) from exc

	return patch_count, iter_count, stage_x, stage_y


def main() -> None:
	validate_adb_connection()
	patch_count, iter_count, stage_x, stage_y = load_runtime_config()

	current_time = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
	with tee_console_to_log(LOG_DIR, f"run_{current_time}.txt") as log_path:
		print(f"log file: {log_path}")
		print(f"run started: {current_time}")

		for patch in range(patch_count):
			print(f"patch {patch + 1}/{patch_count} started")
			for iteration in range(iter_count):
				print(f"iter {iteration + 1}/{iter_count} clear loop started")
				tap_pixel(ADB_SERIAL, stage_x, stage_y)
				time.sleep(0.15)
				tap_pixel(ADB_SERIAL, 280, 862)
				time.sleep(0.5)

				capture_screenshot = partial(
					capture_cropped_screenshot,
					ADB_SERIAL,
					GRID_X,
					GRID_Y,
					GRID_WIDTH,
					GRID_HEIGHT,
					timeout_seconds=ADB_COMMAND_TIMEOUT_SECONDS,
				)

				while True:
					_, _ = run_map_once(capture_screenshot, ADB_SERIAL)

					verify_grid = verify_current_grid(capture_screenshot)
					if is_verified_clear_grid(verify_grid):
						tap_pixel(ADB_SERIAL, 30, 30)
						time.sleep(0.25)
						tap_pixel(ADB_SERIAL, 350, 720)
						time.sleep(0.25)
						break

					_ = verify_grid

			restart_game(ADB_SERIAL)
			click_travel(ADB_SERIAL)
			move_to_right_buttom(ADB_SERIAL)



if __name__ == "__main__":
	main()
