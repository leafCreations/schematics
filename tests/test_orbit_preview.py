"""Tests for 3D orbit preview mesh building."""

from __future__ import annotations

from helpers.context import SchematicContext
from helpers.orbit_mesh import (
    OrbitMeshData,
    build_box_orbit_mesh_from_context,
    build_orbit_mesh_from_context,
    iter_occupied_voxels,
)
from ui.mesh_build_worker import MeshBuildWorker


def _sample_ctx() -> SchematicContext:
    return SchematicContext(
        structure="test",
        stage=1,
        name="Orbit Sample",
        layers=[
            {
                "index": 0,
                "cells": [
                    ["A", "B"],
                    [".", "C"],
                ],
            },
            {
                "index": 1,
                "cells": [
                    ["D"],
                ],
            },
        ],
        grid={"site_size": 20, "offset_x": 2, "offset_z": 3},
        block_registry={},
        assets_dir=__import__("pathlib").Path("."),
        worldgen_template_dir=__import__("pathlib").Path("."),
        output_schematics_dir=__import__("pathlib").Path("."),
        output_worldgen_dir=__import__("pathlib").Path("."),
    )


def test_iter_occupied_voxels_applies_offsets_and_skips_empty():
    occupied = iter_occupied_voxels(_sample_ctx())
    positions = {position for position, _token in occupied}

    assert (2, 0, 3) in positions
    assert (3, 0, 3) in positions
    assert (3, 0, 4) in positions
    assert (2, 1, 3) in positions
    assert (2, 0, 4) not in positions


def test_build_orbit_mesh_combines_exterior_faces():
    mesh = build_orbit_mesh_from_context(_sample_ctx())

    assert isinstance(mesh, OrbitMeshData)
    assert mesh.vertex_count > 0
    assert len(mesh.positions) == mesh.vertex_count * 3
    assert len(mesh.colors) == mesh.vertex_count * 3
    assert mesh.bounds_radius >= 1.0


def test_build_orbit_mesh_empty_structure():
    ctx = _sample_ctx()
    ctx.layers = [{"index": 0, "cells": [[".", "."], [".", "."]]}]
    mesh = build_orbit_mesh_from_context(ctx)

    assert mesh.vertex_count == 0
    assert mesh.positions == ()


def test_mesh_build_worker_emits_finished():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")

    ctx = _sample_ctx()
    worker = MeshBuildWorker(ctx)
    results: list[OrbitMeshData] = []
    worker.finished.connect(results.append)

    worker.run()

    assert len(results) == 1
    assert results[0].vertex_count > 0


def test_orbit_preview_view_matrix_uses_qvector3d_lookat():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from helpers.orbit_camera import default_exterior_eye, forward_vector
    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    widget._bounds_center = (1.0, 2.0, 3.0)
    widget._bounds_radius = 4.0
    widget._distance = 12.0
    widget._camera_position = default_exterior_eye(
        widget._bounds_center,
        widget._bounds_radius,
        widget._azimuth,
        widget._elevation,
        widget._distance,
    )

    matrix = widget._view_matrix()
    fwd = forward_vector(widget._azimuth, widget._elevation)
    eye = widget._camera_position

    assert matrix.isIdentity() is False
    assert eye != widget._bounds_center
    assert abs(fwd[0]) + abs(fwd[1]) + abs(fwd[2]) > 0.0


def test_orbit_preview_keyboard_wasd_moves_on_plane():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    widget._bounds_radius = 5.0
    widget._elevation = 0.0
    start = (0.0, 0.0, 0.0)
    widget._camera_position = start

    assert widget._apply_keyboard_movement(Qt.Key.Key_W)
    forward_pos = widget._camera_position
    widget._camera_position = start
    assert widget._apply_keyboard_movement(Qt.Key.Key_Up)
    arrow_forward_pos = widget._camera_position

    assert forward_pos == arrow_forward_pos
    assert forward_pos != start
    assert forward_pos[1] == start[1]

    widget._camera_position = start
    assert widget._apply_keyboard_movement(Qt.Key.Key_A)
    assert widget._camera_position != start
    assert widget._camera_position[1] == start[1]

    widget._azimuth = 0.0
    widget._elevation = 0.0
    widget._camera_position = start
    assert widget._apply_keyboard_movement(Qt.Key.Key_D)
    assert widget._camera_position[0] > start[0]
    widget._camera_position = start
    assert widget._apply_keyboard_movement(Qt.Key.Key_A)
    assert widget._camera_position[0] < start[0]


