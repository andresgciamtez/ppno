"""Pytest configuration for local source imports."""

import sys
import types
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
root_path = str(PROJECT_ROOT)

if root_path in sys.path:
    sys.path.remove(root_path)
sys.path.insert(0, root_path)

try:
    import pygmo  # noqa: F401
except ImportError:
    pygmo_stub = types.ModuleType("pygmo")
    pygmo_stub.set_global_rng_seed = lambda seed: None
    sys.modules["pygmo"] = pygmo_stub
