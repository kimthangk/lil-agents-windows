import shutil
import sys

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QPoint

from overlay_window import OverlayWindow, get_taskbar_rect, OVERLAY_HEIGHT
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

    # Win32 SHAppBarMessage returns physical pixels; Qt uses logical pixels.
    # Divide by devicePixelRatio to get logical coordinates.
    dpi = app.primaryScreen().devicePixelRatio()
    taskbar_rect = get_taskbar_rect()
    taskbar_rect.left = int(taskbar_rect.left / dpi)
    taskbar_rect.top = int(taskbar_rect.top / dpi)
    taskbar_rect.right = int(taskbar_rect.right / dpi)
    taskbar_rect.bottom = int(taskbar_rect.bottom / dpi)
    screen_width = app.primaryScreen().geometry().width()

    overlay = OverlayWindow(screen_width, taskbar_rect)
    container = overlay.centralWidget()

    # Walk timing from original LilAgentsController.swift (per-character)
    bruce = WalkerCharacter(resource_path("assets/bruce.gif"), parent=container,
                            accel_start=3.0, full_speed_start=3.75, decel_start=8.0, walk_stop=8.5)
    jazz = WalkerCharacter(resource_path("assets/jazz.gif"), parent=container,
                           accel_start=3.9, full_speed_start=4.5, decel_start=8.0, walk_stop=8.75)
    bruce.move(100, OVERLAY_HEIGHT - bruce.height())
    jazz.move(350, OVERLAY_HEIGHT - jazz.height())
    bruce.show()
    jazz.show()

    active_popovers: list = []

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

        def _on_closed():
            character.resume()
            active_popovers.remove(popover)

        popover.closed.connect(_on_closed)
        active_popovers.append(popover)
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
    tray.setToolTip("Lil Agents — right-click to quit")
    tray.show()

    overlay.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
