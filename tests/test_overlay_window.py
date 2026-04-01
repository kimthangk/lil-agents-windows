from ctypes import wintypes
from overlay_window import compute_overlay_geometry, OVERLAY_HEIGHT


def _make_rect(left, top, right, bottom) -> wintypes.RECT:
    r = wintypes.RECT()
    r.left = left
    r.top = top
    r.right = right
    r.bottom = bottom
    return r


def test_overlay_sits_above_taskbar():
    rect = _make_rect(0, 1000, 1920, 1040)
    geom = compute_overlay_geometry(rect, 1920)
    assert geom.y() == 1000 - OVERLAY_HEIGHT


def test_overlay_spans_full_screen_width():
    rect = _make_rect(0, 1000, 1920, 1040)
    geom = compute_overlay_geometry(rect, 1920)
    assert geom.width() == 1920


def test_overlay_height_matches_constant():
    rect = _make_rect(0, 1000, 1920, 1040)
    geom = compute_overlay_geometry(rect, 1920)
    assert geom.height() == OVERLAY_HEIGHT


def test_overlay_starts_at_left_edge():
    rect = _make_rect(0, 1000, 1920, 1040)
    geom = compute_overlay_geometry(rect, 1920)
    assert geom.x() == 0


def test_overlay_adapts_to_high_dpi():
    # Simulates a 4K screen at 200% DPI: logical height 540, taskbar at y=500
    rect = _make_rect(0, 500, 960, 540)
    geom = compute_overlay_geometry(rect, 960)
    assert geom.y() == 500 - OVERLAY_HEIGHT
    assert geom.width() == 960
