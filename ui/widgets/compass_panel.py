"""Top-down compass for structure and site grids (+x east, +z south)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QGroupBox, QLabel, QWidget

from helpers.paths import UI_ASSETS_FOLDER
from ui.widgets.panel_header import PANEL_COMPASS_MAX_HEIGHT, create_titled_panel_layout
from ui.widgets.panel_tool_button import make_panel_close_button

_COMPASS_SVG = UI_ASSETS_FOLDER / "compass.svg"
_ROSE_SIZE = 80


class CompassRoseWidget(QWidget):
    """Compass rose aligned with editor grids (north up, east right)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(_ROSE_SIZE, _ROSE_SIZE)
        self._pixmap = self._load_pixmap()

    @staticmethod
    def _load_pixmap() -> QPixmap | None:
        if not _COMPASS_SVG.is_file():
            return None

        pixmap = QPixmap(str(_COMPASS_SVG))

        if pixmap.isNull():
            return None

        return pixmap.scaled(
            _ROSE_SIZE,
            _ROSE_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def paintEvent(self, event) -> None:  # noqa: N802
        if self._pixmap is not None and not self._pixmap.isNull():
            painter = QPainter(self)
            painter.drawPixmap(0, 0, self._pixmap)
            painter.end()
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        _paint_compass_rose(painter, self.width(), self.height())
        painter.end()


def _paint_compass_rose(painter: QPainter, width: int, height: int) -> None:
    center_x = width / 2
    center_y = height / 2
    radius = min(width, height) * 0.45

    painter.setPen(QPen(QColor("#666666"), 1.5))
    painter.setBrush(QColor("#fafafa"))
    painter.drawEllipse(
        int(center_x - radius),
        int(center_y - radius),
        int(radius * 2),
        int(radius * 2),
    )

    painter.setPen(QPen(QColor("#cccccc"), 1))
    painter.drawLine(
        int(center_x), int(center_y - radius + 4), int(center_x), int(center_y + radius - 4)
    )
    painter.drawLine(
        int(center_x - radius + 4), int(center_y), int(center_x + radius - 4), int(center_y)
    )

    north = QPolygonF(
        [
            (center_x, center_y - radius + 6),
            (center_x + 6, center_y - 8),
            (center_x, center_y - 14),
            (center_x - 6, center_y - 8),
        ]
    )
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#333333"))
    painter.drawPolygon(north)

    south = QColor("#aaaaaa")
    for points in (
        [
            (center_x, center_y + radius - 6),
            (center_x + 6, center_y + 8),
            (center_x, center_y + 14),
            (center_x - 6, center_y + 8),
        ],
        [
            (center_x + radius - 6, center_y),
            (center_x + 8, center_y + 6),
            (center_x + 14, center_y),
            (center_x + 8, center_y - 6),
        ],
        [
            (center_x - radius + 6, center_y),
            (center_x - 8, center_y + 6),
            (center_x - 14, center_y),
            (center_x - 8, center_y - 6),
        ],
    ):
        painter.setBrush(south)
        painter.drawPolygon(QPolygonF(points))

    font = QFont()
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor("#222222"))
    painter.drawText(int(center_x - 6), 14, "N")

    font.setBold(False)
    font.setPointSize(8)
    painter.setFont(font)
    painter.setPen(QColor("#555555"))
    painter.drawText(int(center_x - 4), height - 4, "S")
    painter.drawText(width - 14, int(center_y + 4), "E")
    painter.drawText(4, int(center_y + 4), "W")


class CompassPanel(QGroupBox):
    """Compass reference for top-down structure and site views."""

    close_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        close_button = make_panel_close_button(
            tooltip="Hide compass",
            clicked=self.close_requested.emit,
        )

        layout = create_titled_panel_layout(self, "Compass", [close_button])
        layout.setSpacing(4)

        rose = CompassRoseWidget()
        hint = QLabel("Top of grid = north\n+x → east, +z ↓ south")
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #ffffff; font-size: 11px;")

        layout.addWidget(rose, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(hint)

        self.setMaximumHeight(PANEL_COMPASS_MAX_HEIGHT)
