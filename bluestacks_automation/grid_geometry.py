from __future__ import annotations

from typing import Final

# Legacy fixed values (screen: 2160x5120).
GRID_ROWS: Final[int] = 13
GRID_COLS: Final[int] = 7

GRID_LEFT_PX: Final[int] = 120
GRID_TOP_PX: Final[int] = 640
GRID_WIDTH_PX: Final[int] = 840
GRID_HEIGHT_PX: Final[int] = 1560

GRID_CELL_PX_X: Final[int] = 120
GRID_CELL_PX_Y: Final[int] = 120
GRID_CELL_CENTER_OFFSET_X: Final[int] = 60
GRID_CELL_CENTER_OFFSET_Y: Final[int] = 60

UI_START_1_PX: tuple[int, int] = (725, 1183)
UI_START_2_PX: tuple[int, int] = (560, 1725)
UI_CLEAR_MENU_PX: tuple[int, int] = (60, 60)
UI_CONFIRM_CLOSE_PX: tuple[int, int] = (700, 1440)
UI_MONSTER_TAP_1_PX: tuple[int, int] = (600, 1500)
UI_MONSTER_TAP_2_PX: tuple[int, int] = (500, 2500)
