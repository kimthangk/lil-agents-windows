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
    thinking_started = pyqtSignal()

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
            self.thinking_started.emit()

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
