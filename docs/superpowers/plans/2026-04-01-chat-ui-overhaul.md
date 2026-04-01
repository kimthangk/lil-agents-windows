# Chat UI Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the chat popover and character feedback up to parity with the original macOS lil-agents — polished character-specific UI, markdown rendering, and a thinking bubble above each character while waiting for a response.

**Architecture:** `chat_popover.py` is fully rewritten to accept character name/accent color, render streamed text into markdown HTML on finish, and show a blinking cursor during streaming. `walker_character.py` gains a `ThinkingBubble` widget and `show_thinking()` / `hide_thinking()` methods on `WalkerCharacter`. `main.py` wires the two together by passing name/color into the popover and calling show/hide thinking on session events.

**Tech Stack:** PyQt6, Python `markdown` library (fenced_code + nl2br extensions)

---

## File Map

| File | Change |
|------|--------|
| `requirements.txt` | Add `markdown>=3.5` |
| `chat_popover.py` | Full rewrite — character name/color params, markdown rendering, streaming cursor, accent header |
| `walker_character.py` | Add `ThinkingBubble` class + `show_thinking()` / `hide_thinking()` on `WalkerCharacter` |
| `main.py` | Pass `name` and `accent_color` to `ChatPopover`; call `character.show_thinking()` / `hide_thinking()` on session events |

---

## Task 1: Add markdown dependency

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add `markdown>=3.5` to requirements.txt**

Replace the file contents with:

```
PyQt6>=6.6.0
PyQt6-Qt6>=6.6.0
markdown>=3.5
```

- [ ] **Step 2: Install the dependency**

Run:
```bash
pip install markdown>=3.5
```

Expected: `Successfully installed markdown-X.X.X` or `Requirement already satisfied`.

- [ ] **Step 3: Verify import works**

Run:
```bash
python -c "import markdown; print(markdown.markdown('**hello**', extensions=['fenced_code','nl2br']))"
```

Expected output:
```
<p><strong>hello</strong></p>
```

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: add markdown>=3.5 dependency"
```

---

## Task 2: Rewrite chat_popover.py

**Files:**
- Modify: `chat_popover.py` (full rewrite)

This task replaces the entire file. The new popover:
- Accepts `name: str` and `accent_color: str` constructor params
- Shows an accent-colored dot + character name in the header (replacing "Lil Agents" title)
- Applies accent color to input focus border and inline code backgrounds via CSS
- Streams raw text with a `▋` cursor appended; cursor removed on each new chunk
- On `finished`: replaces the streamed raw block with markdown-rendered HTML

- [ ] **Step 1: Write the new chat_popover.py**

Replace the entire file with:

```python
import markdown as _md

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, QLineEdit,
    QComboBox, QLabel, QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QTextCursor, QColor, QTextCharFormat

POPOVER_WIDTH = 460
POPOVER_HEIGHT = 400

HELP_TEXT = """Commands:
  /clear  — clear the conversation
  /copy   — copy last response to clipboard
  /help   — show this message"""

INSTALL_URLS = {
    "claude": "https://docs.anthropic.com/en/docs/claude-code",
    "gemini": "https://ai.google.dev/gemini-api/docs/gemini-cli",
}

_BASE_STYLE = """
QDialog {{
    background: #1e1e2e;
    border: 1px solid #45475a;
    border-radius: 10px;
}}
QTextEdit {{
    background: #181825;
    color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 6px;
    selection-background-color: #45475a;
}}
QLineEdit {{
    background: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 10px;
}}
QLineEdit:focus {{
    border: 1px solid {accent};
}}
QComboBox {{
    background: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 2px 8px;
}}
QComboBox QAbstractItemView {{
    background: #313244;
    color: #cdd6f4;
    selection-background-color: #45475a;
}}
QLabel {{
    color: #a6adc8;
}}
QPushButton {{
    background: transparent;
    color: #6c7086;
    border: none;
    border-radius: 4px;
    font-size: 16px;
}}
QPushButton:hover {{
    background: #313244;
    color: #cdd6f4;
}}
"""

