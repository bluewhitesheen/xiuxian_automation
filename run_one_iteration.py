from __future__ import annotations

import datetime as _dt

from bluestacks_automation.iteration import print_grid, run_map_once
from main import ADB_SERIAL, capture_device_screenshot


def main() -> None:
	current_time = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
	print(f"run one iteration: {current_time}")
	grid, _ = run_map_once(capture_device_screenshot, ADB_SERIAL)
	print("Final grid:")
	print_grid(grid)


if __name__ == "__main__":
	main()
