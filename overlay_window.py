import ctypes
from ctypes import wintypes

from PyQt6.QtWidgets import QMainWindow, QWidget
from PyQt6.QtCore import Qt, QRect

OVERLAY_HEIGHT = 150  # px — tall enough for 80x142 character GIFs
ABM_GETTASKBARPOS = 0x00000005
WDA_EXCLUDEFROMCAPTURE = 0x00000011

# Windows 11 DWM border color constants
_DWMWA_BORDER_COLOR = 34
_DWMWA_COLOR_NONE = 0xFFFFFFFE  # tells DWM to draw no border


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

        hwnd = int(self.winId())

        # Exclude window from screenshots and screen share (Windows 10 2004+)
        ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)

    def showEvent(self, event):
        super().showEvent(event)
        # Remove the DWM border outline — must run after the window is shown
        # so DWM has fully composed the window. DWMWA_BORDER_COLOR = 34 with
        # DWMWA_COLOR_NONE (0xFFFFFFFE) is the Windows 11 API for this.
        hwnd = int(self.winId())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, _DWMWA_BORDER_COLOR,
            ctypes.byref(ctypes.c_int(_DWMWA_COLOR_NONE)),
            ctypes.sizeof(ctypes.c_int),
        )
