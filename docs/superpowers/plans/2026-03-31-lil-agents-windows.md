# Lil Agents Windows Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows port of lil-agents — animated AI companion characters (Bruce and Jazz) that walk above the Windows taskbar and open a terminal-style chat popover on click, powered by Claude Code or Google Gemini CLI.

**Architecture:** A transparent frameless PyQt6 window sits flush above the Windows taskbar (position detected via Win32 `SHAppBarMessage`). Two `WalkerCharacter` (QLabel + QMovie) instances animate GIF sprites inside it. Clicking a character opens a `ChatPopover` (QDialog) that streams AI CLI output in real time via `QProcess`.

**Tech Stack:** Python 3.11+, PyQt6 6.6+, ctypes/Win32, PyInstaller 6+, pytest + pytest-qt 4.4+

---

## File Map

| File | Responsibility |
|---|---|
| `main.py` | Entry point: QApplication, OverlayWindow, characters, system tray |
| `overlay_window.py` | Transparent frameless window above taskbar; Win32 geometry helpers |
| `walker_character.py` | GIF animation + walking logic for one character |
| `chat_popover.py` | Terminal-style chat QDialog; slash commands; position helper |
| `agent_session.py` | Base class: QProcess lifecycle, stdout/stderr streaming |
| `claude_session.py` | `claude -p <input>` subprocess |
| `gemini_session.py` | `gemini <input>` subprocess |
| `config.py` | Read/write `%APPDATA%\LilAgents\config.json` |
| `utils.py` | `resource_path()` for dev + PyInstaller bundle |
| `tools/convert_assets.py` | One-time ffmpeg + Pillow conversion of .mov → .gif, .png → .ico |
| `tests/test_config.py` | Config persistence unit tests |
| `tests/test_utils.py` | resource_path unit test |
| `tests/test_agent_session.py` | AgentSession command construction tests |
| `tests/test_walker_character.py` | Walking logic unit tests |
| `tests/test_overlay_window.py` | Geometry calculation unit tests |
| `tests/test_chat_popover.py` | Position calculation + slash command tests |
| `requirements.txt` | Runtime deps |
| `requirements-dev.txt` | Test/build deps |
| `lil_agents.spec` | PyInstaller build config |
| `build.bat` | One-command build script |

---

## Task 1: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `.gitignore`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `requirements.txt`**

```
PyQt6>=6.6.0
PyQt6-Qt6>=6.6.0
```

- [ ] **Step 2: Create `requirements-dev.txt`**

```
pytest>=8.0.0
pytest-qt>=4.4.0
Pillow>=10.0.0
pyinstaller>=6.0.0
```

- [ ] **Step 3: Create `.gitignore`**

```
__pycache__/
*.pyc
*.pyo
.venv/
venv/
dist/
build/
*.spec.bak
.pytest_cache/
```

- [ ] **Step 4: Create empty `tests/__init__.py`**

Create an empty file at `tests/__init__.py`.

- [ ] **Step 5: Create a Python virtual environment and install deps**

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
```

Expected: all packages install without errors.

- [ ] **Step 6: Verify pytest runs (empty suite)**

```bash
pytest tests/ -v
```

Expected: `no tests ran` — zero failures.

- [ ] **Step 7: Commit**

```bash
git add requirements.txt requirements-dev.txt .gitignore tests/__init__.py
git commit -m "chore: project scaffolding and dependencies"
```

---

## Task 2: Asset conversion tool

**Files:**
- Create: `tools/__init__.py`
- Create: `tools/convert_assets.py`
- Create: `assets/` directory (populated by running the script)

**Prerequisite:** Fork https://github.com/ryanstephen/lil-agents and clone it locally. The `.mov` files and `menuicon.png` are inside the `LilAgents/` folder of that repo.

- [ ] **Step 1: Create empty `tools/__init__.py`**

Create an empty file at `tools/__init__.py`.

- [ ] **Step 2: Create `tools/convert_assets.py`**

```python
#!/usr/bin/env python3
"""
One-time script to convert original lil-agents .mov and .png assets for Windows.

Requirements:
    - ffmpeg on PATH  (https://ffmpeg.org/download.html)
    - Pillow: pip install Pillow

Usage:
    python tools/convert_assets.py --mov-dir /path/to/lil-agents/LilAgents
"""
import argparse
import subprocess
from pathlib import Path