def test_orbit_preview_forward_key_moves_along_look_when_pitched_down():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    widget._bounds_radius = 5.0
    widget._elevation = 0.5
    start = (0.0, 10.0, 0.0)
    widget._camera_position = start

    assert widget._apply_keyboard_movement(Qt.Key.Key_W)
    assert widget._camera_position[1] < start[1]
    assert widget._camera_position != start


def test_orbit_preview_space_hold_moves_vertical():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    widget._bounds_radius = 5.0
    start_y = 12.0
    widget._camera_position = (0.0, start_y, 0.0)

    assert widget._apply_movement_for_keys({Qt.Key.Key_Space})
    assert widget._camera_position[1] > start_y

    widget._camera_position = (0.0, start_y, 0.0)
    assert widget._apply_movement_for_keys({Qt.Key.Key_Shift})
    assert widget._camera_position[1] < start_y


def test_orbit_preview_key_press_hold_starts_movement_timer():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QEvent, Qt
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    press = QKeyEvent(
        QEvent.Type.KeyPress,
        Qt.Key.Key_Space,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.keyPressEvent(press)

    assert Qt.Key.Key_Space in widget._held_movement_keys
    assert widget._movement_timer.isActive()

    release = QKeyEvent(
        QEvent.Type.KeyRelease,
        Qt.Key.Key_Space,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.keyReleaseEvent(release)

    assert Qt.Key.Key_Space not in widget._held_movement_keys
    assert not widget._movement_timer.isActive()


def test_orbit_preview_autorepeat_release_keeps_held_key():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QEvent, Qt
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    press = QKeyEvent(
        QEvent.Type.KeyPress,
        Qt.Key.Key_W,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.keyPressEvent(press)

    autorep_release = QKeyEvent(
        QEvent.Type.KeyRelease,
        Qt.Key.Key_W,
        Qt.KeyboardModifier.NoModifier,
        autorep=True,
    )
    widget.keyReleaseEvent(autorep_release)

    assert Qt.Key.Key_W in widget._held_movement_keys
    assert widget._movement_timer.isActive()

    release = QKeyEvent(
        QEvent.Type.KeyRelease,
        Qt.Key.Key_W,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.keyReleaseEvent(release)

    assert Qt.Key.Key_W not in widget._held_movement_keys
    assert not widget._movement_timer.isActive()


def test_orbit_preview_shift_key_is_movement_key():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    assert widget._normalize_movement_key(Qt.Key.Key_Shift) == Qt.Key.Key_Shift
    assert widget._normalize_movement_key(Qt.Key.Key_R) is None


def test_orbit_preview_reset_restores_default_exterior_pose():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from helpers.orbit_camera import default_exterior_eye
    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    mesh = build_orbit_mesh_from_context(_sample_ctx())
    widget._mesh = mesh
    widget._vertex_count = mesh.vertex_count
    widget._bounds_center = mesh.bounds_center
    widget._bounds_radius = mesh.bounds_radius

    widget._azimuth = 2.1
    widget._elevation = -0.8
    widget._camera_position = (99.0, 88.0, 77.0)

    assert widget._apply_keyboard_movement(Qt.Key.Key_W)
    moved_pos = widget._camera_position

    assert widget.reset_camera_to_default()
    assert widget._azimuth == pytest.approx(0.7)
    assert widget._elevation == pytest.approx(0.45)
    expected_distance = max(24.0, mesh.bounds_radius * 2.5)
    assert widget._distance == pytest.approx(expected_distance)
    expected_eye = default_exterior_eye(
        mesh.bounds_center,
        mesh.bounds_radius,
        0.7,
        0.45,
        expected_distance,
    )
    assert widget._camera_position == pytest.approx(expected_eye)
    assert widget._camera_position != moved_pos


def test_orbit_preview_apply_camera_pose_restores_azimuth_and_position():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from helpers.orbit_camera import default_exterior_eye
    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    mesh = build_orbit_mesh_from_context(_sample_ctx())
    widget._mesh = mesh
    widget._vertex_count = mesh.vertex_count
    widget._bounds_center = mesh.bounds_center
    widget._bounds_radius = mesh.bounds_radius

    saved_pos = (12.0, 5.0, -8.0)
    saved_az = 1.5
    saved_el = -0.3

    assert widget.apply_camera_pose(
        position=saved_pos,
        azimuth=saved_az,
        elevation=saved_el,
    )
    assert widget._azimuth == pytest.approx(saved_az)
    assert widget._elevation == pytest.approx(saved_el)
    assert widget._camera_position == pytest.approx(saved_pos)
    assert widget._keep_pose_on_mesh_upload is True

    widget._bounds_center = mesh.bounds_center
    widget._bounds_radius = mesh.bounds_radius
    if not widget._keep_pose_on_mesh_upload:
        widget._camera_position = default_exterior_eye(
            widget._bounds_center,
            widget._bounds_radius,
            widget._azimuth,
            widget._elevation,
            widget._distance,
        )
    assert widget._camera_position == pytest.approx(saved_pos)

    assert not widget.apply_camera_pose(
        position=(0.0, 0.0, 0.0),
        azimuth=0.0,
        elevation=99.0,
    )


def test_orbit_preview_projection_near_plane_scales_with_bounds_radius():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    small = OrbitPreviewWidget()
    small._bounds_radius = 5.0
    large = OrbitPreviewWidget()
    large._bounds_radius = 40.0

    small_near = small._projection_near_plane()
    large_near = large._projection_near_plane()
    small_far = small._projection_far_plane()
    large_far = large._projection_far_plane()

    assert small_near < large_near
    assert small_far < large_far
    assert small_near == pytest.approx(5.0 * 0.008)
    assert large_near == pytest.approx(40.0 * 0.008)


def test_orbit_preview_mouse_look_delta_increases_azimuth():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    widget._azimuth = 0.5
    widget._apply_mouse_look_delta(-10.0, 0.0)

    assert widget._azimuth == pytest.approx(0.6)


def test_orbit_preview_enables_mouse_tracking():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    assert widget.hasMouseTracking() is True


def test_orbit_preview_mouse_look_requires_pointer_capture(monkeypatch):
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QPoint, QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    widget._azimuth = 0.5
    widget._skip_next_mouse_look = False
    widget._last_look_global = QPoint(100, 100)

    move = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(110, 100),
        QPointF(110, 100),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget._pointer_captured = False
    widget.mouseMoveEvent(move)
    assert widget._azimuth == pytest.approx(0.5)

    widget._pointer_captured = True
    widget._skip_next_mouse_look = False
    widget._last_look_global = QPoint(100, 100)
    widget.mouseMoveEvent(move)
    assert widget._azimuth == pytest.approx(0.4)


def test_orbit_preview_pointer_capture_grabs_mouse_and_keyboard():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    widget._capture_pointer()
    assert widget._pointer_captured is True
    assert widget._pointer_cursor_hidden is True
    assert widget.mouseGrabber() is widget

    widget._release_pointer()
    assert widget._pointer_captured is False
    assert widget._pointer_cursor_hidden is False
    assert widget.mouseGrabber() is None


def test_orbit_preview_focus_hides_pointer_cursor():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    widget._capture_pointer()
    assert widget._pointer_cursor_hidden is True

    widget._release_pointer()
    assert widget._pointer_cursor_hidden is False


def test_orbit_preview_escape_clears_focus(monkeypatch):
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    widget._capture_pointer()
    assert widget._pointer_captured is True
    cleared = False

    def _clear_focus() -> None:
        nonlocal cleared
        cleared = True

    monkeypatch.setattr(widget, "hasFocus", lambda: True)
    monkeypatch.setattr(widget, "clearFocus", _clear_focus)

    widget.keyPressEvent(
        QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_Escape,
            Qt.KeyboardModifier.NoModifier,
        ),
    )
    assert cleared
    assert widget._pointer_captured is False
    assert widget._pointer_cursor_hidden is False


def test_orbit_preview_mouse_look_skips_first_move_after_anchor_reset():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    widget.show()
    application.processEvents()
    widget._azimuth = 0.5
    widget._pointer_captured = True
    widget._reset_mouse_look_anchor()
    assert widget._skip_next_mouse_look is True

    first = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(200, 200),
        QPointF(200, 200),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mouseMoveEvent(first)
    assert widget._azimuth == pytest.approx(0.5)

    second = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(210, 200),
        QPointF(210, 200),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mouseMoveEvent(second)
    assert widget._azimuth == pytest.approx(0.4)


def test_orbit_preview_wheel_event_does_not_move_camera(monkeypatch):
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from unittest.mock import MagicMock

    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    monkeypatch.setattr(
        "ui.widgets.orbit_preview_widget.set_orbit_camera_move_speed",
        lambda _value: None,
    )

    widget = OrbitPreviewWidget()
    start = (1.0, 2.0, 3.0)
    widget._camera_position = start
    widget._pointer_captured = True

    delta = MagicMock()
    delta.y.return_value = 120
    event = MagicMock()
    event.angleDelta.return_value = delta

    widget.wheelEvent(event)
    assert widget._camera_position == start


def test_orbit_preview_wheel_adjusts_move_speed_multiplier(monkeypatch):
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from unittest.mock import MagicMock

    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    saved: list[float] = []
    monkeypatch.setattr(
        "ui.widgets.orbit_preview_widget.set_orbit_camera_move_speed",
        lambda value: saved.append(value),
    )

    widget = OrbitPreviewWidget()
    widget._move_speed_multiplier = 0.65
    widget._pointer_captured = True

    delta = MagicMock()
    delta.y.return_value = 120
    event = MagicMock()
    event.angleDelta.return_value = delta

    widget.wheelEvent(event)
    assert widget.move_speed_multiplier() == pytest.approx(0.7)
    assert len(saved) == 1
    assert saved[0] == pytest.approx(0.7)
    event.accept.assert_called_once()


def test_orbit_preview_wheel_at_clamp_still_shows_speed_feedback(monkeypatch):
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from unittest.mock import MagicMock

    from PySide6.QtWidgets import QApplication

    from ui.app_settings import _ORBIT_CAMERA_MOVE_SPEED_MAX
    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    monkeypatch.setattr(
        "ui.widgets.orbit_preview_widget.set_orbit_camera_move_speed",
        lambda _value: None,
    )

    widget = OrbitPreviewWidget()
    widget.resize(400, 300)
    widget.show()
    widget._move_speed_multiplier = _ORBIT_CAMERA_MOVE_SPEED_MAX
    widget._pointer_captured = True

    delta = MagicMock()
    delta.y.return_value = 120
    event = MagicMock()
    event.angleDelta.return_value = delta

    emitted: list[str] = []
    widget.move_speed_feedback.connect(emitted.append)

    widget.wheelEvent(event)
    assert len(emitted) == 1
    assert f"{_ORBIT_CAMERA_MOVE_SPEED_MAX:.1f}" in emitted[0]


def test_orbit_preview_plus_minus_adjust_move_speed(monkeypatch):
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    saved: list[float] = []
    monkeypatch.setattr(
        "ui.widgets.orbit_preview_widget.set_orbit_camera_move_speed",
        lambda value: saved.append(value),
    )

    widget = OrbitPreviewWidget()
    widget.resize(400, 300)
    widget.show()
    widget._move_speed_multiplier = 0.65

    emitted: list[str] = []
    widget.move_speed_feedback.connect(emitted.append)

    assert widget._try_adjust_move_speed_key(Qt.Key.Key_Equal)
    assert widget.move_speed_multiplier() == pytest.approx(0.7)
    assert len(emitted) == 1
    assert "0.7" in emitted[0]

    assert widget._try_adjust_move_speed_key(Qt.Key.Key_Minus)
    assert widget.move_speed_multiplier() == pytest.approx(0.65)
    assert len(saved) == 2
    assert saved[0] == pytest.approx(0.7)
    assert saved[1] == pytest.approx(0.65)


def test_orbit_preview_movement_step_scales_with_move_speed():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    widget._bounds_radius = 10.0
    widget._move_speed_multiplier = 2.0
    base = 0.08 * 10.0
    assert widget._movement_step() == pytest.approx(base * 2.0)


def test_orbit_preview_movement_distance_scales_with_elapsed():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    widget._bounds_radius = 10.0
    widget._move_speed_multiplier = 1.0
    full = widget._movement_distance(50)
    half = widget._movement_distance(25)
    assert full == pytest.approx(widget._movement_step())
    assert half == pytest.approx(full * 0.5)


def test_orbit_preview_emits_move_speed_feedback(monkeypatch):
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    monkeypatch.setattr(
        "ui.widgets.orbit_preview_widget.set_orbit_camera_move_speed",
        lambda _value: None,
    )

    widget = OrbitPreviewWidget()
    emitted: list[str] = []
    widget.move_speed_feedback.connect(emitted.append)

    widget._set_move_speed_multiplier(0.8)
    assert len(emitted) == 1
    assert "0.8" in emitted[0]


def _orbit_preview_widget_with_mesh():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from ui.widgets.orbit_preview_widget import OrbitPreviewWidget

    application = QApplication.instance() or QApplication([])
    _ = application

    widget = OrbitPreviewWidget()
    mesh = build_orbit_mesh_from_context(_sample_ctx())
    widget._mesh = mesh
    widget._pending_mesh = mesh
    widget._vertex_count = mesh.vertex_count
    widget._bounds_center = mesh.bounds_center
    widget._bounds_radius = mesh.bounds_radius
    widget.show()
    widget._refresh_camera_hud()
    return widget, mesh


def test_orbit_preview_crosshair_visible_when_hud_and_mesh_active():
    widget, _mesh = _orbit_preview_widget_with_mesh()
    widget.set_orbit_view_active(True)
    widget.set_camera_hud_visible(True)

    assert widget._crosshair.isVisible()
    assert widget._crosshair.testAttribute(
        __import__("PySide6").QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents,
    )


def test_orbit_preview_crosshair_hidden_when_hud_off_or_not_3d():
    widget, _mesh = _orbit_preview_widget_with_mesh()
    widget.set_orbit_view_active(True)
    widget.set_camera_hud_visible(True)
    assert widget._crosshair.isVisible()

    widget.set_camera_hud_visible(False)
    assert not widget._crosshair.isVisible()

    widget.set_camera_hud_visible(True)
    widget.set_orbit_view_active(False)
    assert not widget._crosshair.isVisible()


def test_orbit_preview_crosshair_centered_after_resize():
    widget, _mesh = _orbit_preview_widget_with_mesh()
    widget.set_orbit_view_active(True)
    widget.set_camera_hud_visible(True)
    widget.resize(640, 480)
    widget._layout_crosshair()

    geo = widget._crosshair.geometry()
    assert geo.x() + geo.width() // 2 == widget.width() // 2
    assert geo.y() + geo.height() // 2 == widget.height() // 2


def test_orbit_preview_crosshair_hidden_when_pref_off():
    widget, _mesh = _orbit_preview_widget_with_mesh()
    widget.set_orbit_view_active(True)
    widget.set_camera_hud_visible(True)
    widget.set_crosshair_visible(True)
    assert widget._crosshair.isVisible()

    widget.set_crosshair_visible(False)
    assert not widget._crosshair.isVisible()
    assert widget._hud_panel.isVisible()


def test_orbit_preview_hud_placement_geometry():
    widget, _mesh = _orbit_preview_widget_with_mesh()
    widget.set_orbit_view_active(True)
    widget.set_camera_hud_visible(True)
    widget.resize(400, 300)

    widget.set_hud_placement("top_right")
    widget._layout_camera_hud()
    top_right = widget._hud_panel.geometry()

    widget.set_hud_placement("top_left")
    widget._layout_camera_hud()
    top_left = widget._hud_panel.geometry()

    widget.set_hud_placement("bottom_center")
    widget._layout_camera_hud()
    bottom_center = widget._hud_panel.geometry()

    assert top_left.x() < top_right.x()
    assert bottom_center.y() > top_right.y()
    assert abs(bottom_center.x() + bottom_center.width() // 2 - widget.width() // 2) < 4


def test_face_count_scales_with_surface_not_volume():
    wide_cells = [["A" for _ in range(8)] for _ in range(8)]

    wide_ctx = _sample_ctx()
    wide_ctx.layers = [{"index": 0, "cells": wide_cells}]
    wide_ctx.grid = {"site_size": 20, "offset_x": 0, "offset_z": 0}
    wide = build_orbit_mesh_from_context(wide_ctx)
    box = build_box_orbit_mesh_from_context(wide_ctx)

    assert wide.triangle_count == 12
    assert box.triangle_count > wide.triangle_count
    assert box.triangle_count < 8 * 8 * 6 * 2


def test_greedy_default_builder_uses_fewer_triangles_than_box_baseline():
    wide_cells = [["A" for _ in range(6)] for _ in range(6)]
    ctx = _sample_ctx()
    ctx.layers = [{"index": 0, "cells": wide_cells}]
    ctx.grid = {"site_size": 20, "offset_x": 0, "offset_z": 0}

    greedy = build_orbit_mesh_from_context(ctx)
    box = build_box_orbit_mesh_from_context(ctx)

    assert greedy.triangle_count < box.triangle_count