_DOC_CSS = """
code {{ font-family: Consolas, monospace; background: {code_bg}; padding: 1px 4px; border-radius: 2px; }}
pre  {{ background: #181825; padding: 8px; margin: 4px 0; border-radius: 4px; }}
h1, h2, h3 {{ color: #cdd6f4; margin: 4px 0; }}
p    {{ margin: 2px 0; }}
ul, ol {{ margin: 2px 0; padding-left: 16px; }}
"""

_STREAM_CURSOR = "\u2587"  # ▋


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert #rrggbb + alpha float to CSS rgba() string."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def compute_popover_pos(
    char_screen_pos: QPoint, char_width: int, screen_width: int
) -> QPoint:
    x = char_screen_pos.x() + char_width // 2 - POPOVER_WIDTH // 2
    y = char_screen_pos.y() - POPOVER_HEIGHT - 8
    if x + POPOVER_WIDTH > screen_width:
        x = screen_width - POPOVER_WIDTH - 8
    x = max(8, x)
    return QPoint(x, y)


class ChatPopover(QDialog):
    closed = pyqtSignal()

    def __init__(self, name: str, accent_color: str, provider: str, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(POPOVER_WIDTH, POPOVER_HEIGHT)
        self._name = name
        self._accent = accent_color
        self._provider = provider
        self._session = None
        self._last_response = ""
        self._raw_response = ""
        self._response_start_pos = 0
        self._is_receiving = False
        self._setup_ui()
        self.setStyleSheet(_BASE_STYLE.format(accent=accent_color))

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(8)
        mono = QFont("Consolas", 10)

        # Header
        header_wrap = QWidget()
        header_wrap.setStyleSheet(
            f"background: transparent; border-left: 3px solid {self._accent}; padding-left: 4px;"
        )
        header = QHBoxLayout(header_wrap)
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        dot = QLabel("\u25cf")  # ●
        dot.setStyleSheet(f"color: {self._accent}; font-size: 10px; border: none;")
        header.addWidget(dot)

        title = QLabel(self._name)
        title.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 13px; border: none;")
        header.addWidget(title)
        header.addStretch()

        self._provider_combo = QComboBox()
        self._provider_combo.addItems(["claude", "gemini"])
        self._provider_combo.setCurrentText(self._provider)
        self._provider_combo.setFixedWidth(90)
        self._provider_combo.currentTextChanged.connect(self._on_provider_changed)
        header.addWidget(self._provider_combo)

        close_btn = QPushButton("\u2715")  # ✕
        close_btn.setFixedSize(26, 26)
        close_btn.setToolTip("Close (Esc)")
        close_btn.setDefault(False)
        close_btn.setAutoDefault(False)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addWidget(header_wrap)

        # Output
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setFont(mono)
        self._output.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        code_bg = _hex_to_rgba(self._accent, 0.18)
        self._output.document().setDefaultStyleSheet(_DOC_CSS.format(code_bg=code_bg))
        layout.addWidget(self._output)

        # Status label
        self._status = QLabel("")
        self._status.setStyleSheet("color: #6c7086; font-size: 10px; padding-left: 2px;")
        layout.addWidget(self._status)

        # Input
        self._input = QLineEdit()
        self._input.setFont(mono)
        self._input.setPlaceholderText("Message... (/help for commands)")
        self._input.returnPressed.connect(self._on_submit)
        layout.addWidget(self._input)

        self._input.setFocus()

    def _on_provider_changed(self, provider: str) -> None:
        from config import set_provider
        self._provider = provider
        set_provider(provider)

    def set_session(self, session) -> None:
        self._session = session
        qt = Qt.ConnectionType.QueuedConnection
        self._session.output_received.connect(self._on_output, qt)
        self._session.error_received.connect(self._on_error, qt)
        self._session.finished.connect(self._on_finished, qt)

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
            self._status.setText("Copied!")
            return
        if text == "/help":
            self._output.append(HELP_TEXT)
            return

        # Show user message
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if self._output.toPlainText():
            cursor.insertText("\n")
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#89b4fa"))
        cursor.insertText(f"You: {text}\n", fmt)
        self._output.setTextCursor(cursor)
        self._output.ensureCursorVisible()

        self._last_response = ""
        self._raw_response = ""
        self._response_start_pos = 0
        self._is_receiving = False
        self._status.setText("Thinking...")
        self._input.setEnabled(False)
        if self._session:
            self._session.send(text)

    def _on_output(self, text: str) -> None:
        self._raw_response += text
        cursor = self._output.textCursor()

        if not self._is_receiving:
            # First chunk: insert character name label and record start position
            self._is_receiving = True
            self._status.setText("")
            cursor.movePosition(QTextCursor.MoveOperation.End)
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(self._accent))
            cursor.insertText(f"{self._name}: ", fmt)
            self._response_start_pos = cursor.position()

        # Replace everything from response start to end with raw text + cursor
        cursor.setPosition(self._response_start_pos)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#cdd6f4"))
        cursor.insertText(self._raw_response + _STREAM_CURSOR, fmt)
        self._output.setTextCursor(cursor)
        self._output.ensureCursorVisible()

    def _on_error(self, text: str) -> None:
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#f38ba8"))
        cursor.insertText(f"[error] {text}", fmt)
        self._output.setTextCursor(cursor)

    def _on_finished(self) -> None:
        if self._is_receiving and self._raw_response:
            # Replace the streamed raw block with rendered HTML
            html = _md.markdown(
                self._raw_response,
                extensions=["fenced_code", "nl2br"],
            )
            cursor = self._output.textCursor()
            cursor.setPosition(self._response_start_pos)
            cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
            cursor.insertHtml(html)
            self._last_response = self._raw_response

            # Add spacing after response
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText("\n")
            self._output.setTextCursor(cursor)

        self._is_receiving = False
        self._status.setText("")
        self._input.setEnabled(True)
        self._input.setFocus()

    def show_binary_not_found(self, provider: str) -> None:
        url = INSTALL_URLS.get(provider, "")
        self._output.append(f"Could not find '{provider}' on PATH.\nInstall: {url}")

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        if self._session:
            self._session.stop()
        self.closed.emit()
        super().closeEvent(event)
