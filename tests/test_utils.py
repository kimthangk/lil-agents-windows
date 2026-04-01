import sys
from pathlib import Path
import importlib


def test_resource_path_dev_mode():
    """In dev mode (no _MEIPASS), returns path relative to project root."""
    if hasattr(sys, "_MEIPASS"):
        delattr(sys, "_MEIPASS")

    import utils
    importlib.reload(utils)

    result = Path(utils.resource_path("assets/bruce.gif"))
    assert result.parts[-2:] == ("assets", "bruce.gif")


def test_resource_path_bundle_mode(tmp_path):
    """In bundle mode (_MEIPASS set), returns path relative to _MEIPASS."""
    sys._MEIPASS = str(tmp_path)

    import utils
    importlib.reload(utils)

    result = Path(utils.resource_path("assets/bruce.gif"))
    assert result == tmp_path / "assets" / "bruce.gif"

    del sys._MEIPASS
