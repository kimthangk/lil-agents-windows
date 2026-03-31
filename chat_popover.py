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
