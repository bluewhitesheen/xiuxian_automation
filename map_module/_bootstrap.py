from __future__ import annotations

from pathlib import Path
import sys

def ensure_repo_root_on_path() -> Path:
	"""Ensure project root is importable when this module is run as a script."""
	project_root = Path(__file__).resolve().parent.parent
	root_str = str(project_root)
	if root_str not in sys.path:
		sys.path.insert(0, root_str)
	return project_root
