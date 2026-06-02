"""Qt platform preflight checks for Linux desktop sessions."""

from __future__ import annotations

import ctypes.util
import os
import sys

# Qt 6.5+ fails to load the xcb plugin without this library.
_REQUIRED_XCB_LIBRARIES = ("xcb-cursor",)

# Helpful on multi-monitor X11 setups, but Qt can start without them.
_RECOMMENDED_XCB_LIBRARIES = ("xcb-xinerama0",)


def missing_qt_linux_libraries(*, required_only: bool = False) -> list[str]:
    """Return XCB libraries missing from the system loader path."""
    libraries = _REQUIRED_XCB_LIBRARIES

    if not required_only:
        libraries = _REQUIRED_XCB_LIBRARIES + _RECOMMENDED_XCB_LIBRARIES

    missing: list[str] = []

    for library in libraries:
        if ctypes.util.find_library(library) is None:
            missing.append(library)

    return missing


def qt_platform_hint() -> str | None:
    missing_required = missing_qt_linux_libraries(required_only=True)

    if not missing_required:
        return None

    packages = {
        "xcb-cursor": "libxcb-cursor0",
        "xcb-xinerama0": "libxcb-xinerama0",
    }
    apt_packages = ", ".join(packages[name] for name in missing_required)

    lines = [
        "PySide6 could not find required system libraries for the Qt xcb plugin:",
        *(f"  - lib{name}.so" for name in missing_required),
        "",
        "On Ubuntu/Debian, install:",
        f"  sudo apt install {apt_packages}",
        "",
        "If you are on a Wayland session, you can also try:",
        "  QT_QPA_PLATFORM=wayland python -m ui --structure residence --stage 1",
    ]

    return "\n".join(lines)


def ensure_qt_platform() -> None:
    if not sys.platform.startswith("linux"):
        return

    if os.environ.get("QT_QPA_PLATFORM"):
        return

    missing_required = missing_qt_linux_libraries(required_only=True)

    if os.environ.get("WAYLAND_DISPLAY") and missing_required:
        os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
        return

    hint = qt_platform_hint()

    if hint is not None:
        print(hint, file=sys.stderr)
        raise SystemExit(1)
