from __future__ import annotations

from datetime import datetime
from pathlib import Path
import time
import sys

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from map_module._bootstrap import ensure_repo_root_on_path
from map_module.capture_and_split import ADB_SERIAL, ADB_TIMEOUT_SECONDS, capture_screenshot

# 修改這四個值即可改讀取位置和間隔
PIXEL_X = 373
PIXEL_Y = 942
DELAY_SECONDS = 0


def get_pixel_rgb(image: Image.Image, x: int, y: int) -> tuple[int, int, int]:
	image_rgb = image.convert("RGB")
	return image_rgb.getpixel((x, y))


def main() -> None:
	ensure_repo_root_on_path()

	while True:
		try:
			image = capture_screenshot(ADB_SERIAL, ADB_TIMEOUT_SECONDS)
			if not (0 <= PIXEL_X < image.width and 0 <= PIXEL_Y < image.height):
				raise RuntimeError(f"pixel coordinate out of bounds for current screenshot: {image.width}x{image.height}")

			pixel = get_pixel_rgb(image, PIXEL_X, PIXEL_Y)
			now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
			print(f"[{now}] ({PIXEL_X}, {PIXEL_Y}) = RGB{pixel}")
		except KeyboardInterrupt:
			print("Stopped by user")
			break
		except Exception as exc:
			print(f"ERROR: {exc}", file=sys.stderr)
		time.sleep(DELAY_SECONDS)


if __name__ == "__main__":
	main()
