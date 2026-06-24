from __future__ import annotations

from typing import Final

# Legacy fixed values (screen: 2160x5120).
GRID_ROWS: Final[int] = 13
GRID_COLS: Final[int] = 7

GRID_LEFT_PX: Final[int] = 240
GRID_TOP_PX: Final[int] = 1280
GRID_WIDTH_PX: Final[int] = 1680
GRID_HEIGHT_PX: Final[int] = 3120

GRID_CELL_PX_X: Final[int] = 240
GRID_CELL_PX_Y: Final[int] = 240
GRID_CELL_CENTER_OFFSET_X: Final[int] = 120
GRID_CELL_CENTER_OFFSET_Y: Final[int] = 120

UI_START_1_PX: tuple[int, int] = (1450, 2365)
UI_START_2_PX: tuple[int, int] = (1120, 3450)
UI_CLEAR_MENU_PX: tuple[int, int] = (120, 120)
UI_CONFIRM_CLOSE_PX: tuple[int, int] = (1400, 2880)
UI_MONSTER_TAP_1_PX: tuple[int, int] = (1200, 3000)
UI_MONSTER_TAP_2_PX: tuple[int, int] = (1000, 5000)
