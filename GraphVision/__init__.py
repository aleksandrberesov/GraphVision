
import sys
from pathlib import Path

_pkg_root = Path(__file__).parent.parent
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

from .GraphVision import app
from .runner import run

__all__ = ["app", "run"]
