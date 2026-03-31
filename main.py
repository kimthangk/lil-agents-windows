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
