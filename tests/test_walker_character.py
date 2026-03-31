import pytest
from PyQt6.QtWidgets import QWidget
from walker_character import WalkerCharacter, WALK_SPEED

# Minimal valid 1x1 animated GIF (2 frames, transparent)
MINIMAL_GIF = (
    b"GIF89a\x01\x00\x01\x00\xf0\x00\x00\xff\xff\xff\x00\x00\x00"
    b"!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00"
    b"\x02\x02D\x01\x00;"
)


@pytest.fixture
def gif_file(tmp_path):
    p = tmp_path / "test.gif"
    p.write_bytes(MINIMAL_GIF)
    return str(p)


@pytest.fixture
def container(qtbot):
    w = QWidget()
    w.resize(800, 80)
    qtbot.addWidget(w)
    w.show()
    return w


def test_initial_direction_is_right(gif_file, container, qtbot):
    char = WalkerCharacter(gif_file, parent=container)
    char.resize(80, 80)
    char.move(100, 0)
    qtbot.addWidget(char)
    assert char._direction == 1


def test_step_moves_right(gif_file, container, qtbot):
    char = WalkerCharacter(gif_file, parent=container)
    char.resize(80, 80)
    char.move(100, 0)
    qtbot.addWidget(char)
    initial_x = char.x()
    char._step()
    assert char.x() == initial_x + WALK_SPEED


def test_reverses_at_right_edge(gif_file, container, qtbot):
    char = WalkerCharacter(gif_file, parent=container)
    char.resize(80, 80)
    # Place at right edge (container.width() - char.width() = 720)
    char.move(720, 0)
    qtbot.addWidget(char)
    char._step()
    assert char._direction == -1


def test_reverses_at_left_edge(gif_file, container, qtbot):
    char = WalkerCharacter(gif_file, parent=container)
    char.resize(80, 80)
    char.move(0, 0)
    char._direction = -1
    qtbot.addWidget(char)
    char._step()
    assert char._direction == 1


def test_pause_stops_timer(gif_file, container, qtbot):
    char = WalkerCharacter(gif_file, parent=container)
    char.resize(80, 80)
    char.move(100, 0)
    qtbot.addWidget(char)
    char.pause()
    assert not char._timer.isActive()


def test_resume_restarts_timer(gif_file, container, qtbot):
    char = WalkerCharacter(gif_file, parent=container)
    char.resize(80, 80)
    char.move(100, 0)
    qtbot.addWidget(char)
    char.pause()
    char.resume()
    assert char._timer.isActive()
