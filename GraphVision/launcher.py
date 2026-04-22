import subprocess
import sys
from pathlib import Path

# rxconfig.py lives one level above this package directory
_REFLEX_ROOT = Path(__file__).parent.parent


def run(env: str = "dev") -> None:
    cmd = [sys.executable, "-m", "reflex", "run"]
    if env == "prod":
        cmd += ["--env", "prod"]
    subprocess.run(cmd, cwd=_REFLEX_ROOT, check=True)
