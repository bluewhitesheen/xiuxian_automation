"""Action helpers for BlueStacks automation."""
from __future__ import annotations

from io import BytesIO
import re
import time
import subprocess
from typing import Final
from PIL import Image

from core.adb_utils import run_adb


APP_PACKAGE: Final[str] = "com.dustglobal.googleplay.xiuxian"
ADB_EMULATOR_SERIAL: Final[str] = "emulator-5554"
ADB_WAIT_TIMEOUT_SECONDS: Final[int] = 120
MEMINFO_TABLE_HEADERS: Final[tuple[str, ...]] = (
	"Pss",
	"Private Dirty",
	"Private Clean",
	"SwapPss",
	"Heap Size",
	"Heap Alloc",
	"Heap Free",
)


def _parse_meminfo_table(raw_output: str) -> dict[str, dict[str, int]]:
	"""Parse `dumpsys meminfo` 2D table into dict[row_name][metric]=value."""
	lines = raw_output.splitlines()
	inside_table = False
	row_layout: dict[str, dict[str, int]] = {}

	header_pattern = re.compile(r"^\s*Pss\s+Private\s+Private\s+SwapPss\s+Heap\s+Heap\s+Heap\b")
	numbered_row_pattern = re.compile(r"^\s*(?P<row>.+?)\s+(?P<numbers>(\d+\s+)+\d+)\s*$")

	for line in lines:
		if not inside_table:
			if header_pattern.match(line):
				inside_table = True
			continue

		if line.startswith(" App Summary") or line.startswith("App Summary"):
			break

		if not line.strip() or set(line.strip()) == {"-"}:
			continue

		match = numbered_row_pattern.match(line)
		if not match:
			continue

		row_name = match.group("row").strip()
		raw_numbers = match.group("numbers").split()
		values = [int(v) for v in raw_numbers]
		if len(values) < len(MEMINFO_TABLE_HEADERS):
			values.extend([0] * (len(MEMINFO_TABLE_HEADERS) - len(values)))

		row_layout[row_name] = {
			header: value
			for header, value in zip(MEMINFO_TABLE_HEADERS, values[: len(MEMINFO_TABLE_HEADERS)])
		}

	memory_layout: dict[str, dict[str, int]] = dict(row_layout)
	for header in MEMINFO_TABLE_HEADERS:
		memory_layout[f"{header} Total"] = {
			row: columns.get(header, 0) for row, columns in row_layout.items()
		}

	return memory_layout


def _get_adb_device_state(serial: str) -> str | None:
	"""Return adb device state for the given serial, e.g. 'device'/'offline'."""
	devices = subprocess.run(
		["adb", "devices"],
		capture_output=True,
		text=True,
		check=False,
	)
	for line in (devices.stdout or "").splitlines():
		parts = line.split()
		if len(parts) >= 2 and parts[0] == serial:
			return parts[1]
	return None


def _wait_for_emulator_ready(serial: str, timeout_seconds: int = ADB_WAIT_TIMEOUT_SECONDS) -> None:
	"""Wait until emulator serial is online and Android boot is complete."""
	start_time = time.time()
	last_server_restart = 0.0
	while True:
		state = _get_adb_device_state(serial)
		if state == "device":
			boot_completed = subprocess.run(
				["adb", "-s", serial, "shell", "getprop", "sys.boot_completed"],
				capture_output=True,
				text=True,
				check=False,
			)
			if (boot_completed.stdout or "").strip() == "1":
				return

		if state == "offline" and time.time() - last_server_restart > 8:
			subprocess.run(["adb", "kill-server"], check=False, capture_output=True, text=True)
			subprocess.run(["adb", "start-server"], check=False, capture_output=True, text=True)
			last_server_restart = time.time()

		if time.time() - start_time > timeout_seconds:
			raise RuntimeError(f"Timed out waiting for adb device {serial} to become ready")
		time.sleep(1)


def tap_pixel(adb_serial: str, x: int, y: int) -> None:
	"""Tap absolute pixel coordinate on device."""
	run_adb(
		adb_serial,
		["shell", "input", "tap", str(x), str(y)],
	)


def read_pixel_rgb(adb_serial: str, x: int, y: int) -> tuple[int, int, int]:
	"""Capture device screenshot and return the RGB tuple at (x, y)."""
	screenshot = run_adb(
		adb_serial,
		["exec-out", "screencap", "-p"],
		capture_output=True,
	)

	raw = screenshot.stdout
	if not isinstance(raw, (bytes, bytearray)):
		raw = str(raw).encode()

	with Image.open(BytesIO(raw)) as image:
		image_rgb = image.convert("RGB")
		width, height = image_rgb.size
		if not (0 <= x < width and 0 <= y < height):
			raise ValueError(f"Pixel coordinate ({x}, {y}) out of bounds for screenshot {width}x{height}")
		return image_rgb.getpixel((x, y))


def restart_game(adb_serial: str) -> None:
	"""Restart BlueStacks and relaunch the target app."""
	subprocess.run(["taskkill", "/F", "/IM", "HD-Player.exe"], check=False)
	subprocess.Popen(
		["C:\\Program Files\\BlueStacks_nxt\\HD-Player.exe"],
	)
	_wait_for_emulator_ready(ADB_EMULATOR_SERIAL)
	for _ in range(3):
		try:
			run_adb(
				adb_serial,
				["shell", "monkey", "-p", APP_PACKAGE, "-c", "android.intent.category.LAUNCHER", "1"],
				capture_output=True,
				text=True,
			)
			break
		except RuntimeError as exc:
			if "device offline" not in str(exc).lower() or _ == 2:
				raise
			_wait_for_emulator_ready(ADB_EMULATOR_SERIAL, timeout_seconds=60)
	time.sleep(15)
	tap_pixel(adb_serial, 270, 1120)
	time.sleep(13)
	tap_pixel(adb_serial, 270, 1035)
	time.sleep(1)

def click_travel(adb_serial: str) -> None:
	tap_pixel(adb_serial, 450, 1250)
	time.sleep(1)

def move_to_right_buttom(adb_serial: str) -> None:
	for _ in range(5):
		run_adb(
			adb_serial,
			["shell", "input", "swipe", "500", "500", "0", "0", "100"],
		)
	time.sleep(0.5)

def show_memory_usage(adb_serial: str) -> dict[str, dict[str, int]]:
	result = run_adb(
		adb_serial, ["shell", "dumpsys", "meminfo", APP_PACKAGE], capture_output=True, text=True
	)
	output = result.stdout or ""
	return _parse_meminfo_table(output)