```

- [ ] **Step 2: Verify the app runs without errors**

Run:
```bash
python main.py
```

Expected: app launches (will crash because main.py still passes old args — that's expected here; fix comes in Task 4). For now, confirm the import is clean:

```bash
python -c "from chat_popover import ChatPopover, compute_popover_pos; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add chat_popover.py
git commit -m "feat: rewrite ChatPopover with markdown rendering and accent colors"
```

---

## Task 3: Add ThinkingBubble to walker_character.py

**Files:**
- Modify: `walker_character.py`

Add a `ThinkingBubble` widget class and `show_thinking()` / `hide_thinking()` methods to `WalkerCharacter`. The bubble:
- Is a pill-shaped `QWidget` child of the overlay container (same parent as the character)
- Shows rotating phrases from a fixed list, every 3–5 seconds via `QTimer`
- Is suppressed (not shown) when the popover is open — tracked via `_popover_open` flag
- Shows `"done!"` for 2 seconds on `hide_thinking(done=True)` if popover is not open

- [ ] **Step 1: Add ThinkingBubble class and update WalkerCharacter**

Open `walker_character.py`. Make the following additions (do NOT remove any existing code):

**A. Add new imports at the top** (extend the existing import block):

```python
import random

from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QMovie, QTransform, QFont
```

**B. Add the phrase list constant** (after the existing constants, before `_movement_norm`):

```python
_THINKING_PHRASES = [
    "hmm...", "thinking...", "one sec...", "ok hold on", "let me check",
    "working on it", "almost...", "bear with me", "on it!", "gimme a sec",
    "brb", "processing...", "hang tight", "just a moment", "figuring it out",
    "crunching...", "reading...", "looking...", "cooking...", "vibing...",
    "digging in", "connecting dots", "give me a sec", "don't rush me",
    "calculating...", "assembling...",
]
```

**C. Add the ThinkingBubble class** (after `_movement_norm`, before `class WalkerCharacter`):

```python
class ThinkingBubble(QWidget):
    def __init__(self, character: "WalkerCharacter", accent_color: str, parent=None):
        super().__init__(parent)
        self._character = character
        self._accent = accent_color

        self.setStyleSheet(
            f"background: #1e1e2e; border: 1.5px solid {accent_color}; border-radius: 10px;"
        )
        self.setMinimumWidth(60)
        self.setFixedHeight(24)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        self._label = QLabel()
        self._label.setFont(QFont("Consolas", 9))
        self._label.setStyleSheet(f"color: {accent_color}; border: none; background: transparent;")
        layout.addWidget(self._label)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._rotate_phrase)
        self.hide()

    def _rotate_phrase(self) -> None:
        self._label.setText(random.choice(_THINKING_PHRASES))
        self.adjustSize()
        self._reposition()
        self._timer.start(random.randint(3000, 5000))

    def _reposition(self) -> None:
        char = self._character
        cx = char.x() + char.width() // 2
        cy = char.y()
        self.move(cx - self.width() // 2, cy - self.height() - 6)

    def start(self) -> None:
        self._rotate_phrase()
        self.show()
        self.raise_()

    def stop(self, done: bool = False) -> None:
        self._timer.stop()
        if done:
            self._label.setText("done!")
            self.adjustSize()
            self._reposition()
            self.show()
            self.raise_()
            QTimer.singleShot(2000, self.hide)
        else:
            self.hide()
```

**D. Update `WalkerCharacter.__init__`** — add `accent_color` param and create the bubble.

Change the constructor signature from:
```python
    def __init__(self, gif_path: str, parent=None,
                 accel_start: float = 3.0, full_speed_start: float = 3.75,
                 decel_start: float = 8.0, walk_stop: float = 8.5):
```
to:
```python
    def __init__(self, gif_path: str, parent=None,
                 accel_start: float = 3.0, full_speed_start: float = 3.75,
                 decel_start: float = 8.0, walk_stop: float = 8.5,
                 accent_color: str = "#a6e3a1"):
```

And add these two lines at the end of `__init__` (before the closing of the method, after `self._pause_timer.start(delay_ms)`):

```python
        self._popover_open = False
        self._bubble = ThinkingBubble(self, accent_color, parent)
```

**E. Add the public API methods** to `WalkerCharacter` (after the existing `mousePressEvent` method):

```python
    def show_thinking(self) -> None:
        """Start thinking state. Bubble only shown if popover is not open."""
        if not self._popover_open:
            self._bubble.start()

    def hide_thinking(self, done: bool = False) -> None:
        """Stop thinking state. If done=True and popover not open, show 'done!' briefly."""
        self._bubble.stop(done=done and not self._popover_open)

    def set_popover_open(self, open: bool) -> None:
        """Track whether the chat popover is open (suppresses the thinking bubble)."""
        self._popover_open = open
        if open:
            self._bubble.stop(done=False)
```

- [ ] **Step 2: Verify import is clean**

```bash
python -c "from walker_character import WalkerCharacter, ThinkingBubble; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add walker_character.py
git commit -m "feat: add ThinkingBubble widget and show/hide_thinking to WalkerCharacter"
```

---

## Task 4: Wire main.py

**Files:**
- Modify: `main.py`

Three changes:
1. Pass `name` and `accent_color` to `ChatPopover` (new constructor params)
2. Call `character.set_popover_open(True/False)` when popover opens/closes
3. Connect `session.finished` to `character.hide_thinking(done=True)`, and call `character.show_thinking()` when `_on_submit` fires (via a signal or direct wiring)

For the thinking signal, the cleanest approach without modifying ChatPopover further: connect `session.output_received` to trigger `hide_thinking` setup, and connect before the session is created. The simplest wiring: connect `session.finished` to `character.hide_thinking` in `on_character_clicked`, and patch `ChatPopover._on_submit` to emit a signal.

Since `ChatPopover` already calls `self._session.send(text)` in `_on_submit`, the cleanest approach is to connect directly to the session after creation: we can't intercept `_on_submit` from outside easily. Instead, we'll have `on_character_clicked` store a reference to `session` and connect `session.finished` to `character.hide_thinking`. For `show_thinking`, we'll subclass or monkeypatch — but the simplest approach is: have the popover emit a signal. However, to avoid changing the popover spec, use a `QueuedConnection` from main.py by wrapping the session's `send` via a proxy.

The pragmatic solution: add one signal `thinking_started = pyqtSignal()` to `ChatPopover` (emitted in `_on_submit` after `self._session.send(text)` is called). Wire it in main.py.

- [ ] **Step 1: Add `thinking_started` signal to ChatPopover**

In `chat_popover.py`, in the `ChatPopover` class body, add the signal next to `closed`:

```python
class ChatPopover(QDialog):
    closed = pyqtSignal()
    thinking_started = pyqtSignal()
```

And in `_on_submit`, after the line `self._session.send(text)`, add:

```python
            self._session.send(text)
            self.thinking_started.emit()
```

- [ ] **Step 2: Update main.py**

Replace the `on_character_clicked` function with:

```python
    CHARACTER_INFO = {
        bruce: ("Bruce", "#a6e3a1"),
        jazz:  ("Jazz",  "#fab387"),
    }

    def on_character_clicked(character: WalkerCharacter) -> None:
        character.pause()
        name, accent_color = CHARACTER_INFO[character]
        provider = get_provider()
        session = _make_session(provider)

        popover = ChatPopover(name, accent_color, provider)
        popover.set_session(session)

        cli_name = "claude" if provider == "claude" else "gemini"
        if shutil.which(cli_name) is None:
            popover.show_binary_not_found(cli_name)

        char_global = character.mapToGlobal(QPoint(0, 0))
        pos = compute_popover_pos(char_global, character.width(), screen_width)
        popover.move(pos)

        character.set_popover_open(True)

        qt = Qt.ConnectionType.QueuedConnection
        popover.thinking_started.connect(character.show_thinking, qt)
        session.finished.connect(lambda: character.hide_thinking(done=True), qt)

        def _on_closed():
            character.set_popover_open(False)
            character.resume()
            active_popovers.remove(popover)

        popover.closed.connect(_on_closed)
        active_popovers.append(popover)
        popover.show()
```

Also update the `WalkerCharacter` construction calls to pass `accent_color`:

```python
    bruce = WalkerCharacter(resource_path("assets/bruce.gif"), parent=container,
                            accel_start=3.0, full_speed_start=3.75, decel_start=8.0, walk_stop=8.5,
                            accent_color="#a6e3a1")
    jazz = WalkerCharacter(resource_path("assets/jazz.gif"), parent=container,
                           accel_start=3.9, full_speed_start=4.5, decel_start=8.0, walk_stop=8.75,
                           accent_color="#fab387")
```

And add `Qt` to the main.py imports (it's needed for `Qt.ConnectionType.QueuedConnection`):

```python
from PyQt6.QtCore import QPoint, Qt
```

- [ ] **Step 3: Run the app and verify visually**

```bash
python main.py
```

Checklist:
- [ ] Bruce and Jazz appear above the taskbar as before
- [ ] Click Bruce → popover opens with "Bruce" in header, green accent dot, green input focus border
- [ ] Click Jazz → popover opens with "Jazz" in header, orange accent dot, orange input focus border
- [ ] Send a message → status shows "Thinking...", input disabled
- [ ] Response streams with `▋` cursor at the end
- [ ] Response finishes → raw text replaced with rendered markdown HTML, input re-enabled
- [ ] `**bold**` renders bold, `` `code` `` renders with tinted background
- [ ] Close popover while waiting → "done!" bubble appears above character for 2s
- [ ] Thinking bubble does NOT appear while popover is open

- [ ] **Step 4: Commit**

```bash
git add chat_popover.py main.py walker_character.py
git commit -m "feat: wire accent colors, markdown popover, and thinking bubble in main"
```

---

## Task 5: Rebuild .exe and push to GitHub

**Files:**
- No source changes — build and release only

- [ ] **Step 1: Rebuild the executable**

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
python -m PyInstaller lil_agents.spec
```

Expected: `dist/LilAgents.exe` is generated without errors.

- [ ] **Step 2: Smoke-test the .exe**

Double-click `dist/LilAgents.exe`. Verify:
- Characters appear above taskbar
- Click a character → styled popover opens (accent color, character name)
- Send a message → markdown renders on completion

- [ ] **Step 3: Tag the release and push**

```bash
git tag v1.1.0
git push origin main --tags
```

- [ ] **Step 4: Create GitHub release with the new .exe**

```bash
gh release create v1.1.0 dist/LilAgents.exe \
  --title "v1.1.0 — Markdown chat & thinking bubble" \
  --notes "## What's new
- Character-specific accent colors (Bruce: green, Jazz: orange)
- Markdown rendering in chat — bold, italic, code blocks, headings, lists
- Streaming cursor (▋) while response is arriving
- Thinking bubble above character while waiting for a response
- Improved chat header with character name and accent dot"
```
