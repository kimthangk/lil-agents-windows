import sys
from pathlib import Path


def resource_path(relative: str) -> str:
    """Resolve asset paths for both dev mode and PyInstaller bundle."""
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent
    return str(base / relative)
