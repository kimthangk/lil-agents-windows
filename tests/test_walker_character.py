import pytest
from PyQt6.QtWidgets import QWidget
from walker_character import WalkerCharacter

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
    qtbot.addWidget(char)
    assert char._direction == 1


def test_pause_stops_pause_timer(gif_file, container, qtbot):
    char = WalkerCharacter(gif_file, parent=container)
    qtbot.addWidget(char)
    char.pause()
    assert not char._pause_timer.isActive()


def test_resume_starts_pause_timer(gif_file, container, qtbot):
    char = WalkerCharacter(gif_file, parent=container)
    qtbot.addWidget(char)
    char.pause()
    char.resume()
    assert char._pause_timer.isActive()


def test_pause_stops_walking(gif_file, container, qtbot):
    char = WalkerCharacter(gif_file, parent=container)
    qtbot.addWidget(char)
    char._is_walking = True
    char.pause()
    assert not char._is_walking


def test_set_popover_open_suppresses_bubble(gif_file, container, qtbot):
    char = WalkerCharacter(gif_file, parent=container, accent_color="#a6e3a1")
    qtbot.addWidget(char)
    char.set_popover_open(True)
    assert char._popover_open is True
    char.show_thinking()
    assert not char._bubble.isVisible()


def test_set_popover_closed_allows_bubble(gif_file, container, qtbot):
    char = WalkerCharacter(gif_file, parent=container, accent_color="#a6e3a1")
    qtbot.addWidget(char)
    char.set_popover_open(False)
    assert char._popover_open is False


def test_hide_thinking_done_suppressed_when_popover_open(gif_file, container, qtbot):
    char = WalkerCharacter(gif_file, parent=container, accent_color="#a6e3a1")
    qtbot.addWidget(char)
    char.set_popover_open(True)
    # hide_thinking with done=True should not show the bubble when popover is open
    char.hide_thinking(done=True)
    assert not char._bubble.isVisible()
