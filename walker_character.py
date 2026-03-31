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
