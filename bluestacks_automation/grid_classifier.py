from __future__ import annotations

import cv2
import numpy as np
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from pprint import pformat

from PIL import Image

from bluestacks_automation.grid_geometry import GRID_ROWS, GRID_COLS


WORKSPACE_DIR = Path(__file__).resolve().parent.parent
RES_DIR = WORKSPACE_DIR / "res"
REFERENCE_CROP_SIZE = 176
SIMILARITY_THRESHOLD = 0.8


@dataclass(frozen=True)
class ReferenceCategory:
	name: str
	marker: str
	target_size: tuple[int, int]
	tiles: tuple[np.ndarray, ...]


def build_edges(length: int, parts: int) -> list[int]:
	if parts <= 0:
		raise ValueError("parts must be positive")

	return [round(length * index / parts) for index in range(parts + 1)]


def split_image(image: Image.Image, rows: int, cols: int) -> list[list[Image.Image]]:
	x_edges = build_edges(image.width, cols)
	y_edges = build_edges(image.height, rows)
	tiles: list[list[Image.Image]] = []

	for row in range(rows):
		row_tiles: list[Image.Image] = []
		top = y_edges[row]
		bottom = y_edges[row + 1]
		for col in range(cols):
			left = x_edges[col]
			right = x_edges[col + 1]
			row_tiles.append(image.crop((left, top, right, bottom)))
		tiles.append(row_tiles)

	return tiles


def _center_crop_gray(image: Image.Image, crop_size: int = REFERENCE_CROP_SIZE) -> np.ndarray:
	crop_width = min(crop_size, image.width)
	crop_height = min(crop_size, image.height)
	left = max(0, (image.width - crop_width) // 2)
	top = max(0, (image.height - crop_height) // 2)
	cropped = image.crop((left, top, left + crop_width, top + crop_height)).convert("RGB")
	array = np.array(cropped)
	return cv2.cvtColor(array, cv2.COLOR_RGB2GRAY)


def _resize_to_target(tile: np.ndarray, target_size: tuple[int, int]) -> np.ndarray:
	target_width, target_height = target_size
	if tile.shape[:2] == (target_height, target_width):
		return tile
	return cv2.resize(tile, target_size, interpolation=cv2.INTER_AREA)


def _normalize_tile_sizes(tiles: list[np.ndarray]) -> tuple[np.ndarray, ...]:
	min_height = min(tile.shape[0] for tile in tiles)
	min_width = min(tile.shape[1] for tile in tiles)
	target_size = (min_width, min_height)
	return tuple(_resize_to_target(tile, target_size) for tile in tiles)


def _load_category(category_name: str, marker: str) -> ReferenceCategory:
	category_dir = RES_DIR / category_name
	if not category_dir.exists():
		raise FileNotFoundError(f"Reference directory not found: {category_dir}")

	paths = sorted(path for path in category_dir.glob("*.png") if path.is_file())
	if not paths:
		raise RuntimeError(f"No reference images found in: {category_dir}")

	tiles: list[np.ndarray] = []
	for path in paths:
		with Image.open(path) as image:
			tiles.append(_center_crop_gray(image))

	normalized_tiles = _normalize_tile_sizes(tiles)
	target_height, target_width = normalized_tiles[0].shape[:2]
	return ReferenceCategory(
		name=category_name,
		marker=marker,
		target_size=(target_width, target_height),
		tiles=normalized_tiles,
	)


@lru_cache(maxsize=1)
def load_reference_categories() -> tuple[ReferenceCategory, ...]:
	return (
		_load_category("monster", "M"),
		_load_category("item", "I"),
		_load_category("people", "P"),
	)


def _classify_tile(tile: Image.Image, categories: tuple[ReferenceCategory, ...]) -> str:
	tile_gray = _center_crop_gray(tile)
	best_marker = "."
	best_similarity = 0.0

	for category in categories:
		for reference_tile in category.tiles:
			resized_tile = _resize_to_target(tile_gray, category.target_size)
			similarity = float(cv2.matchTemplate(resized_tile, reference_tile, cv2.TM_CCOEFF_NORMED)[0, 0])
			if similarity > best_similarity:
				best_similarity = similarity
				best_marker = category.marker

	if best_similarity <= SIMILARITY_THRESHOLD:
		return "."

	return best_marker


def analyze_screenshot_grid(image: Image.Image, rows: int = GRID_ROWS, cols: int = GRID_COLS) -> list[list[str]]:
	categories = load_reference_categories()
	grid: list[list[str]] = []

	for row_tiles in split_image(image, rows, cols):
		grid.append([_classify_tile(tile, categories) for tile in row_tiles])

	return grid


def format_grid(grid: list[list[str]]) -> str:
	return pformat(grid, width=120)

