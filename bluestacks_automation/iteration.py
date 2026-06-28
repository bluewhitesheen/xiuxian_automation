from __future__ import annotations

import time
from collections.abc import Callable

from PIL import Image

from .executor import execute_list, interact_with_monster, tap_pixel
from .grid_classifier import analyze_screenshot_grid
from .route_planner_old import get_next_route
from .grid_geometry import (
	GRID_CELL_CENTER_OFFSET_X,
	GRID_CELL_CENTER_OFFSET_Y,
	GRID_CELL_PX_X,
	GRID_CELL_PX_Y,
	GRID_LEFT_PX,
	GRID_TOP_PX,
)

Grid = list[list[str]]
GridPoint = tuple[int, int]
ScreenshotFunc = Callable[[], Image.Image]


def grid_point_to_pixel(row: int, col: int) -> tuple[int, int]:
	return (
		GRID_LEFT_PX + col * GRID_CELL_PX_X + GRID_CELL_CENTER_OFFSET_X,
		GRID_TOP_PX + row * GRID_CELL_PX_Y + GRID_CELL_CENTER_OFFSET_Y,
	)


def find_player(grid: Grid) -> GridPoint:
	for row_index, row in enumerate(grid):
		for col_index, cell in enumerate(row):
			if cell == "P":
				return row_index, col_index
	raise RuntimeError("P not found")


def is_verified_clear_grid(grid: Grid) -> bool:
	player_count = sum(1 for row in grid for cell in row if cell == "P")
	has_event = any(cell in ("M", "I") for row in grid for cell in row)
	return player_count == 1 and not has_event


def print_grid(grid: Grid) -> None:
	for row in grid:
		print("".join(row))


def capture_grid(capture_device_screenshot: ScreenshotFunc) -> Grid:
	image = capture_device_screenshot()
	return analyze_screenshot_grid(image)


def tap_initial_player_position(adb_serial: str | None = None) -> None:
	start_x, start_y = grid_point_to_pixel(12, 3)
	tap_pixel(adb_serial, start_x, start_y)
	time.sleep(0.7)


def run_map_once(
	capture_device_screenshot: ScreenshotFunc,
	adb_serial: str | None = None,
	grid: Grid | None = None,
	current_pos: GridPoint | None = None,
	tap_start: bool = True,
) -> tuple[Grid, GridPoint]:
	"""Run route planning until no next route is available for the current captured grid."""
	if tap_start:
		tap_initial_player_position(adb_serial)

	if grid is None:
		grid = capture_grid(capture_device_screenshot)

	if current_pos is None:
		try:
			current_pos = find_player(grid)
		except RuntimeError:
			print("player not found in classified grid:")
			raise

	while True:
		try:
			target, click_list = get_next_route(grid)
		except ValueError as exc:
			print(f"no next route: {exc}")
			break

		execute_list(click_list, current_pos, adb_serial)

		entry = click_list[-1] if click_list else current_pos
		row_index, col_index = target
		if 0 <= row_index < len(grid) and 0 <= col_index < len(grid[0]):
			cell_before = grid[row_index][col_index]
			if cell_before == "M":
				interact_with_monster((row_index, col_index), adb_serial)
				grid[row_index][col_index] = "."
			elif cell_before == "I":
				grid[row_index][col_index] = "."

		prev_row, prev_col = current_pos
		if 0 <= prev_row < len(grid) and 0 <= prev_col < len(grid[0]) and grid[prev_row][prev_col] == "P":
			grid[prev_row][prev_col] = "."

		entry_row, entry_col = entry
		grid[entry_row][entry_col] = "P"
		current_pos = entry

	return grid, current_pos


def verify_current_grid(capture_device_screenshot: ScreenshotFunc) -> Grid:
	time.sleep(0.7)
	verify_grid = capture_grid(capture_device_screenshot)
	return verify_grid
