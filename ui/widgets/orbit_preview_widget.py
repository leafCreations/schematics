"""OpenGL orbit camera widget for 3D greedy-meshed preview."""

from __future__ import annotations

import array
import math

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QImage, QMatrix4x4, QMouseEvent, QVector3D, QWheelEvent
from PySide6.QtOpenGL import (
    QOpenGLBuffer,
    QOpenGLShader,
    QOpenGLShaderProgram,
    QOpenGLTexture,
    QOpenGLVertexArrayObject,
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QLabel, QSizePolicy

from helpers.orbit_mesh import OrbitMeshData

_GL_FLOAT = 0x1406
_GL_COLOR_BUFFER_BIT = 0x00004000
_GL_DEPTH_BUFFER_BIT = 0x00000100
_GL_DEPTH_TEST = 0x0B71
_GL_TRIANGLES = 0x0004

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


class OrbitPreviewWidget(QOpenGLWidget):
    """Orbit view of a combined greedy mesh with optional catalog texture atlas."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(240, 180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

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
        self._dragging = False
        self._last_pos = QPoint()

        self._color_program: QOpenGLShaderProgram | None = None
        self._textured_program: QOpenGLShaderProgram | None = None
        self._vao = QOpenGLVertexArrayObject(self)
        self._position_buffer = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        self._color_buffer = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        self._normal_buffer = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        self._tile_rect_buffer = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        self._atlas_texture: QOpenGLTexture | None = None
        self._gl_ready = False

        self._overlay = QLabel("Drag to orbit. Scroll to zoom.", self)
        self._overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._overlay.setStyleSheet("color: #888; background: transparent;")
        self._overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def has_mesh(self) -> bool:
        return self._mesh is not None and self._mesh.vertex_count > 0

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
            self._overlay.setText("Drag to orbit. Scroll to zoom.")
            self._overlay.setVisible(False)
        self.update()

    def set_status_message(self, message: str) -> None:
        self._overlay.setText(message)
        self._overlay.setVisible(True)
        self.update()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._overlay.setGeometry(self.rect())

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
            return

        program = self._textured_program if self._textured else self._color_program
        if program is None:
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

    def resizeGL(self, width: int, height: int) -> None:  # noqa: N802
        self._viewport_width = max(width, 1)
        self._viewport_height = max(height, 1)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._last_pos = event.position().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if not self._dragging:
            return
        pos = event.position().toPoint()
        delta_x = pos.x() - self._last_pos.x()
        delta_y = pos.y() - self._last_pos.y()
        self._last_pos = pos
        self._azimuth += delta_x * 0.01
        self._elevation = max(-1.4, min(1.4, self._elevation + delta_y * 0.01))
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        delta = event.angleDelta().y()
        if delta == 0:
            return
        factor = 0.9 if delta > 0 else 1.1
        min_distance = max(self._bounds_radius * 1.5, 4.0)
        self._distance = max(min_distance, min(400.0, self._distance * factor))
        self.update()

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

    def _projection_matrix(self) -> QMatrix4x4:
        projection = QMatrix4x4()
        aspect = self._viewport_width / float(self._viewport_height)
        projection.perspective(45.0, aspect, 0.1, 2000.0)
        return projection

    def _view_matrix(self) -> QMatrix4x4:
        cx, cy, cz = self._bounds_center
        radius = max(self._bounds_radius, 1.0)
        distance = max(self._distance, radius * 1.8)

        eye_x = cx + distance * math.cos(self._elevation) * math.sin(self._azimuth)
        eye_y = cy + distance * math.sin(self._elevation)
        eye_z = cz + distance * math.cos(self._elevation) * math.cos(self._azimuth)

        view = QMatrix4x4()
        view.lookAt(
            QVector3D(eye_x, eye_y, eye_z),
            QVector3D(cx, cy, cz),
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
        self._distance = max(self._distance, mesh.bounds_radius * 2.5)

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
