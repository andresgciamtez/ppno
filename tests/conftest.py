"""Pytest configuration for local source imports."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
root_path = str(PROJECT_ROOT)

if root_path in sys.path:
    sys.path.remove(root_path)
sys.path.insert(0, root_path)
