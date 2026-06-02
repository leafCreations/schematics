import pytest

pytest.importorskip("PySide6")

from ui.platform import missing_qt_linux_libraries, qt_platform_hint


def test_qt_platform_hint_when_libraries_missing(monkeypatch):
    monkeypatch.setattr(
        "ui.platform.missing_qt_linux_libraries",
        lambda *, required_only=False: ["xcb-cursor"],
    )

    hint = qt_platform_hint()

    assert hint is not None
    assert "libxcb-cursor0" in hint
    assert "QT_QPA_PLATFORM=wayland" in hint


def test_qt_platform_hint_none_when_libraries_present(monkeypatch):
    monkeypatch.setattr(
        "ui.platform.missing_qt_linux_libraries",
        lambda *, required_only=False: [],
    )

    assert qt_platform_hint() is None


def test_missing_qt_linux_libraries_returns_list():
    missing = missing_qt_linux_libraries()

    assert isinstance(missing, list)
