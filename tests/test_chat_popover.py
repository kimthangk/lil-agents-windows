import pytest
from PyQt6.QtCore import QPoint
from chat_popover import compute_popover_pos, POPOVER_WIDTH, POPOVER_HEIGHT, ChatPopover


def test_popover_anchors_above_character():
    pos = compute_popover_pos(QPoint(400, 900), 80, 1920)
    assert pos.y() == 900 - POPOVER_HEIGHT


def test_popover_aligns_with_character_x():
    pos = compute_popover_pos(QPoint(400, 900), 80, 1920)
    assert pos.x() == 400


def test_popover_shifts_left_near_right_edge():
    pos = compute_popover_pos(QPoint(1800, 900), 80, 1920)
    assert pos.x() == 1920 - POPOVER_WIDTH


def test_popover_clamps_to_left_edge():
    pos = compute_popover_pos(QPoint(-50, 900), 80, 1920)
    assert pos.x() == 0


def test_clear_command_clears_output(qtbot):
    popover = ChatPopover("claude")
    qtbot.addWidget(popover)
    popover._output.setPlainText("some text")
    popover._input.setText("/clear")
    popover._on_submit()
    assert popover._output.toPlainText() == ""


def test_help_command_shows_help(qtbot):
    popover = ChatPopover("claude")
    qtbot.addWidget(popover)
    popover._input.setText("/help")
    popover._on_submit()
    assert "Available commands" in popover._output.toPlainText()


def test_copy_command_puts_last_response_in_clipboard(qtbot):
    from PyQt6.QtWidgets import QApplication
    popover = ChatPopover("claude")
    qtbot.addWidget(popover)
    popover._last_response = "AI said hello"
    popover._input.setText("/copy")
    popover._on_submit()
    assert QApplication.clipboard().text() == "AI said hello"


def test_show_binary_not_found_displays_message(qtbot):
    popover = ChatPopover("claude")
    qtbot.addWidget(popover)
    popover.show_binary_not_found("claude")
    assert "claude" in popover._output.toPlainText()
    assert "PATH" in popover._output.toPlainText()
