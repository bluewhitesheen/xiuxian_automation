from __future__ import annotations

import datetime as _dt

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from map_module._bootstrap import ensure_repo_root_on_path
from map_automation.iteration import print_grid, run_map_once

ensure_repo_root_on_path()
from map_module.map_automation_main import ADB_SERIAL, GRID_X, GRID_Y, GRID_HEIGHT, GRID_WIDTH
from core.capture import capture_cropped_screenshot
from core.adb_utils import ADB_COMMAND_TIMEOUT_SECONDS


def main() -> None:
	capture_screenshot = lambda: capture_cropped_screenshot(
		ADB_SERIAL,
		GRID_X,
		GRID_Y,
		GRID_WIDTH,
		GRID_HEIGHT,
		timeout_seconds=ADB_COMMAND_TIMEOUT_SECONDS,
	)

	current_time = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
	print(f"run one iteration: {current_time}")
	grid, _ = run_map_once(capture_screenshot, ADB_SERIAL)
	print("Final grid:")
	print_grid(grid)


if __name__ == "__main__":
	main()
