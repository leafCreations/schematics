"""Helpers for suppressing widget or panel callback signals during updates."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from PySide6.QtCore import QObject, QSignalBlocker


class CallbackGate:
    """Suppress panel handler callbacks during programmatic list/selection updates."""

    def __init__(self) -> None:
        self._blocked = False

    @property
    def blocked(self) -> bool:
        return self._blocked

    @contextmanager
    def block(self) -> Iterator[None]:
        was = self._blocked
        self._blocked = True
        try:
            yield
        finally:
            self._blocked = was


@contextmanager
def block_widget_signals(*objects: QObject) -> Iterator[None]:
    """Block Qt signals on one or more objects for the duration of the context."""
    blockers = [QSignalBlocker(obj) for obj in objects]
    try:
        yield
    finally:
        del blockers
