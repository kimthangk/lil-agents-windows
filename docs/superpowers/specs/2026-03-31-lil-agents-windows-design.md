# Lil Agents — Windows Port Design

**Date:** 2026-03-31
**Source repo:** https://github.com/ryanstephen/lil-agents
**Status:** Approved

---

## Overview

A Windows port of lil-agents: animated AI companion characters that live above the Windows taskbar. Users click a character to open a terminal-style chat popover connected to a locally-installed AI CLI (Claude Code or Google Gemini). The app is distributed as a single `.exe` built with PyInstaller.

---

## Tech Stack

| Concern | Choice |
|---|---|
| Language | Python 3.11+ |
| UI framework | PyQt6 |
| Animation | QMovie (animated GIF) |
| AI CLI integration | QProcess (subprocess streaming) |
| Taskbar positioning | ctypes / Win32 `SHAppBarMessage` |
| Packaging | PyInstaller (onefile, windowed) |

---

## Architecture

```
lil-agents-windows/
├── main.py                  # Entry point: QApplication, OverlayWindow, system tray
├── overlay_window.py        # Transparent frameless always-on-top window above taskbar
├── walker_character.py      # GIF animation + walking logic for one character
├── chat_popover.py          # Terminal-style QDialog for AI conversation
├── agent_session.py         # Base class: QProcess lifecycle, output streaming
├── claude_session.py        # Spawns `claude -p <input>`, streams stdout
├── gemini_session.py        # Spawns `gemini <input>`, streams stdout
├── assets/
│   ├── bruce.gif            # Converted from walk-bruce-01.mov (ffmpeg)
│   ├── jazz.gif             # Converted from walk-jazz-01.mov (ffmpeg)
│   └── icon.ico             # Converted from menuicon.png
├── tools/
│   └── convert_assets.py   # One-time ffmpeg helper to produce GIFs and .ico
├── config.py                # config.json read/write helpers (%APPDATA%\LilAgents\)
├── lil_agents.spec          # PyInstaller build spec
└── build.bat                # Single-command build: runs pyinstaller lil_agents.spec
```

Each component has one clear responsibility and communicates through well-defined interfaces (Qt signals or direct method calls). No shared mutable state between the two character instances.

---

## Component Details

### `main.py`
- Detects taskbar geometry via `ctypes` at startup
- Instantiates `OverlayWindow` with two `WalkerCharacter` instances (Bruce and Jazz), staggered start positions
- Creates a `QSystemTrayIcon` with a right-click menu: **About**, **Quit**
- Enters `QApplication.exec()`

### `overlay_window.py` — `OverlayWindow(QMainWindow)`
- Flags: `Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool`
  (`Qt.Tool` keeps it out of the Alt+Tab / taskbar app list)
- Background: `rgba(0, 0, 0, 0)` — fully transparent
- Positioned flush against the top edge of the taskbar, full screen width
- Uses `SHAppBarMessage(ABM_GETTASKBARPOS)` to handle taskbar on any screen edge and any DPI scale
- Registers a `QAbstractNativeEventFilter` for `WM_DPICHANGED` to re-position on display scale changes
- Calls `SetWindowDisplayAffinity(DWMWA_EXCLUDE_FROM_CAPTURE)` to exclude from screenshots and screen share

### `walker_character.py` — `WalkerCharacter(QLabel)`
- Plays its `.gif` via `QMovie`
- A `QTimer` (~16ms) increments `x` position; reverses direction at screen edges
- On direction reversal, applies `QTransform().scale(-1, 1)` to flip the animation
- `mousePressEvent`: pauses walking, emits `clicked` signal
- Public `resume()` slot: resumes walking after popover closes
- Two instances walk independently; no collision detection (they pass through each other)

### `chat_popover.py` — `ChatPopover(QDialog)`
- Frameless `QDialog` anchored above the clicked character's current position
- Layout: scrollable `QTextEdit` (output, read-only, monospace font) + `QLineEdit` (input)
- Provider selector (Claude / Gemini) shown on first open; selection saved to `config.json`
- Slash commands: `/clear`, `/copy` (copies last AI response), `/help`
- On submit: passes input to the active `AgentSession`; streams response chunks into the output area via `QProcess.readyReadStandardOutput`
- If CLI binary not found on `PATH`: shows inline error with install URL instead of crashing
- On close: emits `closed` signal → `WalkerCharacter.resume()`

### `agent_session.py` — `AgentSession`
- Base class owning a `QProcess` instance
- `send(text: str)`: starts the process with the correct args, connects stdout/stderr signals
- `output_received = pyqtSignal(str)`: emits decoded stdout chunks
- `error_received = pyqtSignal(str)`: emits stderr chunks
- Kills the process on `ChatPopover` close if still running

### `claude_session.py` — `ClaudeSession(AgentSession)`
```python
process.start("claude", ["-p", user_input])
```

### `gemini_session.py` — `GeminiSession(AgentSession)`
```python
process.start("gemini", [user_input])
```

### `config.py`
- Reads/writes `%APPDATA%\LilAgents\config.json`
- Persists: selected AI provider
- Creates the directory on first run if it doesn't exist

---

## Asset Conversion

The original `.mov` files must be converted once before building. `tools/convert_assets.py` runs:

```bash
ffmpeg -i walk-bruce-01.mov -vf "fps=15,scale=80:-1:flags=lanczos" bruce.gif
ffmpeg -i walk-jazz-01.mov  -vf "fps=15,scale=80:-1:flags=lanczos" jazz.gif
```

The `icon.ico` is produced by the same script using Pillow:
```python
from PIL import Image
Image.open("menuicon.png").save("assets/icon.ico", format="ICO", sizes=[(32,32),(16,16)])
```

`ffmpeg` and Pillow must be available to run the conversion. The converted GIFs and `.ico` are committed to the repo so end users don't need either tool.

---

## Packaging

`lil_agents.spec` configures PyInstaller:
- `--onefile` — single `.exe`
- `--windowed` — no console window
- `--icon=assets/icon.ico`
- `datas=[("assets", "assets")]` — bundles GIFs and icon

A `resource_path(relative)` helper in `main.py` resolves asset paths correctly in both dev mode and the bundled `.exe` (handles PyInstaller's `sys._MEIPASS` temp dir).

`build.bat` runs:
```bat
pyinstaller lil_agents.spec
```
Output: `dist/LilAgents.exe`

---

## Privacy & Security

- No network calls made by the app itself
- All AI conversation goes through the user's locally-installed CLI; the app only spawns a subprocess
- Window excluded from screen capture via `SetWindowDisplayAffinity`
- No telemetry, no auto-update mechanism in v1

---

## Out of Scope (v1)

- Auto-update (Sparkle equivalent)
- Sound effects
- Additional AI providers (Codex, Copilot)
- Custom themes / color schemes
- Installer wizard / registry entries

---

## Success Criteria

- Two animated characters walk above the Windows taskbar and remain visible when other windows are open
- Clicking a character opens a chat popover; the user can send messages and see streamed responses from Claude Code or Gemini CLI
- The app runs as a single `LilAgents.exe` with no Python installation required
- Works on Windows 10 and Windows 11 at standard and high DPI scales