def convert_gif(mov_path: Path, out_path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(mov_path),
            "-vf", "fps=15,scale=80:-1:flags=lanczos",
            str(out_path),
        ],
        check=True,
    )


def convert_ico(png_path: Path, out_path: Path) -> None:
    from PIL import Image
    img = Image.open(str(png_path))
    img.save(str(out_path), format="ICO", sizes=[(32, 32), (16, 16)])


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert lil-agents assets for Windows")
    parser.add_argument(
        "--mov-dir",
        required=True,
        help="Path to LilAgents/ source directory containing .mov files and menuicon.png",
    )
    args = parser.parse_args()

    mov_dir = Path(args.mov_dir)
    assets_dir = Path(__file__).parent.parent / "assets"
    assets_dir.mkdir(exist_ok=True)

    print("Converting bruce.gif ...")
    convert_gif(mov_dir / "walk-bruce-01.mov", assets_dir / "bruce.gif")

    print("Converting jazz.gif ...")
    convert_gif(mov_dir / "walk-jazz-01.mov", assets_dir / "jazz.gif")

    print("Converting icon.ico ...")
    convert_ico(mov_dir / "menuicon.png", assets_dir / "icon.ico")

    print("Done. Assets written to:", assets_dir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run the conversion (requires ffmpeg on PATH)**

```bash
python tools/convert_assets.py --mov-dir /path/to/lil-agents/LilAgents
```

Expected output:
```
Converting bruce.gif ...
Converting jazz.gif ...
Converting icon.ico ...
Done. Assets written to: <project>/assets
```

Verify `assets/bruce.gif`, `assets/jazz.gif`, `assets/icon.ico` all exist.

- [ ] **Step 4: Commit assets and tool**

```bash
git add tools/__init__.py tools/convert_assets.py assets/bruce.gif assets/jazz.gif assets/icon.ico
git commit -m "feat: add asset conversion tool and converted GIF/ico assets"
```

---

## Task 3: `utils.py` — resource_path helper

**Files:**
- Create: `utils.py`
- Create: `tests/test_utils.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_utils.py`:

```python
import sys
from pathlib import Path
import importlib


def test_resource_path_dev_mode():
    """In dev mode (no _MEIPASS), returns path relative to project root."""
    # Ensure _MEIPASS is not set
    if hasattr(sys, "_MEIPASS"):
        delattr(sys, "_MEIPASS")

    import utils
    importlib.reload(utils)

    result = Path(utils.resource_path("assets/bruce.gif"))
    # Should resolve to <project_root>/assets/bruce.gif
    assert result.parts[-2:] == ("assets", "bruce.gif")


def test_resource_path_bundle_mode(tmp_path):
    """In bundle mode (_MEIPASS set), returns path relative to _MEIPASS."""
    sys._MEIPASS = str(tmp_path)

    import utils
    importlib.reload(utils)

    result = Path(utils.resource_path("assets/bruce.gif"))
    assert result == tmp_path / "assets" / "bruce.gif"

    del sys._MEIPASS
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_utils.py -v
```

Expected: `ModuleNotFoundError: No module named 'utils'`

- [ ] **Step 3: Create `utils.py`**

```python
import sys
from pathlib import Path


def resource_path(relative: str) -> str:
    """Resolve asset paths for both dev mode and PyInstaller bundle."""
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent
    return str(base / relative)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_utils.py -v
```

Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add utils.py tests/test_utils.py
git commit -m "feat: add resource_path helper for dev and bundled modes"
```

---

## Task 4: `config.py` — config persistence

**Files:**
- Create: `config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_config.py`:

```python
import json
import pytest
from pathlib import Path


def test_load_config_returns_empty_when_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    import config
    result = config.load_config()
    assert result == {}


def test_save_and_load_config(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    import config
    config.save_config({"provider": "gemini"})
    result = config.load_config()
    assert result == {"provider": "gemini"}


def test_get_provider_defaults_to_claude(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    import config
    assert config.get_provider() == "claude"


def test_set_and_get_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    import config
    config.set_provider("gemini")
    assert config.get_provider() == "gemini"


def test_config_file_is_valid_json(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    import config
    config.set_provider("claude")
    config_file = tmp_path / "LilAgents" / "config.json"
    data = json.loads(config_file.read_text())
    assert data["provider"] == "claude"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'config'`

- [ ] **Step 3: Create `config.py`**

```python
import json
import os
from pathlib import Path


def _config_path() -> Path:
    appdata = os.environ.get("APPDATA", str(Path.home()))
    config_dir = Path(appdata) / "LilAgents"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def load_config() -> dict:
    path = _config_path()
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_config(data: dict) -> None:
    path = _config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_provider() -> str:
    return load_config().get("provider", "claude")


def set_provider(provider: str) -> None:
    data = load_config()
    data["provider"] = provider
    save_config(data)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_config.py -v
```

Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add config.py tests/test_config.py
git commit -m "feat: config persistence for provider selection"
```

---

## Task 5: `agent_session.py` — base session class

**Files:**
- Create: `agent_session.py`
- Create: `tests/test_agent_session.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_agent_session.py`:

```python
import pytest
from agent_session import AgentSession


class EchoSession(AgentSession):
    """Concrete session that runs Python to echo its input."""
    def _command(self) -> tuple[str, list[str]]:
        import sys
        return sys.executable, ["-c", "import sys; print(sys.argv[1])"]


def test_command_returns_tuple():
    session = EchoSession()
    program, args = session._command()
    assert isinstance(program, str)
    assert isinstance(args, list)


def test_output_received_emits(qtbot):
    session = EchoSession()
    received = []
    session.output_received.connect(received.append)
    session.send("hello")
    qtbot.waitSignal(session.finished, timeout=5000)
    assert any("hello" in chunk for chunk in received)


def test_stop_does_not_raise_when_not_running():
    session = EchoSession()
    session.stop()  # Should not raise


def test_send_kills_previous_process(qtbot):
    """Calling send() while a process is running should kill and restart."""
    import sys
    session = EchoSession()
    session.send("first")
    # Immediately send again — should not raise or hang
    session.send("second")
    qtbot.waitSignal(session.finished, timeout=5000)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_agent_session.py -v
```

Expected: `ModuleNotFoundError: No module named 'agent_session'`

- [ ] **Step 3: Create `agent_session.py`**

```python
from PyQt6.QtCore import QObject, QProcess, pyqtSignal


class AgentSession(QObject):
    output_received = pyqtSignal(str)
    error_received = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process = QProcess(self)
        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.readyReadStandardError.connect(self._on_stderr)
        self._process.finished.connect(self.finished)

    def _command(self) -> tuple[str, list[str]]:
        """Return (program, base_args). Input text is appended as the last arg."""
        raise NotImplementedError

    def send(self, text: str) -> None:
        if self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.kill()
            self._process.waitForFinished(1000)
        program, args = self._command()
        self._process.start(program, args + [text])

    def stop(self) -> None:
        if self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.kill()
            self._process.waitForFinished(1000)

    def _on_stdout(self) -> None:
        data = self._process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        self.output_received.emit(data)

    def _on_stderr(self) -> None:
        data = self._process.readAllStandardError().data().decode("utf-8", errors="replace")
        self.error_received.emit(data)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_agent_session.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add agent_session.py tests/test_agent_session.py
git commit -m "feat: AgentSession base class with QProcess streaming"
```

---

## Task 6: `claude_session.py` + `gemini_session.py`

**Files:**
- Create: `claude_session.py`
- Create: `gemini_session.py`
- Create: `tests/test_claude_session.py`
- Create: `tests/test_gemini_session.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_claude_session.py`:

```python
from claude_session import ClaudeSession


def test_command_uses_claude_binary():
    session = ClaudeSession()
    program, args = session._command()
    assert program == "claude"


def test_command_includes_print_flag():
    session = ClaudeSession()
    program, args = session._command()
    assert "-p" in args
```

Create `tests/test_gemini_session.py`:

```python
from gemini_session import GeminiSession


def test_command_uses_gemini_binary():
    session = GeminiSession()
    program, args = session._command()
    assert program == "gemini"


def test_command_has_no_extra_flags():
    session = GeminiSession()
    program, args = session._command()
    assert args == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_claude_session.py tests/test_gemini_session.py -v
```

Expected: `ModuleNotFoundError` for both modules.

- [ ] **Step 3: Create `claude_session.py`**

```python
from agent_session import AgentSession


class ClaudeSession(AgentSession):
    def _command(self) -> tuple[str, list[str]]:
        return "claude", ["-p"]
```

- [ ] **Step 4: Create `gemini_session.py`**

```python
from agent_session import AgentSession


class GeminiSession(AgentSession):
    def _command(self) -> tuple[str, list[str]]:
        return "gemini", []
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_claude_session.py tests/test_gemini_session.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add claude_session.py gemini_session.py tests/test_claude_session.py tests/test_gemini_session.py
git commit -m "feat: ClaudeSession and GeminiSession subprocess wrappers"
```

---

## Task 7: `walker_character.py` — GIF animation + walking

**Files:**
- Create: `walker_character.py`
- Create: `tests/test_walker_character.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_walker_character.py`:

```python
import pytest
from pathlib import Path
from PyQt6.QtWidgets import QWidget
from walker_character import WalkerCharacter, WALK_SPEED

# Minimal valid 1x1 animated GIF (2 frames, transparent)
MINIMAL_GIF = (
    b"GIF89a\x01\x00\x01\x00\xf0\x00\x00\xff\xff\xff\x00\x00\x00"
    b"!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00"
    b"\x02\x02D\x01\x00;"
)


@pytest.fixture
def gif_file(tmp_path):
    p = tmp_path / "test.gif"
    p.write_bytes(MINIMAL_GIF)
    return str(p)


@pytest.fixture
def container(qtbot):
    w = QWidget()
    w.resize(800, 80)
    qtbot.addWidget(w)
    w.show()
    return w


def test_initial_direction_is_right(gif_file, container, qtbot):
    char = WalkerCharacter(gif_file, parent=container)
    char.resize(80, 80)
    char.move(100, 0)
    qtbot.addWidget(char)
    assert char._direction == 1


def test_step_moves_right(gif_file, container, qtbot):
    char = WalkerCharacter(gif_file, parent=container)
    char.resize(80, 80)
    char.move(100, 0)
    qtbot.addWidget(char)
    initial_x = char.x()
    char._step()
    assert char.x() == initial_x + WALK_SPEED


def test_reverses_at_right_edge(gif_file, container, qtbot):
    char = WalkerCharacter(gif_file, parent=container)
    char.resize(80, 80)
    # Place at right edge (container.width() - char.width() = 720)
    char.move(720, 0)
    qtbot.addWidget(char)
    char._step()
    assert char._direction == -1


def test_reverses_at_left_edge(gif_file, container, qtbot):
    char = WalkerCharacter(gif_file, parent=container)
    char.resize(80, 80)
    char.move(0, 0)
    char._direction = -1
    qtbot.addWidget(char)
    char._step()
    assert char._direction == 1


def test_pause_stops_timer(gif_file, container, qtbot):
    char = WalkerCharacter(gif_file, parent=container)
    char.resize(80, 80)
    char.move(100, 0)
    qtbot.addWidget(char)
    char.pause()
    assert not char._timer.isActive()


def test_resume_restarts_timer(gif_file, container, qtbot):
    char = WalkerCharacter(gif_file, parent=container)
    char.resize(80, 80)
    char.move(100, 0)
    qtbot.addWidget(char)
    char.pause()
    char.resume()
    assert char._timer.isActive()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_walker_character.py -v
```

Expected: `ModuleNotFoundError: No module named 'walker_character'`

- [ ] **Step 3: Create `walker_character.py`**

```python
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QMovie, QTransform

WALK_SPEED = 2       # pixels per timer tick
TIMER_INTERVAL = 16  # ms (~60 fps)


class WalkerCharacter(QLabel):
    clicked = pyqtSignal(object)  # emits self

    def __init__(self, gif_path: str, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._direction = 1  # 1 = right, -1 = left
        self._movie = QMovie(gif_path)
        self._movie.frameChanged.connect(self._update_frame)
        self._movie.start()
        self._timer = QTimer(self)
        self._timer.setInterval(TIMER_INTERVAL)
        self._timer.timeout.connect(self._step)
        self._timer.start()

    def _update_frame(self, _: int) -> None:
        frame = self._movie.currentPixmap()
        if self._direction == -1:
            frame = frame.transformed(QTransform().scale(-1, 1))
        self.setPixmap(frame)

    def _step(self) -> None:
        parent = self.parent()
        if parent is None:
            return
        max_x = parent.width() - self.width()
        new_x = self.x() + (WALK_SPEED * self._direction)
        if new_x >= max_x:
            new_x = max_x
            self._direction = -1
        elif new_x <= 0:
            new_x = 0
            self._direction = 1
        self.move(new_x, self.y())

    def pause(self) -> None:
        self._timer.stop()
        self._movie.setPaused(True)

    def resume(self) -> None:
        self._movie.setPaused(False)
        self._timer.start()

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self)
        super().mousePressEvent(event)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_walker_character.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add walker_character.py tests/test_walker_character.py
git commit -m "feat: WalkerCharacter with GIF animation and walking logic"
```

---

## Task 8: `overlay_window.py` — taskbar overlay

**Files:**
- Create: `overlay_window.py`
- Create: `tests/test_overlay_window.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_overlay_window.py`:

```python
from ctypes import wintypes
from overlay_window import compute_overlay_geometry, OVERLAY_HEIGHT


def _make_rect(left, top, right, bottom) -> wintypes.RECT:
    r = wintypes.RECT()
    r.left = left
    r.top = top
    r.right = right
    r.bottom = bottom
    return r


def test_overlay_sits_above_taskbar():
    rect = _make_rect(0, 1000, 1920, 1040)
    geom = compute_overlay_geometry(rect, 1920)
    assert geom.y() == 1000 - OVERLAY_HEIGHT


def test_overlay_spans_full_screen_width():
    rect = _make_rect(0, 1000, 1920, 1040)
    geom = compute_overlay_geometry(rect, 1920)
    assert geom.width() == 1920


def test_overlay_height_matches_constant():
    rect = _make_rect(0, 1000, 1920, 1040)
    geom = compute_overlay_geometry(rect, 1920)
    assert geom.height() == OVERLAY_HEIGHT


def test_overlay_starts_at_left_edge():
    rect = _make_rect(0, 1000, 1920, 1040)
    geom = compute_overlay_geometry(rect, 1920)
    assert geom.x() == 0


def test_overlay_adapts_to_high_dpi():
    # Simulates a 4K screen at 200% DPI: logical height 540, taskbar at y=500
    rect = _make_rect(0, 500, 960, 540)
    geom = compute_overlay_geometry(rect, 960)
    assert geom.y() == 500 - OVERLAY_HEIGHT
    assert geom.width() == 960
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_overlay_window.py -v
```

Expected: `ModuleNotFoundError: No module named 'overlay_window'`

- [ ] **Step 3: Create `overlay_window.py`**

```python
import ctypes
from ctypes import wintypes

from PyQt6.QtWidgets import QMainWindow, QWidget
from PyQt6.QtCore import Qt, QRect

OVERLAY_HEIGHT = 80  # px — should match GIF height
ABM_GETTASKBARPOS = 0x00000005
WDA_EXCLUDEFROMCAPTURE = 0x00000011


class _APPBARDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uCallbackMessage", wintypes.UINT),
        ("uEdge", wintypes.UINT),
        ("rc", wintypes.RECT),
        ("lParam", wintypes.LPARAM),
    ]


def get_taskbar_rect() -> wintypes.RECT:
    """Query Win32 for the current taskbar position and size."""
    data = _APPBARDATA()
    data.cbSize = ctypes.sizeof(_APPBARDATA)
    ctypes.windll.shell32.SHAppBarMessage(ABM_GETTASKBARPOS, ctypes.byref(data))
    return data.rc


def compute_overlay_geometry(taskbar_rect: wintypes.RECT, screen_width: int) -> QRect:
    """Return QRect for overlay window: full-width strip above the taskbar."""
    return QRect(0, taskbar_rect.top - OVERLAY_HEIGHT, screen_width, OVERLAY_HEIGHT)


class OverlayWindow(QMainWindow):
    def __init__(self, screen_width: int, taskbar_rect: wintypes.RECT):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        central = QWidget(self)
        central.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCentralWidget(central)

        geom = compute_overlay_geometry(taskbar_rect, screen_width)
        self.setGeometry(geom)

        # Exclude window from screenshots and screen share (Windows 10 2004+)
        hwnd = int(self.winId())
        ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_overlay_window.py -v
```

Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add overlay_window.py tests/test_overlay_window.py
git commit -m "feat: OverlayWindow with Win32 taskbar positioning"
```

---

## Task 9: `chat_popover.py` — chat UI

**Files:**
- Create: `chat_popover.py`
- Create: `tests/test_chat_popover.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_chat_popover.py`:

```python
import pytest
from PyQt6.QtCore import QPoint
from chat_popover import compute_popover_pos, POPOVER_WIDTH, POPOVER_HEIGHT, ChatPopover


def test_popover_anchors_above_character():
    pos = compute_popover_pos(QPoint(400, 900), 80, 1920)
    assert pos.y() == 900 - POPOVER_HEIGHT


def test_popover_aligns_with_character_x():
    pos = compute_popover_pos(QPoint(400, 900), 80, 1920)
    assert pos.x() == 400


def test_popover_shifts_left_near_right_edge():
    pos = compute_popover_pos(QPoint(1800, 900), 80, 1920)
    assert pos.x() == 1920 - POPOVER_WIDTH


def test_popover_clamps_to_left_edge():
    pos = compute_popover_pos(QPoint(-50, 900), 80, 1920)
    assert pos.x() == 0


def test_clear_command_clears_output(qtbot):
    popover = ChatPopover("claude")
    qtbot.addWidget(popover)
    popover._output.setPlainText("some text")
    popover._input.setText("/clear")
    popover._on_submit()
    assert popover._output.toPlainText() == ""


def test_help_command_shows_help(qtbot):
    popover = ChatPopover("claude")
    qtbot.addWidget(popover)
    popover._input.setText("/help")
    popover._on_submit()
    assert "Available commands" in popover._output.toPlainText()


def test_copy_command_puts_last_response_in_clipboard(qtbot):
    from PyQt6.QtWidgets import QApplication
    popover = ChatPopover("claude")
    qtbot.addWidget(popover)
    popover._last_response = "AI said hello"
    popover._input.setText("/copy")
    popover._on_submit()
    assert QApplication.clipboard().text() == "AI said hello"


def test_show_binary_not_found_displays_message(qtbot):
    popover = ChatPopover("claude")
    qtbot.addWidget(popover)
    popover.show_binary_not_found("claude")
    assert "claude" in popover._output.toPlainText()
    assert "PATH" in popover._output.toPlainText()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_chat_popover.py -v
```

Expected: `ModuleNotFoundError: No module named 'chat_popover'`

- [ ] **Step 3: Create `chat_popover.py`**

```python
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QComboBox, QLabel,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QTextCursor

POPOVER_WIDTH = 420
POPOVER_HEIGHT = 320

HELP_TEXT = """Available commands:
  /clear  — clear the output
  /copy   — copy last AI response to clipboard
  /help   — show this message"""

INSTALL_URLS = {
    "claude": "https://docs.anthropic.com/en/docs/claude-code",
    "gemini": "https://ai.google.dev/gemini-api/docs/gemini-cli",
}


def compute_popover_pos(
    char_screen_pos: QPoint, char_width: int, screen_width: int
) -> QPoint:
    """Return top-left corner for the popover, anchored above the character."""
    x = char_screen_pos.x()
    y = char_screen_pos.y() - POPOVER_HEIGHT
    if x + POPOVER_WIDTH > screen_width:
        x = screen_width - POPOVER_WIDTH
    x = max(0, x)
    return QPoint(x, y)


class ChatPopover(QDialog):
    closed = pyqtSignal()

    def __init__(self, provider: str, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.resize(POPOVER_WIDTH, POPOVER_HEIGHT)
        self._provider = provider
        self._session = None
        self._last_response = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        font = QFont("Consolas", 10)

        # Provider selector row
        header = QHBoxLayout()
        header.addWidget(QLabel("Provider:"))
        self._provider_combo = QComboBox()
        self._provider_combo.addItems(["claude", "gemini"])
        self._provider_combo.setCurrentText(self._provider)
        self._provider_combo.currentTextChanged.connect(self._on_provider_changed)
        header.addWidget(self._provider_combo)
        header.addStretch()
        layout.addLayout(header)

        # Output area
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setFont(font)
        layout.addWidget(self._output)

        # Input field
        self._input = QLineEdit()
        self._input.setFont(font)
        self._input.setPlaceholderText("Ask something... (/help for commands)")
        self._input.returnPressed.connect(self._on_submit)
        layout.addWidget(self._input)

    def _on_provider_changed(self, provider: str) -> None:
        from config import set_provider
        self._provider = provider
        set_provider(provider)

    def set_session(self, session) -> None:
        self._session = session
        self._session.output_received.connect(self._on_output)
        self._session.error_received.connect(self._on_error)

    def _on_submit(self) -> None:
        text = self._input.text().strip()
        self._input.clear()
        if not text:
            return
        if text == "/clear":
            self._output.clear()
            self._last_response = ""
            return
        if text == "/copy":
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(self._last_response)
            return
        if text == "/help":
            self._output.append(HELP_TEXT)
            return
        self._output.append(f"\n> {text}")
        self._last_response = ""
        if self._session:
            self._session.send(text)

    def _on_output(self, text: str) -> None:
        self._last_response += text
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self._output.setTextCursor(cursor)

    def _on_error(self, text: str) -> None:
        self._output.append(f"[error] {text}")

    def show_binary_not_found(self, provider: str) -> None:
        url = INSTALL_URLS.get(provider, "")
        self._output.append(
            f"Could not find '{provider}' on PATH.\n"
            f"Install it from: {url}"
        )

    def closeEvent(self, event) -> None:
        if self._session:
            self._session.stop()
        self.closed.emit()
        super().closeEvent(event)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_chat_popover.py -v
```

Expected: 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add chat_popover.py tests/test_chat_popover.py
git commit -m "feat: ChatPopover with terminal UI and slash commands"
```

---

## Task 10: `main.py` — wiring everything together

**Files:**
- Create: `main.py`

No unit tests for `main.py` — it is integration-only and verified by running the app.

- [ ] **Step 1: Create `main.py`**

```python
import shutil
import sys

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QPoint

from overlay_window import OverlayWindow, get_taskbar_rect
from walker_character import WalkerCharacter
from chat_popover import ChatPopover, compute_popover_pos
from claude_session import ClaudeSession
from gemini_session import GeminiSession
from config import get_provider
from utils import resource_path

SESSION_CLASSES = {
    "claude": ClaudeSession,
    "gemini": GeminiSession,
}


def _make_session(provider: str):
    cls = SESSION_CLASSES.get(provider, ClaudeSession)
    return cls()


def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    taskbar_rect = get_taskbar_rect()
    screen_width = app.primaryScreen().geometry().width()

    overlay = OverlayWindow(screen_width, taskbar_rect)
    container = overlay.centralWidget()

    bruce = WalkerCharacter(resource_path("assets/bruce.gif"), parent=container)
    jazz = WalkerCharacter(resource_path("assets/jazz.gif"), parent=container)
    bruce.resize(80, 80)
    jazz.resize(80, 80)
    bruce.move(100, 0)
    jazz.move(350, 0)
    bruce.show()
    jazz.show()

    def on_character_clicked(character: WalkerCharacter) -> None:
        character.pause()
        provider = get_provider()
        session = _make_session(provider)

        popover = ChatPopover(provider)
        popover.set_session(session)

        cli_name = "claude" if provider == "claude" else "gemini"
        if shutil.which(cli_name) is None:
            popover.show_binary_not_found(cli_name)

        char_global = character.mapToGlobal(QPoint(0, 0))
        pos = compute_popover_pos(char_global, character.width(), screen_width)
        popover.move(pos)
        popover.closed.connect(character.resume)
        popover.show()

    bruce.clicked.connect(on_character_clicked)
    jazz.clicked.connect(on_character_clicked)

    # System tray icon
    tray_icon = QIcon(resource_path("assets/icon.ico"))
    tray = QSystemTrayIcon(tray_icon, app)

    menu = QMenu()
    about_action = QAction("About Lil Agents")
    about_action.triggered.connect(
        lambda: QMessageBox.about(
            None,
            "Lil Agents",
            "Lil Agents v1.0\nAnimated AI companions for Windows.\n\nOriginal macOS app by Ryan Stephen.",
        )
    )
    quit_action = QAction("Quit")
    quit_action.triggered.connect(app.quit)
    menu.addAction(about_action)
    menu.addSeparator()
    menu.addAction(quit_action)
    tray.setContextMenu(menu)
    tray.show()

    overlay.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run a smoke test**

```bash
python main.py
```

Expected: two animated characters walk above the taskbar. Right-clicking the system tray shows About / Quit. Clicking a character opens the chat popover. No exceptions in the terminal.

- [ ] **Step 3: Run the full test suite to confirm nothing regressed**

```bash
pytest tests/ -v
```

Expected: all existing tests PASS.

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "feat: main entry point wiring overlay, characters, tray, and popover"
```

---

## Task 11: PyInstaller packaging

**Files:**
- Create: `lil_agents.spec`
- Create: `build.bat`

- [ ] **Step 1: Create `lil_agents.spec`**

```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[("assets", "assets")],
    hiddenimports=[
        "PyQt6.QtMultimedia",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="LilAgents",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon="assets/icon.ico",
)
```

- [ ] **Step 2: Create `build.bat`**

```bat
@echo off
echo Building LilAgents.exe ...
pyinstaller lil_agents.spec
echo.
echo Build complete: dist\LilAgents.exe
```

- [ ] **Step 3: Run the build**

```bash
build.bat
```

Expected: `dist/LilAgents.exe` is created with no fatal errors. Size will be ~60–100 MB.

- [ ] **Step 4: Test the bundled executable**

Double-click `dist\LilAgents.exe` (no Python required).

Expected: characters walk above the taskbar, system tray icon appears, chat popover works — identical behaviour to `python main.py`.

- [ ] **Step 5: Commit**

```bash
git add lil_agents.spec build.bat
git commit -m "feat: PyInstaller spec and build script for LilAgents.exe"
```

---

## Done

All tasks complete. Verify the final state:

```bash
pytest tests/ -v
```

Expected: all tests PASS, no failures.

`dist/LilAgents.exe` is a self-contained Windows executable that:
- Places Bruce and Jazz above the taskbar
- Streams responses from Claude Code or Google Gemini CLI
- Persists provider choice in `%APPDATA%\LilAgents\config.json`
- Excludes itself from screen capture
