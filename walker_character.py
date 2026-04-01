import random

from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QMovie, QTransform, QFont

# GIF properties (15 fps, 151 frames ≈ 10 s — matches original .mov)
GIF_FPS = 15.0

# Distance to walk per trip (pixels)
WALK_MIN_PX = 125
WALK_MAX_PX = 250

# Pause between walks (seconds)
PAUSE_MIN = 5.0
PAUSE_MAX = 12.0

_THINKING_PHRASES = [
    "hmm...", "thinking...", "one sec...", "ok hold on", "let me check",
    "working on it", "almost...", "bear with me", "on it!", "gimme a sec",
    "brb", "processing...", "hang tight", "just a moment", "figuring it out",
    "crunching...", "reading...", "looking...", "cooking...", "vibing...",
    "digging in", "connecting dots", "give me a sec", "don't rush me",
    "calculating...", "assembling...",
]


def _movement_norm(video_time: float, accel_start: float, full_speed_start: float,
                   decel_start: float, walk_stop: float) -> float:
    """0→1 normalised progress through a walk at the given video timestamp."""
    d_in  = full_speed_start - accel_start
    d_lin = decel_start - full_speed_start
    d_out = walk_stop - decel_start
    v = 1.0 / (d_in / 2.0 + d_lin + d_out / 2.0)

    if video_time <= accel_start:
        return 0.0
    elif video_time <= full_speed_start:
        t = video_time - accel_start
        return v * t * t / (2.0 * d_in)
    elif video_time <= decel_start:
        t = video_time - full_speed_start
        return v * d_in / 2.0 + v * t
    elif video_time <= walk_stop:
        t = video_time - decel_start
        return v * d_in / 2.0 + v * d_lin + v * (t - t * t / (2.0 * d_out))
    else:
        return 1.0


class ThinkingBubble(QWidget):
    def __init__(self, character: "WalkerCharacter", accent_color: str, parent=None):
        super().__init__(parent)
        self._character = character

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
        # Position is updated each time a phrase rotates. The character must
        # be paused while the bubble is visible to avoid positional drift.
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


class WalkerCharacter(QLabel):
    clicked = pyqtSignal(object)

    def __init__(self, gif_path: str, parent=None,
                 accel_start: float = 3.0, full_speed_start: float = 3.75,
                 decel_start: float = 8.0, walk_stop: float = 8.5,
                 accent_color: str = "#a6e3a1"):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._accel_start = accel_start
        self._full_speed_start = full_speed_start
        self._decel_start = decel_start
        self._walk_stop = walk_stop

        self._direction = 1       # 1 = right, -1 = left
        self._is_walking = False
        self._walk_start_x = 0.0
        self._walk_end_x = 0.0

        self._movie = QMovie(gif_path)
        self._movie.setCacheMode(QMovie.CacheMode.CacheAll)
        self._movie.jumpToFrame(0)
        pix = self._movie.currentPixmap()
        if not pix.isNull():
            self.setPixmap(pix)
            self.adjustSize()
        self._last_frame_num = -1
        self._movie.frameChanged.connect(self._on_frame_changed)

        # Start paused; pause timer fires to begin first walk
        self._movie.start()
        self._movie.setPaused(True)

        self._pause_timer = QTimer(self)
        self._pause_timer.setSingleShot(True)
        self._pause_timer.timeout.connect(self._start_walk)
        delay_ms = int(random.uniform(1000, 3000))
        self._pause_timer.start(delay_ms)
        self._popover_open = False
        self._bubble = ThinkingBubble(self, accent_color, parent)

    # ------------------------------------------------------------------
    # Frame-driven update — single source of truth for both visuals + position
    # ------------------------------------------------------------------

    def _on_frame_changed(self, frame_num: int) -> None:
        # 1. Render the frame (with flip if going left)
        frame = self._movie.currentPixmap()
        if self._direction == -1:
            frame = frame.transformed(QTransform().scale(-1, 1))
        self.setPixmap(frame)

        if self._is_walking:
            video_time = frame_num / GIF_FPS

            # Only update position during the actual walking window —
            # avoids any rounding jump during the standing-still frames.
            if video_time > self._accel_start:
                norm = _movement_norm(video_time, self._accel_start, self._full_speed_start,
                                     self._decel_start, self._walk_stop)
                new_x = self._walk_start_x + (self._walk_end_x - self._walk_start_x) * norm
                self.move(int(new_x), self.y())

            # Detect GIF loop by frame number wrapping back to near 0.
            # Avoids relying on frameCount() which may be 0 while loading.
            if self._last_frame_num > 50 and frame_num < 5:
                self.move(int(self._walk_end_x), self.y())
                self._enter_pause()

        self._last_frame_num = frame_num

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def _start_walk(self) -> None:
        parent = self.parent()
        if parent is None:
            return
        max_x = parent.width() - self.width()
        if max_x <= 0:
            return

        x = self.x()
        if x > max_x * 0.85:
            going_right = False
        elif x < max_x * 0.15:
            going_right = True
        else:
            going_right = random.choice([True, False])

        self._direction = 1 if going_right else -1
        walk_px = random.uniform(WALK_MIN_PX, WALK_MAX_PX)
        self._walk_start_x = float(x)
        if going_right:
            self._walk_end_x = min(x + walk_px, float(max_x))
        else:
            self._walk_end_x = max(x - walk_px, 0.0)

        self._is_walking = True
        self._last_frame_num = -1
        self._movie.jumpToFrame(0)
        self._movie.setPaused(False)

    def _enter_pause(self) -> None:
        self._is_walking = False
        self._movie.setPaused(True)
        # Show frame 0 (rest pose) while standing
        self._movie.jumpToFrame(0)
        delay_ms = int(random.uniform(PAUSE_MIN, PAUSE_MAX) * 1000)
        self._pause_timer.start(delay_ms)

    # ------------------------------------------------------------------
    # External control
    # ------------------------------------------------------------------

    def pause(self) -> None:
        self._pause_timer.stop()
        self._is_walking = False
        self._movie.setPaused(True)

    def resume(self) -> None:
        self._movie.jumpToFrame(0)
        delay_ms = int(random.uniform(1000, 3000))
        self._pause_timer.start(delay_ms)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self)
        super().mousePressEvent(event)

    def show_thinking(self) -> None:
        """Start thinking state. Bubble only shown if popover is not open."""
        if not self._popover_open:
            self._bubble.start()

    def hide_thinking(self, done: bool = False) -> None:
        """Stop thinking state. If done=True and popover not open, show 'done!' briefly."""
        self._bubble.stop(done=done and not self._popover_open)

    def set_popover_open(self, is_open: bool) -> None:
        """Track whether the chat popover is open (suppresses the thinking bubble)."""
        self._popover_open = is_open
        if is_open:
            self._bubble.stop(done=False)
