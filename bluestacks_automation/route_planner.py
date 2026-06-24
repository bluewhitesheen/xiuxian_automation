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


# -----------------------------
# event points
# -----------------------------

def _build_event_points(grid: Grid) -> dict[Point, Point]:
	event_points: dict[Point, Point] = {}
	rows = len(grid)
	cols = len(grid[0]) if rows else 0

	for row in range(rows):
		if row == 0:
			continue
		for col in range(cols):
			cell = grid[row][col]

			if cell == "I":
				event_points[(row, col)] = (row, col)

			if cell == "M":
				continue

			for nr, nc in _neighbors(row, col):
				if _in_bounds(grid, nr, nc) and _is_monster(grid, nr, nc):
					event_points[(row, col)] = (nr, nc)
					break

	return event_points


# -----------------------------
# BFS
# -----------------------------

def _bfs_distances(grid: Grid, start: Point):
	parents: dict[Point, Point | None] = {start: None}
	distances: dict[Point, int] = {start: 0}
	queue = deque([start])

	while queue:
		r, c = queue.popleft()
		for nr, nc in _neighbors(r, c):
			if not _in_bounds(grid, nr, nc):
				continue
			if not _is_passable(grid, nr, nc):
				continue
			if (nr, nc) in distances:
				continue

			distances[(nr, nc)] = distances[(r, c)] + 1
			parents[(nr, nc)] = (r, c)
			queue.append((nr, nc))

	return parents, distances


def _reconstruct_path(parents, end):
	path = []
	cur = end
	while cur is not None:
		path.append(cur)
		cur = parents[cur]
	return path[::-1]


def _count_turns(path: list[Point]) -> int:
	if len(path) < 3:
		return 0

	turns = 0
	prev = None

	for i in range(1, len(path)):
		a = path[i - 1]
		b = path[i]
		d = (b[0] - a[0], b[1] - a[1])

		if prev is not None and d != prev:
			turns += 1

		prev = d

	return turns


def _center_manhattan_distance(grid: Grid, point: Point) -> int:
	rows = len(grid)
	cols = len(grid[0]) if rows else 0
	cr = (rows - 1) / 2
	cc = (cols - 1) / 2
	r, c = point
	return int(abs(r - cr) + abs(c - cc))


# -----------------------------
# ⭐ NEW: event density
# -----------------------------

def _event_density(grid: Grid, point: Point) -> int:
	"""
	count nearby event-like tiles (M or I)
	radius = 2
	"""
	r0, c0 = point
	cnt = 0

	for dr in range(-2, 3):
		for dc in range(-2, 3):
			r, c = r0 + dr, c0 + dc
			if _in_bounds(grid, r, c):
				if grid[r][c] in ("M", "I"):
					cnt += 1

	return cnt


def _compress_path(path: list[Point]) -> list[Point]:
	if len(path) <= 1:
		return []

	waypoints = []
	prev_dir = None

	for i in range(1, len(path)):
		a = path[i - 1]
		b = path[i]
		d = (b[0] - a[0], b[1] - a[1])

		if prev_dir is not None and d != prev_dir:
			waypoints.append(path[i - 1])

		prev_dir = d

	waypoints.append(path[-1])
	return waypoints


# -----------------------------
# main
# -----------------------------

def get_next_route(grid: Grid) -> tuple[Point, list[Point]]:
	if not grid or not grid[0]:
		raise ValueError("grid 不能是空的")

	start = _find_player(grid)
	event_points = _build_event_points(grid)

	if not event_points:
		raise ValueError("找不到可前往的 event point")

	parents, distances = _bfs_distances(grid, start)

	reachable_events = [p for p in event_points if p in distances]
	if not reachable_events:
		raise ValueError("沒有可達的 event point")

	best_event = min(
		reachable_events,
		key=lambda p: (
			distances[p],

			# ⭐ NEW: event density priority
			-_event_density(grid, p),

			# keep your original heuristics
			-_center_manhattan_distance(grid, p),
			_count_turns(_reconstruct_path(parents, p)),
		),
	)

	best_path = _reconstruct_path(parents, best_event)
	return event_points[best_event], _compress_path(best_path)