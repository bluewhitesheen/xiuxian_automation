from __future__ import annotations

from pathlib import Path
import argparse
import sys

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from core.capture import capture_screenshot_via_exec_out

RES_DIR = PROJECT_ROOT / "res" / "result"

ADB_DEFAULT_SERIAL = "emulator-5554"
ADB_DEFAULT_TIMEOUT_SECONDS = 10

GRID_START_X = 23
GRID_START_Y = 472
GRID_CELL_SIZE = 71
GRID_GAP_X = 14
GRID_GAP_Y = 21
GRID_ROWS = 8
GRID_COLS = 6


def capture_full_screenshot(serial: str, timeout_seconds: int) -> Image.Image:
	image_buffer = capture_screenshot_via_exec_out(serial, timeout_seconds=timeout_seconds)
	with Image.open(image_buffer) as image:
		return image.copy()


def crop_cell(image: Image.Image, row: int, col: int) -> Image.Image:
	left = GRID_START_X + col * (GRID_CELL_SIZE + GRID_GAP_X)
	top = GRID_START_Y + row * (GRID_CELL_SIZE + GRID_GAP_Y)
	right = left + GRID_CELL_SIZE
	bottom = top + GRID_CELL_SIZE
	return image.crop((left, top, right, bottom))


def save_treasure_cells(serial: str, timeout_seconds: int) -> Path:
	image = capture_full_screenshot(serial, timeout_seconds)
	RES_DIR.mkdir(parents=True, exist_ok=True)

	for row in range(GRID_ROWS):
		for col in range(GRID_COLS):
			cell = crop_cell(image, row, col)
			cell.save(RES_DIR / f"{row}_{col}.png")

	return RES_DIR


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Capture 8x6 treasure grid images from device screen.")
	parser.add_argument("--serial", default=ADB_DEFAULT_SERIAL, help="ADB serial, e.g. emulator-5554")
	parser.add_argument("--timeout", type=int, default=ADB_DEFAULT_TIMEOUT_SECONDS, help="ADB timeout seconds")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	output_dir = save_treasure_cells(args.serial, args.timeout)
	print(f"Saved 8x6 treasure images to: {output_dir}")


if __name__ == "__main__":
	main()
