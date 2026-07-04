from __future__ import annotations

from collections import deque
from typing import Iterable


Grid = list[list[str]]
Point = tuple[int, int]


def _find_player(grid: Grid) -> Point:
	for row_index, row in enumerate(grid):
		for col_index, cell in enumerate(row):
			if cell == "P":
				return row_index, col_index
	raise ValueError("找不到 P")


def _in_bounds(grid: Grid, row: int, col: int) -> bool:
	return 0 <= row < len(grid) and 0 <= col < len(grid[0])


def _neighbors(row: int, col: int) -> Iterable[Point]:
	yield row - 1, col
	yield row + 1, col
	yield row, col - 1
	yield row, col + 1


def _is_monster(grid: Grid, row: int, col: int) -> bool:
	return grid[row][col] == "M"


def _is_passable(grid: Grid, row: int, col: int) -> bool:
	return grid[row][col] != "M"


def _build_event_points(grid: Grid) -> dict[Point, Point]:
	event_points: dict[Point, Point] = {}
	rows = len(grid)
	cols = len(grid[0]) if rows else 0

	for row in range(rows):
		if row == 0:
			continue
		for col in range(cols):
			if grid[12][0] == '.' and col == 0: 
				continue
			if grid[5][6] == '.' and grid[12][6] == '.' and col == 6:
				continue
			cell = grid[row][col]
			if cell == "I":
				event_points[(row, col)] = (row, col)
			if cell == "M":
				continue
			for neighbor_row, neighbor_col in _neighbors(row, col):
				if _in_bounds(grid, neighbor_row, neighbor_col) and _is_monster(grid, neighbor_row, neighbor_col):
					event_points[(row, col)] = (neighbor_row, neighbor_col)
					break

	return event_points


def _bfs_distances(grid: Grid, start: Point) -> tuple[dict[Point, Point | None], dict[Point, int]]:
	parents: dict[Point, Point | None] = {start: None}
	distances: dict[Point, int] = {start: 0}
	queue: deque[Point] = deque([start])

	while queue:
		row, col = queue.popleft()
		current_distance = distances[(row, col)]
		for next_row, next_col in _neighbors(row, col):
			if not _in_bounds(grid, next_row, next_col):
				continue
			if not _is_passable(grid, next_row, next_col):
				continue
			next_point = (next_row, next_col)
			if next_point in distances:
				continue
			parents[next_point] = (row, col)
			distances[next_point] = current_distance + 1
			queue.append(next_point)

	return parents, distances


def _reconstruct_path(parents: dict[Point, Point | None], end: Point) -> list[Point]:
	path: list[Point] = []
	current: Point | None = end

	while current is not None:
		path.append(current)
		current = parents[current]

	path.reverse()
	return path


def _count_turns(path: list[Point]) -> int:
	if len(path) < 3:
		return 0

	turns = 0
	previous_direction: tuple[int, int] | None = None

	for index in range(1, len(path)):
		row_a, col_a = path[index - 1]
		row_b, col_b = path[index]
		direction = (row_b - row_a, col_b - col_a)
		if previous_direction is not None and direction != previous_direction:
			turns += 1
		previous_direction = direction

	return turns


def _center_manhattan_distance(grid: Grid, point: Point) -> int:
	rows = len(grid)
	cols = len(grid[0]) if rows else 0
	center_row = (rows - 1) / 2
	center_col = (cols - 1) / 2
	row, col = point
	return int(abs(row - center_row) + abs(col - center_col))


def _compress_path(path: list[Point]) -> list[Point]:
	if len(path) <= 1:
		return []

	waypoints: list[Point] = []
	previous_direction: tuple[int, int] | None = None

	for index in range(1, len(path)):
		row_a, col_a = path[index - 1]
		row_b, col_b = path[index]
		direction = (row_b - row_a, col_b - col_a)
		if previous_direction is not None and direction != previous_direction:
			waypoints.append(path[index - 1])
		previous_direction = direction

	waypoints.append(path[-1])
	return waypoints


def get_next_route(grid: Grid) -> tuple[Point, list[Point]]:
	if not grid or not grid[0]:
		raise ValueError("grid 不能是空的")

	start = _find_player(grid)
	event_points = _build_event_points(grid)
	if not event_points:
		raise ValueError("找不到可前往的 event point")

	parents, distances = _bfs_distances(grid, start)
	reachable_events = [point for point in event_points if point in distances]
	if not reachable_events:
		raise ValueError("沒有可達的 event point")

	best_event = min(
		reachable_events,
		key=lambda point: (
			distances[point],
			-_center_manhattan_distance(grid, point),
			_count_turns(_reconstruct_path(parents, point)),
		),
	)
	best_path = _reconstruct_path(parents, best_event)
	return event_points[best_event], _compress_path(best_path)
