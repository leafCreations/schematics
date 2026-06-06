"""Tests for ui.widgets.signal_utils."""

from PySide6.QtCore import QObject, Signal

from ui.widgets.signal_utils import CallbackGate, block_widget_signals


def test_callback_gate_block_sets_blocked():
    gate = CallbackGate()
    assert not gate.blocked

    with gate.block():
        assert gate.blocked

    assert not gate.blocked


def test_callback_gate_nested_block():
    gate = CallbackGate()

    with gate.block():
        with gate.block():
            assert gate.blocked
        assert gate.blocked

    assert not gate.blocked


def test_block_widget_signals_suppresses_emit():
    class Emitter(QObject):
        fired = Signal(int)

    emitter = Emitter()
    values: list[int] = []
    emitter.fired.connect(values.append)

    emitter.fired.emit(1)

    with block_widget_signals(emitter):
        emitter.fired.emit(2)

    emitter.fired.emit(3)
    assert values == [1, 3]
