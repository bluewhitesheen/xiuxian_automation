from __future__ import annotations

import argparse
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from PIL import Image

from bluestacks_automation.grid_geometry import (
	GRID_COLS,
	GRID_HEIGHT_PX,
	GRID_LEFT_PX,
	GRID_ROWS,
	GRID_TOP_PX,
	GRID_WIDTH_PX,
)

WORKSPACE_DIR = Path(__file__).resolve().parent
RES_DIR = WORKSPACE_DIR / "res"
ADB_SERIAL = "emulator-5554"
ADB_TIMEOUT_SECONDS = 20

# Default crop matches the 13x7 grid used by the current classifier.
DEFAULT_GRID_X = GRID_LEFT_PX
DEFAULT_GRID_Y = GRID_TOP_PX
DEFAULT_GRID_WIDTH = GRID_WIDTH_PX
DEFAULT_GRID_HEIGHT = GRID_HEIGHT_PX
DEFAULT_ROWS = GRID_ROWS
DEFAULT_COLS = GRID_COLS


def run_adb(args: list[str], serial: str, timeout_seconds: int) -> subprocess.CompletedProcess[str]:
	adb_path = shutil.which("adb")
	if adb_path is None:
		raise RuntimeError("找不到 adb 指令，請先安裝 platform-tools 並加入 PATH")

	try:
		return subprocess.run(
			[adb_path, "-s", serial, *args],
			check=True,
			capture_output=True,
			text=True,
			timeout=timeout_seconds,
		)
	except subprocess.TimeoutExpired as exc:
		raise RuntimeError(f"adb 指令超時（{timeout_seconds}s）: {' '.join(args)}") from exc


def capture_screenshot(serial: str, timeout_seconds: int) -> Image.Image:
	adb_path = shutil.which("adb")
	if adb_path is None:
		raise RuntimeError("找不到 adb 指令，請先安裝 platform-tools 並加入 PATH")

	with NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
		temp_path = Path(temp_file.name)

	try:
		with temp_path.open("wb") as output_file:
			subprocess.run(
				[adb_path, "-s", serial, "exec-out", "screencap", "-p"],
				check=True,
				stdout=output_file,
				stderr=subprocess.PIPE,
				timeout=timeout_seconds,
			)

		with Image.open(temp_path) as image:
			return image.copy()
	finally:
		if temp_path.exists():
			temp_path.unlink()


def crop_grid_region(
	image: Image.Image,
	grid_x: int,
	grid_y: int,
	grid_width: int,
	grid_height: int,
) -> Image.Image:
	left = max(0, grid_x)
	top = max(0, grid_y)
	right = min(image.width, left + grid_width)
	bottom = min(image.height, top + grid_height)

	if left >= right or top >= bottom:
		raise RuntimeError("裁切範圍無效，請檢查 grid_x/grid_y/grid_width/grid_height")

	return image.crop((left, top, right, bottom))


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


def save_tiles(tiles: list[list[Image.Image]], output_dir: Path) -> None:
	output_dir.mkdir(parents=True, exist_ok=True)
	for row_index, row_tiles in enumerate(tiles):
		for col_index, tile in enumerate(row_tiles):
			tile_path = output_dir / f"r{row_index:02d}_c{col_index:02d}.png"
			tile.save(tile_path)


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="ADB 截圖、裁切並切成格子後存到 res 底下")
	parser.add_argument("--serial", default=ADB_SERIAL, help="ADB 裝置序號，預設 emulator-5554")
	parser.add_argument("--out", default=None, help="輸出資料夾前綴，預設為時間戳")
	parser.add_argument("--grid-x", type=int, default=DEFAULT_GRID_X, help="裁切區左上角 X")
	parser.add_argument("--grid-y", type=int, default=DEFAULT_GRID_Y, help="裁切區左上角 Y")
	parser.add_argument("--grid-width", type=int, default=DEFAULT_GRID_WIDTH, help="裁切區寬度")
	parser.add_argument("--grid-height", type=int, default=DEFAULT_GRID_HEIGHT, help="裁切區高度")
	parser.add_argument("--rows", type=int, default=DEFAULT_ROWS, help="網格列數")
	parser.add_argument("--cols", type=int, default=DEFAULT_COLS, help="網格欄數")
	parser.add_argument("--save-full", action="store_true", help="是否同時儲存完整裁切圖")
	parser.add_argument("--timeout", type=int, default=ADB_TIMEOUT_SECONDS, help="adb 指令逾時秒數")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	run_adb(["get-state"], args.serial, args.timeout)
	image = capture_screenshot(args.serial, args.timeout)
	cropped = crop_grid_region(image, args.grid_x, args.grid_y, args.grid_width, args.grid_height)
	tiles = split_image(cropped, args.rows, args.cols)

	output_name = args.out or datetime.now().strftime("capture_%Y%m%d_%H%M%S")
	output_dir = RES_DIR / output_name
	output_dir.mkdir(parents=True, exist_ok=True)

	if args.save_full:
		cropped.save(output_dir / "grid.png")

	save_tiles(tiles, output_dir / "tiles")
	print(f"儲存路徑: {output_dir}")


if __name__ == "__main__":
	main()

