from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QComboBox, QLabel,
    QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QTextCursor, QColor, QTextCharFormat

POPOVER_WIDTH = 460
POPOVER_HEIGHT = 380

HELP_TEXT = """Commands:
  /clear  — clear the conversation
  /copy   — copy last response to clipboard
  /help   — show this message"""

INSTALL_URLS = {
    "claude": "https://docs.anthropic.com/en/docs/claude-code",
    "gemini": "https://ai.google.dev/gemini-api/docs/gemini-cli",
}

STYLE = """
QDialog {
    background: #1e1e2e;
    border: 1px solid #45475a;
    border-radius: 10px;
}
QTextEdit {
    background: #181825;
    color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 6px;
    selection-background-color: #45475a;
}
QLineEdit {
    background: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 10px;
}
QLineEdit:focus {
    border: 1px solid #89b4fa;
}
QComboBox {
    background: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 2px 8px;
}
QComboBox QAbstractItemView {
    background: #313244;
    color: #cdd6f4;
    selection-background-color: #45475a;
}
QLabel {
    color: #a6adc8;
}
QPushButton {
    background: transparent;
    color: #6c7086;
    border: none;
    border-radius: 4px;
    font-size: 16px;
}
QPushButton:hover {
    background: #313244;
    color: #cdd6f4;
}
"""


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

    def __init__(self, provider: str, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(POPOVER_WIDTH, POPOVER_HEIGHT)
        self._provider = provider
        self._session = None
        self._last_response = ""
        self._is_receiving = False
        self._setup_ui()
        self.setStyleSheet(STYLE)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(8)
        mono = QFont("Consolas", 10)

        # Header
        header = QHBoxLayout()
        header.setSpacing(6)
        title = QLabel("Lil Agents")
        title.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 13px;")
        header.addWidget(title)
        header.addStretch()
        self._provider_combo = QComboBox()
        self._provider_combo.addItems(["claude", "gemini"])
        self._provider_combo.setCurrentText(self._provider)
        self._provider_combo.setFixedWidth(90)
        self._provider_combo.currentTextChanged.connect(self._on_provider_changed)
        header.addWidget(self._provider_combo)
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(26, 26)
        close_btn.setToolTip("Close (Esc)")
        close_btn.setDefault(False)
        close_btn.setAutoDefault(False)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        # Output
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setFont(mono)
        self._output.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        layout.addWidget(self._output)

        # Status label (thinking indicator)
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

        # Show user message in blue
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if not self._output.toPlainText() == "":
            cursor.insertText("\n")
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#89b4fa"))
        cursor.insertText(f"You: {text}\n", fmt)
        self._output.setTextCursor(cursor)
        self._output.ensureCursorVisible()

        self._last_response = ""
        self._is_receiving = False
        self._status.setText("Thinking...")
        self._input.setEnabled(False)
        if self._session:
            self._session.send(text)

    def _on_output(self, text: str) -> None:
        self._last_response += text
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if not self._is_receiving:
            self._is_receiving = True
            self._status.setText("")
            fmt = QTextCharFormat()
            fmt.setForeground(QColor("#a6e3a1"))
            cursor.insertText("Claude: ", fmt)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#cdd6f4"))
        cursor.insertText(text, fmt)
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
        self._is_receiving = False
        self._status.setText("")
        self._input.setEnabled(True)
        self._input.setFocus()
        # Add spacing after response
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText("\n")
        self._output.setTextCursor(cursor)

    def show_binary_not_found(self, provider: str) -> None:
        url = INSTALL_URLS.get(provider, "")
        self._output.append(
            f"Could not find '{provider}' on PATH.\nInstall: {url}"
        )

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
