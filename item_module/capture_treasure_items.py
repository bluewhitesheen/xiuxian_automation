from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.actions import tap_pixel
from core.capture import capture_screenshot_via_exec_out
from item_module import print_color_percent

RES_DIR = PROJECT_ROOT / "result"

ADB_SERIAL = "emulator-5554"
ADB_TIMEOUT_SECONDS = 10

GRID_ROWS = 8
GRID_COLS = 6
GRID_START_X = 23
GRID_START_Y = 472
GRID_CELL_SIZE = 71
GRID_GAP_X = 14
GRID_GAP_Y = 21

CROP_LEFT = 84
CROP_TOP = 660
CROP_RIGHT = 332
CROP_BOTTOM = 740

CONFIRM_TAP_X = 200
CONFIRM_TAP_Y = 860
ITEM_BLUE = (173, 207, 255)
ITEM_GOLD = (239, 215, 165)
COLOR_THRESHOLD = 10


def capture_full_screenshot(serial: str, timeout_seconds: int) -> Image.Image:
    image_buffer = capture_screenshot_via_exec_out(serial, timeout_seconds=timeout_seconds)
    with Image.open(image_buffer) as image:
        return image.copy()


def crop_item_cell(image: Image.Image, row: int, col: int) -> Image.Image:
    left = GRID_START_X + col * (GRID_CELL_SIZE + GRID_GAP_X)
    top = GRID_START_Y + row * (GRID_CELL_SIZE + GRID_GAP_Y)
    return image.crop((left, top, left + GRID_CELL_SIZE, top + GRID_CELL_SIZE))


def crop_region(image: Image.Image) -> Image.Image:
    right = min(CROP_RIGHT, image.width)
    bottom = min(CROP_BOTTOM, image.height)
    return image.crop((CROP_LEFT, CROP_TOP, right, bottom))


def grid_cell_center(row: int, col: int) -> tuple[int, int]:
    x = GRID_START_X + col * (GRID_CELL_SIZE + GRID_GAP_X) + (GRID_CELL_SIZE // 2)
    y = GRID_START_Y + row * (GRID_CELL_SIZE + GRID_GAP_Y) + (GRID_CELL_SIZE // 2)
    return x, y


def is_target_color_present(cell_image: Image.Image, target_color: tuple[int, int, int]) -> bool:
    pixel = cell_image.convert("RGB").getpixel((10, 10))
    dr = pixel[0] - target_color[0]
    dg = pixel[1] - target_color[1]
    db = pixel[2] - target_color[2]
    distance = math.sqrt(dr * dr + dg * dg + db * db)
    return distance <= COLOR_THRESHOLD


def capture_treasure_grid(serial: str, timeout_seconds: int) -> Path:
    RES_DIR.mkdir(parents=True, exist_ok=True)

    cell_image = []
    screenshot = capture_full_screenshot(serial, timeout_seconds)
    for row in range(GRID_ROWS):
        row_cells = []
        for col in range(GRID_COLS):
            row_cells.append(crop_item_cell(screenshot, row, col))
        cell_image.append(row_cells)

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            # save all white image with same size if target color appears
            if is_target_color_present(cell_image[row][col], ITEM_BLUE):
                Image.new("RGB", (CROP_RIGHT - CROP_LEFT, CROP_BOTTOM - CROP_TOP), color=(255, 255, 255)).save(
                    RES_DIR / f"{row}_{col}.png"
                )
                continue

            if is_target_color_present(cell_image[row][col], ITEM_GOLD):
                return RES_DIR

            center_x, center_y = grid_cell_center(row, col)
            tap_pixel(serial, center_x, center_y)
            time.sleep(0.5)

            screenshot = capture_full_screenshot(serial, timeout_seconds)
            cropped = crop_region(screenshot)
            cropped.save(RES_DIR / f"{row}_{col}.png")

            tap_pixel(serial, CONFIRM_TAP_X, CONFIRM_TAP_Y)
            time.sleep(0.5)

    return RES_DIR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture item info screenshots for an 8x6 grid.")
    parser.add_argument("--serial", default=ADB_SERIAL, help="ADB serial, e.g. emulator-5554")
    parser.add_argument("--timeout", type=int, default=ADB_TIMEOUT_SECONDS, help="ADB timeout seconds")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = capture_treasure_grid(args.serial, args.timeout)
    print_color_percent.analyze_result_dir(output_dir, show_popup=True)


if __name__ == "__main__":
	main()
