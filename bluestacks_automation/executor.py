from __future__ import annotations

import shlex
import shutil
import subprocess
import time
from typing import List

from bluestacks_automation.grid_geometry import (
    GRID_CELL_CENTER_OFFSET_X,
    GRID_CELL_CENTER_OFFSET_Y,
    GRID_CELL_PX_X,
    GRID_CELL_PX_Y,
    GRID_LEFT_PX,
    GRID_TOP_PX,
    UI_MONSTER_TAP_1_PX,
    UI_MONSTER_TAP_2_PX,
)

GridPoint = tuple[int, int]


# Grid mapping constants.
DEFAULT_ADB_SERIAL = "emulator-5554"


def _grid_to_pixel(point: GridPoint) -> tuple[int, int]:
    row, col = point
    x = GRID_LEFT_PX + col * GRID_CELL_PX_X + GRID_CELL_CENTER_OFFSET_X
    y = GRID_TOP_PX + row * GRID_CELL_PX_Y + GRID_CELL_CENTER_OFFSET_Y
    return x, y


def _adb_tap(x: int, y: int, adb_serial: str | None = None) -> None:
    adb_path = shutil.which("adb")
    if adb_path is None:
        raise RuntimeError("adb not found. Please install Android platform-tools and ensure adb is in PATH")

    serial = adb_serial or DEFAULT_ADB_SERIAL
    cmd = [adb_path, "-s", serial, "shell", "input", "tap", str(x), str(y)]
    print("raw command:", " ".join(shlex.quote(arg) for arg in cmd))
    subprocess.run(cmd, check=True)


def execute_list(
    click_list: List[GridPoint],
    start_pos: GridPoint,
    adb_serial: str | None = None,
) -> GridPoint:
    """
    Execute a sequence of grid points (waypoints) by issuing adb tap commands
    and waiting for the in-game character to move between grids.

    Returns the final grid position after executing the list (or start_pos if list empty).
    """
    if not click_list:
        return start_pos

    current = start_pos
    for point in click_list:
        # compute distance in grid steps (Manhattan)
        dist = abs(point[0] - current[0]) + abs(point[1] - current[1])
        wait_seconds = dist * 0.53
        x, y = _grid_to_pixel(point)
        _adb_tap(x, y, adb_serial)
        # wait for movement to finish before next tap
        time.sleep(wait_seconds)
        current = point

    return current


def tap_pixel(x: int, y: int, adb_serial: str | None = None) -> None:
    """Tap absolute pixel coordinate on device."""
    _adb_tap(x, y, adb_serial)


def interact_with_monster(monster_point: GridPoint, adb_serial: str | None = None) -> None:
    """
    Perform the defined monster interaction sequence:
    1) tap monster cell
    2) wait 0.5s and tap (1200, 3000)
    3) wait 5.0s and tap (1000, 5000)
    """
    # tap monster cell
    x, y = _grid_to_pixel(monster_point)
    _adb_tap(x, y, adb_serial)
    time.sleep(0.5)
    monster_tap_x, monster_tap_y = UI_MONSTER_TAP_1_PX
    _adb_tap(monster_tap_x, monster_tap_y, adb_serial)
    time.sleep(6.5)
    monster_done_x, monster_done_y = UI_MONSTER_TAP_2_PX
    _adb_tap(monster_done_x, monster_done_y, adb_serial)
    time.sleep(0.5)
