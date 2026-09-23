from __future__ import annotations

from pathlib import Path
from typing import Iterable, Union

import cv2
import numpy as np

ImageLike = Union[str, Path, np.ndarray]


def _load_image(image: ImageLike) -> np.ndarray | None:
    if isinstance(image, (str, Path)):
        image_arr = cv2.imread(str(image), cv2.IMREAD_COLOR)
        if image_arr is None:
            return None
        return image_arr

    array = np.asarray(image)
    if array.ndim != 3:
        return None
    return array


def has_monster_border(
    image: ImageLike,
    *,
    expected_size: tuple[int, int] = (60, 60),
    min_radius: float = 24.0,
    max_radius: float = 30.0,
    center_tolerance: float = 3.0,
    ring_std_threshold: float = 35.0,
) -> bool:
    """Return True if a 60x60 icon appears to have a circular frame border."""

    img = _load_image(image)
    if img is None:
        return False

    if img.shape[0] != expected_size[0] or img.shape[1] != expected_size[1]:
        return False

    gray = cv2.cvtColor(img[..., :3], cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0.0)

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.0,
        minDist=10.0,
        param1=50.0,
        param2=15.0,
        minRadius=int(min_radius),
        maxRadius=int(max_radius),
    )
    if circles is None:
        return False

    height, width = gray.shape
    yy, xx = np.indices((height, width))
    center_x = width / 2.0
    center_y = height / 2.0

    for cx, cy, radius in np.round(circles[0], 2):
        if abs(cx - center_x) > center_tolerance or abs(cy - center_y) > center_tolerance:
            continue
        if not (min_radius <= radius <= max_radius):
            continue

        dist2 = (xx - cx) ** 2 + (yy - cy) ** 2
        ring_mask = (dist2 >= (radius - 1.2) ** 2) & (dist2 <= (radius + 1.2) ** 2)
        ring_pixels = gray[ring_mask]
        if ring_pixels.size == 0:
            continue

        if float(ring_pixels.std()) >= ring_std_threshold:
            return True

    return False


def iter_image_files(root: Path | str = Path("res")) -> Iterable[Path]:
    root_path = Path(root)
    if not root_path.exists():
        return []
    for path in root_path.rglob("*"):
        if path.is_file():
            yield path


def main() -> None:
    root = Path("res")
    for path in iter_image_files(root):
        is_monster = has_monster_border(path)
        try:
            rel_path = str(path.relative_to(Path.cwd()))
        except ValueError:
            rel_path = str(path)
        print(f"{rel_path} {is_monster}")


if __name__ == "__main__":
    main()
