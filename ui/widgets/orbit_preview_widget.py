"""OpenGL orbit camera widget for 3D greedy-meshed preview."""

from __future__ import annotations

import array

from PySide6.QtCore import QElapsedTimer, QPoint, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush,
    QCursor,
    QEnterEvent,
    QFocusEvent,
    QIcon,
    QImage,
    QKeyEvent,
    QMatrix4x4,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QVector3D,
    QWheelEvent,
)
from PySide6.QtOpenGL import (
    QOpenGLBuffer,
    QOpenGLShader,
    QOpenGLShaderProgram,
    QOpenGLTexture,
    QOpenGLVertexArrayObject,
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from helpers.orbit_camera import (
    default_exterior_eye,
    format_camera_hud_lines,
    forward_vector,
    move_along_look,
    move_on_plane,
)
from helpers.orbit_mesh import OrbitMeshData
from ui.app_settings import (
    ORBIT_CAMERA_MOVE_SPEED_WHEEL_STEP,
    clamp_orbit_camera_move_speed,
    parse_orbit_camera_azimuth,
    parse_orbit_camera_elevation,
    parse_orbit_camera_hud_placement,
    parse_orbit_camera_position,
)
from ui.editor_prefs import (
    orbit_camera_hud_crosshair_visible,
    orbit_camera_hud_placement,
    orbit_camera_move_speed,
    set_orbit_camera_move_speed,
)
from ui.widgets.panel_tool_button import make_panel_tool_button

_GL_FLOAT = 0x1406
_GL_COLOR_BUFFER_BIT = 0x00004000
_GL_DEPTH_BUFFER_BIT = 0x00000100
_GL_DEPTH_TEST = 0x0B71
_GL_TRIANGLES = 0x0004
_MOVEMENT_TICK_MS = 16
_MOVEMENT_REFERENCE_TICK_MS = 50
_SPEED_FEEDBACK_MS = 2000
_WHEEL_ANGLE_DELTA = 120

# Center reticle: 2px dot + 2px gap + 8px arms (matches fc3a reference art).
_CROSSHAIR_UNIT = 2
_CROSSHAIR_GAP = 2
_CROSSHAIR_ARM = 8
_CROSSHAIR_SIZE = (_CROSSHAIR_UNIT // 2 + _CROSSHAIR_GAP + _CROSSHAIR_ARM) * 2 + _CROSSHAIR_UNIT
ORBIT_CROSSHAIR_SIZE = _CROSSHAIR_SIZE
ORBIT_SPEED_FEEDBACK_MS = _SPEED_FEEDBACK_MS


class _CrosshairOverlay(QWidget):
    """Screen-center reticle marking the look-ray origin (fc3a)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(_CROSSHAIR_SIZE, _CROSSHAIR_SIZE)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(_CROSSHAIR_SIZE, _CROSSHAIR_SIZE)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(Qt.GlobalColor.white))

        unit = _CROSSHAIR_UNIT
        gap = _CROSSHAIR_GAP
        arm = _CROSSHAIR_ARM
        cx = self.width() // 2
        cy = self.height() // 2
        half = unit // 2
        inner = half + gap

        painter.drawRect(cx - half, cy - half, unit, unit)
        painter.drawRect(cx - half, cy - inner - arm, unit, arm)
        painter.drawRect(cx - half, cy + inner, unit, arm)
        painter.drawRect(cx - inner - arm, cy - half, arm, unit)
        painter.drawRect(cx + inner, cy - half, arm, unit)


_VERTEX_SHADER_COLOR = """
attribute vec3 aPos;
attribute vec3 aCol;
varying vec3 vCol;
uniform mat4 uMvp;
void main() {
    vCol = aCol;
    gl_Position = uMvp * vec4(aPos, 1.0);
}
"""

_FRAGMENT_SHADER_COLOR = """
varying vec3 vCol;
void main() {
    gl_FragColor = vec4(vCol * 0.85 + vec3(0.08), 1.0);
}
"""

_VERTEX_SHADER_TEXTURED = """
attribute vec3 aPos;
attribute vec3 aNormal;
attribute vec4 aTileRect;
varying vec3 vWorldPos;
varying vec3 vNormal;
varying vec4 vTileRect;
uniform mat4 uMvp;
void main() {
    vWorldPos = aPos;
    vNormal = aNormal;
    vTileRect = aTileRect;
    gl_Position = uMvp * vec4(aPos, 1.0);
}
"""

_FRAGMENT_SHADER_TEXTURED = """
varying vec3 vWorldPos;
varying vec3 vNormal;
varying vec4 vTileRect;
uniform sampler2D uAtlas;

vec2 tileFrac(vec3 pos, vec3 normal) {
    vec3 absNormal = abs(normal);
    if (absNormal.y >= absNormal.x && absNormal.y >= absNormal.z) {
        return fract(pos.xz);
    }
    if (absNormal.x >= absNormal.z) {
        return fract(vec2(pos.z, pos.y));
    }
    return fract(vec2(pos.x, pos.y));
}

void main() {
    vec2 t = tileFrac(vWorldPos, vNormal);
    vec2 atlasUv = mix(vTileRect.xy, vTileRect.zw, t);
    vec4 sample = texture2D(uAtlas, atlasUv);
    if (sample.a < 0.05) {
        discard;
    }
    gl_FragColor = vec4(sample.rgb * 0.92 + vec3(0.04), 1.0);
}
"""


def _hud_settings_icon() -> QIcon:
    for theme_name in ("preferences-system", "document-properties", "preferences-desktop"):
        themed = QIcon.fromTheme(theme_name)
        if not themed.isNull():
            return themed
    return QIcon()


class OrbitPreviewWidget(QOpenGLWidget):
    """Orbit view of a combined greedy mesh with optional catalog texture atlas."""

    move_speed_feedback = Signal(str)
    hud_settings_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(240, 180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

        self._mesh: OrbitMeshData | None = None
        self._pending_mesh: OrbitMeshData | None = None
        self._vertex_count = 0
        self._textured = False
        self._bounds_center = (0.0, 0.0, 0.0)
        self._bounds_radius = 1.0
        self._viewport_width = 1
        self._viewport_height = 1

        self._azimuth = 0.7
        self._elevation = 0.45
        self._distance = 24.0
        self._camera_position = (0.0, 0.0, 0.0)
        self._last_look_pos = QPoint()
        self._last_look_global = QPoint()
        self._skip_next_mouse_look = False
        self._pointer_cursor_hidden = False
        self._pointer_captured = False

        self._color_program: QOpenGLShaderProgram | None = None
        self._textured_program: QOpenGLShaderProgram | None = None
        self._vao = QOpenGLVertexArrayObject(self)
        self._position_buffer = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        self._color_buffer = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        self._normal_buffer = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        self._tile_rect_buffer = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        self._atlas_texture: QOpenGLTexture | None = None
        self._gl_ready = False

        self._orbit_overlay_hint = (
            "Click the 3D view to look (cursor hidden). Esc to release. "
            "Scroll or +/- adjusts fly speed (not mouse look). "
            "Hold W/S or ↑/↓ along look; A/D or ←/→ strafe; "
            "Space / Shift up/down. R to reset view."
        )
        self._overlay = QLabel(self._orbit_overlay_hint, self)
        self._overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._overlay.setStyleSheet("color: #888; background: transparent;")
        self._overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._camera_hud_visible = True
        self._hud_placement = orbit_camera_hud_placement()
        self._crosshair_visible_pref = orbit_camera_hud_crosshair_visible()
        self._hud_panel = QWidget(self)
        self._hud_panel.setStyleSheet("background-color: rgba(0, 0, 0, 120);")
        hud_layout = QVBoxLayout(self._hud_panel)
        hud_layout.setContentsMargins(6, 4, 6, 6)
        hud_layout.setSpacing(2)
        hud_header = QHBoxLayout()
        hud_header.setContentsMargins(0, 0, 0, 0)
        hud_header.addStretch()
        self._hud_settings_button = make_panel_tool_button(
            _hud_settings_icon(),
            "HUD Properties…",
            clicked=self._on_hud_settings_clicked,
        )
        hud_header.addWidget(self._hud_settings_button)
        self._hud_label = QLabel("")
        self._hud_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
        )
        self._hud_label.setStyleSheet("color: #ddd; background: transparent;")
        self._hud_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        hud_layout.addLayout(hud_header)
        hud_layout.addWidget(self._hud_label)
        self._hud_panel.hide()

        self._orbit_view_active = True
        self._crosshair = _CrosshairOverlay(self)
        self._crosshair.hide()

        self._move_speed_multiplier = orbit_camera_move_speed()

        self._held_movement_keys: set[int] = set()
        self._movement_elapsed = QElapsedTimer()
        self._movement_timer = QTimer(self)
        self._movement_timer.setInterval(_MOVEMENT_TICK_MS)
        self._movement_timer.timeout.connect(self._on_movement_timer_tick)
        self._keep_pose_on_mesh_upload = False

    def export_camera_pose(self) -> dict[str, object] | None:
        """Return the current camera pose when a mesh is loaded."""
        if self._mesh is None or self._vertex_count == 0:
            return None
        return {
            "position": self._camera_position,
            "azimuth": self._azimuth,
            "elevation": self._elevation,
        }

    def apply_camera_pose(
        self,
        *,
        position: tuple[float, float, float],
        azimuth: float,
        elevation: float,
    ) -> bool:
        """Apply a saved pose; mesh upload keeps this eye position instead of default exterior."""
        parsed_position = parse_orbit_camera_position(list(position))
        parsed_azimuth = parse_orbit_camera_azimuth(azimuth)
        parsed_elevation = parse_orbit_camera_elevation(elevation)
        if parsed_position is None or parsed_azimuth is None or parsed_elevation is None:
            self._keep_pose_on_mesh_upload = False
            return False

        self._azimuth = parsed_azimuth
        self._elevation = parsed_elevation
        self._camera_position = parsed_position
        self._keep_pose_on_mesh_upload = True
        self._refresh_camera_hud()
        return True

    def has_mesh(self) -> bool:
        return self._mesh is not None and self._mesh.vertex_count > 0

    def camera_hud_visible(self) -> bool:
        return self._camera_hud_visible

    def set_camera_hud_visible(self, visible: bool) -> None:
        self._camera_hud_visible = visible
        self._refresh_camera_hud()

    def hud_placement(self) -> str:
        return self._hud_placement

    def set_hud_placement(self, placement: str) -> None:
        self._hud_placement = parse_orbit_camera_hud_placement(placement)
        self._layout_camera_hud()

    def set_crosshair_visible(self, visible: bool) -> None:
        self._crosshair_visible_pref = visible
        self._refresh_camera_hud()

    def set_move_speed_multiplier(self, value: float) -> None:
        """Apply fly speed from prefs or dialog without transient feedback."""
        self._move_speed_multiplier = clamp_orbit_camera_move_speed(value)

    def _on_hud_settings_clicked(self) -> None:
        self.hud_settings_requested.emit()

    def set_orbit_view_active(self, active: bool) -> None:
        """True when the preview panel is showing this widget in 3D (not 2D)."""
        self._orbit_view_active = active
        if not active:
            self._release_pointer()
            if self.hasFocus():
                self.clearFocus()
        self._refresh_camera_hud()

    def set_mesh(self, mesh: OrbitMeshData | None) -> None:
        self._pending_mesh = mesh
        if self._gl_ready:
            self._upload_pending_mesh()
        if mesh is None:
            self._overlay.setText("Building 3D mesh…")
            self._overlay.setVisible(True)
        elif mesh.vertex_count == 0:
            self._overlay.setText("No blocks to display.")
            self._overlay.setVisible(True)
        else:
            self._overlay.setText(self._orbit_overlay_hint)
            self._overlay.setVisible(False)
        self._refresh_camera_hud()
        self.update()

    def set_status_message(self, message: str) -> None:
        self._overlay.setText(message)
        self._overlay.setVisible(True)
        self.update()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._overlay.setGeometry(self.rect())
        self._layout_camera_hud()
        self._layout_crosshair()

    def move_speed_multiplier(self) -> float:
        return self._move_speed_multiplier

    def _layout_camera_hud(self) -> None:
        margin = 8
        self._hud_panel.adjustSize()
        label_width = self._hud_label.sizeHint().width()
        label_height = self._hud_label.sizeHint().height()
        width = min(label_width + 24, max(self.width() - margin * 2, 120))
        height = label_height + self._hud_settings_button.sizeHint().height() + 20
        x, y = self._hud_panel_position(width, height)
        self._hud_panel.setGeometry(x, y, width, height)

    def _hud_panel_position(self, panel_width: int, panel_height: int) -> tuple[int, int]:
        margin = 8
        view_width = max(self.width(), 1)
        view_height = max(self.height(), 1)
        placements = {
            "top_left": (margin, margin),
            "top_center": ((view_width - panel_width) // 2, margin),
            "top_right": (max(margin, view_width - panel_width - margin), margin),
            "middle_left": (margin, (view_height - panel_height) // 2),
            "middle_right": (
                max(margin, view_width - panel_width - margin),
                (view_height - panel_height) // 2,
            ),
            "bottom_left": (margin, max(margin, view_height - panel_height - margin)),
            "bottom_center": (
                (view_width - panel_width) // 2,
                max(margin, view_height - panel_height - margin),
            ),
            "bottom_right": (
                max(margin, view_width - panel_width - margin),
                max(margin, view_height - panel_height - margin),
            ),
        }
        return placements.get(self._hud_placement, placements["top_right"])

    def _layout_crosshair(self) -> None:
        half = _CROSSHAIR_SIZE // 2
        cx = self.width() // 2
        cy = self.height() // 2
        self._crosshair.setGeometry(cx - half, cy - half, _CROSSHAIR_SIZE, _CROSSHAIR_SIZE)

    def _hud_overlay_visible(self) -> bool:
        active_mesh = self._mesh if self._mesh is not None else self._pending_mesh
        return (
            self._orbit_view_active
            and self._camera_hud_visible
            and active_mesh is not None
            and active_mesh.vertex_count > 0
        )

    def _refresh_camera_hud(self) -> None:
        if not self._hud_overlay_visible():
            self._hud_panel.hide()
            self._crosshair.hide()
            return

        active_mesh = self._mesh if self._mesh is not None else self._pending_mesh
        assert active_mesh is not None
        lines = format_camera_hud_lines(
            azimuth=self._azimuth,
            elevation=self._elevation,
            position=self._camera_position,
            offset_x=active_mesh.offset_x,
            offset_z=active_mesh.offset_z,
            voxel_map=active_mesh.hud_voxel_dict(),
        )
        self._hud_label.setText("\n".join(lines))
        self._layout_camera_hud()
        self._hud_panel.show()
        self._layout_crosshair()
        if self._crosshair_visible_pref:
            self._crosshair.show()
        else:
            self._crosshair.hide()

    def initializeGL(self) -> None:  # noqa: N802
        self._color_program = self._link_program(
            _VERTEX_SHADER_COLOR,
            _FRAGMENT_SHADER_COLOR,
            (("aPos", 0), ("aCol", 1)),
        )
        self._textured_program = self._link_program(
            _VERTEX_SHADER_TEXTURED,
            _FRAGMENT_SHADER_TEXTURED,
            (("aPos", 0), ("aNormal", 1), ("aTileRect", 2)),
        )
        self._vao.create()
        self._position_buffer.create()
        self._color_buffer.create()
        self._normal_buffer.create()
        self._tile_rect_buffer.create()
        self._gl_ready = True
        self._upload_pending_mesh()

    def paintGL(self) -> None:  # noqa: N802
        ctx = self.context()
        if ctx is None:
            return

        funcs = ctx.functions()
        funcs.glClearColor(0.12, 0.13, 0.16, 1.0)
        funcs.glClear(_GL_COLOR_BUFFER_BIT | _GL_DEPTH_BUFFER_BIT)
        funcs.glEnable(_GL_DEPTH_TEST)

        if self._vertex_count == 0:
            self._raise_widget_overlays()
            return

        program = self._textured_program if self._textured else self._color_program
        if program is None:
            self._raise_widget_overlays()
            return

        program.bind()
        mvp = self._projection_matrix() * self._view_matrix()
        program.setUniformValue("uMvp", mvp)

        if self._textured and self._atlas_texture is not None:
            self._atlas_texture.bind()
            program.setUniformValue("uAtlas", 0)

        self._vao.bind()
        self._position_buffer.bind()
        program.enableAttributeArray(0)
        program.setAttributeBuffer(0, _GL_FLOAT, 0, 3)

        if self._textured:
            self._normal_buffer.bind()
            program.enableAttributeArray(1)
            program.setAttributeBuffer(1, _GL_FLOAT, 0, 3)
            self._tile_rect_buffer.bind()
            program.enableAttributeArray(2)
            program.setAttributeBuffer(2, _GL_FLOAT, 0, 4)
        else:
            self._color_buffer.bind()
            program.enableAttributeArray(1)
            program.setAttributeBuffer(1, _GL_FLOAT, 0, 3)

        funcs.glDrawArrays(_GL_TRIANGLES, 0, self._vertex_count)

        if self._textured and self._atlas_texture is not None:
            self._atlas_texture.release()

        self._vao.release()
        program.release()
        self._raise_widget_overlays()

    def _raise_widget_overlays(self) -> None:
        """Keep QLabel children visible above the GL framebuffer (QOpenGLWidget quirk)."""
        for widget in (
            self._overlay,
            self._hud_panel,
            self._crosshair,
        ):
            if widget.isVisible():
                widget.raise_()

    def resizeGL(self, width: int, height: int) -> None:  # noqa: N802
        self._viewport_width = max(width, 1)
        self._viewport_height = max(height, 1)

    def _mouse_look_enabled(self) -> bool:
        """True while pointer is captured (click 3D view; released with Esc)."""
        return self._pointer_captured

    def _hide_pointer_cursor(self) -> None:
        if self._pointer_cursor_hidden:
            return
        QApplication.setOverrideCursor(Qt.CursorShape.BlankCursor)
        self._pointer_cursor_hidden = True

    def _show_pointer_cursor(self) -> None:
        if not self._pointer_cursor_hidden:
            return
        QApplication.restoreOverrideCursor()
        self._pointer_cursor_hidden = False

    def _capture_pointer(self) -> None:
        if self._pointer_captured:
            self._reset_mouse_look_anchor()
            return
        self.grabMouse()
        self.grabKeyboard()
        self._hide_pointer_cursor()
        self._reset_mouse_look_anchor()
        self._pointer_captured = True

    def _release_pointer(self) -> None:
        if not self._pointer_captured and not self._pointer_cursor_hidden:
            return
        if self.mouseGrabber() is self:
            self.releaseMouse()
        if self._pointer_captured:
            self.releaseKeyboard()
        self._show_pointer_cursor()
        self._pointer_captured = False

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        self._capture_pointer()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if not self._mouse_look_enabled():
            return
        global_pos = event.globalPosition().toPoint()
        if self._skip_next_mouse_look:
            self._last_look_global = global_pos
            self._last_look_pos = event.position().toPoint()
            self._skip_next_mouse_look = False
            return
        delta_x = global_pos.x() - self._last_look_global.x()
        delta_y = global_pos.y() - self._last_look_global.y()
        self._last_look_global = global_pos
        self._last_look_pos = event.position().toPoint()
        if delta_x == 0 and delta_y == 0:
            return
        self._apply_mouse_look_delta(delta_x, delta_y)
        self._refresh_camera_hud()
        self.update()

    def _apply_mouse_look_delta(self, delta_x: float, delta_y: float) -> None:
        """Apply pointer delta; horizontal sign matches cursor (move left → look left)."""
        self._azimuth -= delta_x * 0.01
        self._elevation = max(-1.4, min(1.4, self._elevation + delta_y * 0.01))

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        super().mouseReleaseEvent(event)

    def focusInEvent(self, event: QFocusEvent) -> None:  # noqa: N802
        super().focusInEvent(event)

    def enterEvent(self, event: QEnterEvent) -> None:  # noqa: N802
        super().enterEvent(event)

    def _reset_mouse_look_anchor(self) -> None:
        self._last_look_global = QCursor.pos()
        self._last_look_pos = self.mapFromGlobal(self._last_look_global)
        self._skip_next_mouse_look = True

    def focusOutEvent(self, event: QFocusEvent) -> None:  # noqa: N802
        self._release_pointer()
        self._held_movement_keys.clear()
        self._movement_timer.stop()
        super().focusOutEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            if self._pointer_captured or self.hasFocus():
                self._release_pointer()
                self.clearFocus()
                event.accept()
            return
        if event.key() == Qt.Key.Key_R:
            if self.reset_camera_to_default():
                self._refresh_camera_hud()
                event.accept()
                self.update()
            return
        if self._try_adjust_move_speed_key(event.key()):
            event.accept()
            return
        movement_key = self._normalize_movement_key(event.key())
        if movement_key is not None:
            if not event.isAutoRepeat():
                self._held_movement_keys.add(movement_key)
                if not self._movement_timer.isActive():
                    self._movement_elapsed.start()
                    self._movement_timer.start()
                self._apply_movement_for_keys(self._held_movement_keys)
            event.accept()
            self._refresh_camera_hud()
            self.update()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        movement_key = self._normalize_movement_key(event.key())
        if movement_key is not None:
            if not event.isAutoRepeat():
                self._held_movement_keys.discard(movement_key)
                if not self._held_movement_keys:
                    self._movement_timer.stop()
            event.accept()
            return
        super().keyReleaseEvent(event)

    def reset_camera_to_default(self) -> bool:
        """Restore default exterior pose for the current mesh (same azimuth/elevation as load)."""
        if self._mesh is None or self._vertex_count == 0:
            return False
        self._azimuth = 0.7
        self._elevation = 0.45
        self._distance = max(24.0, self._bounds_radius * 2.5)
        self._camera_position = default_exterior_eye(
            self._bounds_center,
            self._bounds_radius,
            self._azimuth,
            self._elevation,
            self._distance,
        )
        self._keep_pose_on_mesh_upload = False
        self._refresh_camera_hud()
        return True

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        if not self.hasFocus() and not self._pointer_captured:
            event.ignore()
            return
        delta_y = event.angleDelta().y()
        if delta_y == 0:
            event.ignore()
            return
        notches = delta_y / float(_WHEEL_ANGLE_DELTA)
        step = notches * ORBIT_CAMERA_MOVE_SPEED_WHEEL_STEP
        self._adjust_move_speed_by(step)
        event.accept()

    def _try_adjust_move_speed_key(self, key: int) -> bool:
        if key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self._adjust_move_speed_by(ORBIT_CAMERA_MOVE_SPEED_WHEEL_STEP)
            return True
        if key == Qt.Key.Key_Minus:
            self._adjust_move_speed_by(-ORBIT_CAMERA_MOVE_SPEED_WHEEL_STEP)
            return True
        return False

    def _adjust_move_speed_by(self, delta: float) -> None:
        clamped = clamp_orbit_camera_move_speed(self._move_speed_multiplier + delta)
        if clamped != self._move_speed_multiplier:
            self._move_speed_multiplier = clamped
            set_orbit_camera_move_speed(clamped)
        self._show_move_speed_feedback()

    def _set_move_speed_multiplier(self, value: float) -> None:
        clamped = clamp_orbit_camera_move_speed(value)
        if clamped != self._move_speed_multiplier:
            self._move_speed_multiplier = clamped
            set_orbit_camera_move_speed(clamped)
        self._show_move_speed_feedback()

    def _show_move_speed_feedback(self) -> None:
        self.move_speed_feedback.emit(
            f"Move speed: {self._move_speed_multiplier:.1f}×",
        )

    def _link_program(
        self,
        vertex_source: str,
        fragment_source: str,
        attributes: tuple[tuple[str, int], ...],
    ) -> QOpenGLShaderProgram:
        program = QOpenGLShaderProgram(self)
        program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex, vertex_source)
        program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment, fragment_source)
        for name, location in attributes:
            program.bindAttributeLocation(name, location)
        program.link()
        return program

    def _projection_near_plane(self) -> float:
        radius = max(self._bounds_radius, 1.0)
        return max(0.001, radius * 0.008)

    def _projection_far_plane(self) -> float:
        radius = max(self._bounds_radius, 1.0)
        return max(500.0, radius * 80.0)

    def _projection_matrix(self) -> QMatrix4x4:
        projection = QMatrix4x4()
        aspect = self._viewport_width / float(self._viewport_height)
        projection.perspective(
            45.0,
            aspect,
            self._projection_near_plane(),
            self._projection_far_plane(),
        )
        return projection

    def _movement_speed_per_second(self) -> float:
        nominal_step = 0.08 * max(self._bounds_radius, 1.0) * self._move_speed_multiplier
        return nominal_step / (_MOVEMENT_REFERENCE_TICK_MS / 1000.0)

    def _movement_step(self) -> float:
        """Nominal distance per 50 ms tick at the current speed multiplier (fc0/fc2b)."""
        return self._movement_speed_per_second() * (_MOVEMENT_REFERENCE_TICK_MS / 1000.0)

    def _movement_distance(self, elapsed_ms: int) -> float:
        return self._movement_speed_per_second() * (max(elapsed_ms, 1) / 1000.0)

    def _normalize_movement_key(self, key: int) -> int | None:
        if key == Qt.Key.Key_Shift:
            return Qt.Key.Key_Shift
        if key in (
            Qt.Key.Key_Left,
            Qt.Key.Key_A,
            Qt.Key.Key_Right,
            Qt.Key.Key_D,
            Qt.Key.Key_Up,
            Qt.Key.Key_W,
            Qt.Key.Key_Down,
            Qt.Key.Key_S,
            Qt.Key.Key_Space,
        ):
            return key
        return None

    def _on_movement_timer_tick(self) -> None:
        if not self._held_movement_keys:
            self._movement_timer.stop()
            return
        elapsed_ms = self._movement_elapsed.restart()
        if elapsed_ms <= 0:
            elapsed_ms = _MOVEMENT_TICK_MS
        step = self._movement_distance(elapsed_ms)
        if self._apply_movement_for_keys(self._held_movement_keys, step=step):
            self._refresh_camera_hud()
            self.update()

    def _apply_keyboard_movement(self, key: int) -> bool:
        movement_key = self._normalize_movement_key(key)
        if movement_key is None:
            return False
        return self._apply_movement_for_keys({movement_key})

    def _apply_movement_for_keys(self, keys: set[int], *, step: float | None = None) -> bool:
        distance = self._movement_step() if step is None else step
        forward_delta = 0.0
        strafe_delta = 0.0
        vertical_delta = 0.0

        for key in keys:
            if key in (Qt.Key.Key_Left, Qt.Key.Key_A):
                strafe_delta -= 1.0
            elif key in (Qt.Key.Key_Right, Qt.Key.Key_D):
                strafe_delta += 1.0
            elif key in (Qt.Key.Key_Up, Qt.Key.Key_W):
                forward_delta += 1.0
            elif key in (Qt.Key.Key_Down, Qt.Key.Key_S):
                forward_delta -= 1.0
            elif key == Qt.Key.Key_Space:
                vertical_delta += 1.0
            elif key == Qt.Key.Key_Shift:
                vertical_delta -= 1.0

        if not (forward_delta or strafe_delta or vertical_delta):
            return False

        if forward_delta:
            self._camera_position = move_along_look(
                self._camera_position,
                self._azimuth,
                self._elevation,
                forward_delta,
                distance,
            )
        if strafe_delta:
            self._camera_position = move_on_plane(
                self._camera_position,
                self._azimuth,
                self._elevation,
                0.0,
                strafe_delta,
                distance,
            )
        if vertical_delta:
            x, y, z = self._camera_position
            self._camera_position = (x, y + vertical_delta * distance, z)
        return True

    def _view_matrix(self) -> QMatrix4x4:
        eye_x, eye_y, eye_z = self._camera_position
        fwd_x, fwd_y, fwd_z = forward_vector(self._azimuth, self._elevation)

        view = QMatrix4x4()
        view.lookAt(
            QVector3D(eye_x, eye_y, eye_z),
            QVector3D(eye_x + fwd_x, eye_y + fwd_y, eye_z + fwd_z),
            QVector3D(0.0, 1.0, 0.0),
        )
        return view

    def _upload_pending_mesh(self) -> None:
        if not self._gl_ready:
            return

        self.makeCurrent()
        mesh = self._pending_mesh
        self._mesh = mesh
        self._vertex_count = 0
        self._textured = False

        if self._atlas_texture is not None:
            self._atlas_texture.destroy()
            self._atlas_texture = None

        if mesh is None or mesh.vertex_count == 0:
            return

        self._bounds_center = mesh.bounds_center
        self._bounds_radius = mesh.bounds_radius
        if not self._keep_pose_on_mesh_upload:
            self._distance = max(self._distance, mesh.bounds_radius * 2.5)
            self._camera_position = default_exterior_eye(
                self._bounds_center,
                self._bounds_radius,
                self._azimuth,
                self._elevation,
                self._distance,
            )

        pos_bytes = array.array("f", mesh.positions).tobytes()

        self._vao.bind()
        self._position_buffer.bind()
        self._position_buffer.allocate(pos_bytes, len(pos_bytes))

        if mesh.uses_texture_atlas and mesh.atlas_rgba is not None:
            normal_bytes = array.array("f", mesh.normals).tobytes()
            tile_rect_bytes = array.array("f", mesh.tile_rects).tobytes()
            self._normal_buffer.bind()
            self._normal_buffer.allocate(normal_bytes, len(normal_bytes))
            self._tile_rect_buffer.bind()
            self._tile_rect_buffer.allocate(tile_rect_bytes, len(tile_rect_bytes))
            self._upload_atlas(mesh)
            self._textured = True
        else:
            col_bytes = array.array("f", mesh.colors).tobytes()
            self._color_buffer.bind()
            self._color_buffer.allocate(col_bytes, len(col_bytes))

        self._vao.release()
        self._vertex_count = mesh.vertex_count
        self._refresh_camera_hud()
        self.update()

    def _upload_atlas(self, mesh: OrbitMeshData) -> None:
        if mesh.atlas_rgba is None or mesh.atlas_width <= 0 or mesh.atlas_height <= 0:
            return

        image = QImage(
            mesh.atlas_rgba,
            mesh.atlas_width,
            mesh.atlas_height,
            QImage.Format.Format_RGBA8888,
        )
        texture = QOpenGLTexture(image)
        texture.setMinificationFilter(QOpenGLTexture.Filter.Linear)
        texture.setMagnificationFilter(QOpenGLTexture.Filter.Linear)
        texture.setWrapMode(QOpenGLTexture.WrapMode.ClampToEdge)
        self._atlas_texture = texture
