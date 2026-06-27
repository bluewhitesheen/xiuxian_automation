from __future__ import annotations

import argparse
from typing import Final

from capture_and_split import (
	DEFAULT_GRID_HEIGHT,
	DEFAULT_GRID_WIDTH,
	DEFAULT_GRID_X,
	DEFAULT_GRID_Y,
	ADB_SERIAL,
	ADB_TIMEOUT_SECONDS,
	capture_screenshot,
	crop_grid_region,
	run_adb,
)
from bluestacks_automation.grid_classifier import GRID_COLS, GRID_ROWS, analyze_screenshot_grid


DEFAULT_SERIAL: Final[str] = ADB_SERIAL
DEFAULT_TIMEOUT_SECONDS: Final[int] = ADB_TIMEOUT_SECONDS


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Capture adb screenshot and print 2D classified grid.")
	parser.add_argument("--serial", default=DEFAULT_SERIAL, help="ADB device serial (default: emulator-5554)")
	parser.add_argument("--grid-x", type=int, default=DEFAULT_GRID_X, help="Grid left pixel")
	parser.add_argument("--grid-y", type=int, default=DEFAULT_GRID_Y, help="Grid top pixel")
	parser.add_argument("--grid-width", type=int, default=DEFAULT_GRID_WIDTH, help="Grid pixel width")
	parser.add_argument("--grid-height", type=int, default=DEFAULT_GRID_HEIGHT, help="Grid pixel height")
	parser.add_argument("--rows", type=int, default=GRID_ROWS, help="Grid rows")
	parser.add_argument("--cols", type=int, default=GRID_COLS, help="Grid columns")
	return parser.parse_args()


def validate_adb(serial: str, timeout_seconds: int) -> None:
	run_adb(serial, ["get-state"], timeout_seconds=timeout_seconds, capture_output=True, text=True)


def capture_grid(serial: str, timeout_seconds: int, grid_x: int, grid_y: int, grid_width: int, grid_height: int, rows: int, cols: int) -> list[list[str]]:
	raw_image = capture_screenshot(serial, timeout_seconds)
	cropped = crop_grid_region(raw_image, grid_x, grid_y, grid_width, grid_height)
	return analyze_screenshot_grid(cropped, rows=rows, cols=cols)


def print_grid(grid: list[list[str]]) -> None:
	for row in grid:
		print(" ".join(row))


def main() -> None:
	args = parse_args()
	validate_adb(args.serial, DEFAULT_TIMEOUT_SECONDS)
	grid = capture_grid(
		args.serial,
		DEFAULT_TIMEOUT_SECONDS,
		args.grid_x,
		args.grid_y,
		args.grid_width,
		args.grid_height,
		args.rows,
		args.cols,
	)
	print_grid(grid)


if __name__ == "__main__":
	main()
