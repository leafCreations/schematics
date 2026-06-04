"""Toolbar icons: bundled assets/icons theme, then Qt standard, then drawn fallbacks."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPalette, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QStyle

from ui.icon_theme import icon_from_assets


def toolbar_icon_size() -> QSize:
    return QSize(22, 22)


def panel_icon_size() -> QSize:
    """Compact icons for left-column panels (Layers, Groups rows)."""
    return QSize(18, 18)


def _toolbar_icon_color(*, disabled: bool = False) -> QColor:
    app = QApplication.instance()

    if app is None:
        return QColor(160, 160, 160) if disabled else QColor(80, 80, 80)

    palette = app.palette()
    group = QPalette.ColorGroup.Disabled if disabled else QPalette.ColorGroup.Active

    return palette.color(group, QPalette.ColorRole.ButtonText)


def _tint_pixmap(pixmap: QPixmap, color: QColor) -> QPixmap:
    if pixmap.isNull():
        return pixmap

    tinted = QPixmap(pixmap.size())
    tinted.fill(Qt.GlobalColor.transparent)
    painter = QPainter(tinted)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(tinted.rect(), color)
    painter.end()
    return tinted


def _monochrome_icon(icon: QIcon, *, size: int | None = None) -> QIcon:
    if icon.isNull():
        return icon

    pixel_size = size or toolbar_icon_size().width()
    result = QIcon()

    for disabled in (False, True):
        color = _toolbar_icon_color(disabled=disabled)
        mode = QIcon.Mode.Disabled if disabled else QIcon.Mode.Normal
        pixmap = icon.pixmap(pixel_size, pixel_size, mode, QIcon.State.Off)
        result.addPixmap(_tint_pixmap(pixmap, color), mode, QIcon.State.Off)

    return result


def _theme_icon(*names: str, size: int | None = None) -> QIcon:
    for name in names:
        icon = icon_from_assets(name)

        if not icon.isNull():
            return _monochrome_icon(icon, size=size)

        icon = QIcon.fromTheme(name)

        if not icon.isNull():
            return _monochrome_icon(icon, size=size)

    return QIcon()


def _standard_icon(pixmap: QStyle.StandardPixmap, *, size: int | None = None) -> QIcon:
    app = QApplication.instance()

    if app is None:
        return QIcon()

    return _monochrome_icon(app.style().standardIcon(pixmap), size=size)


def _drawn_icon(
    draw: Callable[[QPainter, int, QColor], None],
    *,
    size: int = 22,
) -> QIcon:
    icon = QIcon()

    for disabled in (False, True):
        color = _toolbar_icon_color(disabled=disabled)
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        draw(painter, size, color)
        painter.end()
        mode = QIcon.Mode.Disabled if disabled else QIcon.Mode.Normal
        icon.addPixmap(pixmap, mode, QIcon.State.Off)

    return icon


def _resolve_icon(
    *,
    theme_names: tuple[str, ...],
    standard: QStyle.StandardPixmap | None = None,
    draw: Callable[[QPainter, int, QColor], None] | None = None,
    size: int | None = None,
) -> QIcon:
    pixel_size = size or toolbar_icon_size().width()
    icon = _theme_icon(*theme_names, size=pixel_size)

    if not icon.isNull():
        return icon

    if standard is not None:
        icon = _standard_icon(standard, size=pixel_size)

        if not icon.isNull():
            return icon

    if draw is not None:
        return _drawn_icon(draw, size=pixel_size)

    return QIcon()


def _draw_plus(painter: QPainter, size: int, color: QColor) -> None:
    pen = QPen(color, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    center = size / 2
    painter.drawLine(center, size * 0.22, center, size * 0.78)
    painter.drawLine(size * 0.22, center, size * 0.78, center)


def _draw_trash(painter: QPainter, size: int, color: QColor) -> None:
    pen = QPen(color, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    w = size * 0.52
    left = (size - w) / 2
    top = size * 0.34
    height = size * 0.46
    painter.drawRect(left, top, w, height)
    lid_w = w * 0.72
    lid_left = (size - lid_w) / 2
    painter.drawLine(lid_left, top, lid_left + lid_w, top)
    painter.drawLine(size * 0.38, size * 0.24, size * 0.62, size * 0.24)


def _draw_copy(painter: QPainter, size: int, color: QColor) -> None:
    pen = QPen(color, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    back = size * 0.42
    painter.drawRoundedRect(size * 0.36, size * 0.18, back, back, 2, 2)
    painter.drawRoundedRect(size * 0.18, size * 0.34, back, back, 2, 2)


def _draw_paste(painter: QPainter, size: int, color: QColor) -> None:
    pen = QPen(color, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    board_w = size * 0.46
    board_left = (size - board_w) / 2
    painter.drawRoundedRect(board_left, size * 0.3, board_w, size * 0.5, 2, 2)
    painter.drawLine(size * 0.34, size * 0.22, size * 0.66, size * 0.22)
    painter.drawLine(size * 0.42, size * 0.44, size * 0.58, size * 0.44)
    painter.drawLine(size * 0.42, size * 0.54, size * 0.58, size * 0.54)


def _draw_eraser(painter: QPainter, size: int, color: QColor) -> None:
    pen = QPen(color, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.drawLine(size * 0.2, size * 0.72, size * 0.72, size * 0.2)
    painter.drawLine(size * 0.28, size * 0.8, size * 0.8, size * 0.28)


def _draw_save(painter: QPainter, size: int, color: QColor) -> None:
    pen = QPen(color, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    body_w = size * 0.5
    body_left = (size - body_w) / 2
    painter.drawRect(body_left, size * 0.22, body_w, size * 0.58)
    slot_w = body_w * 0.42
    painter.drawRect((size - slot_w) / 2, size * 0.14, slot_w, size * 0.14)
    inner = size * 0.22
    painter.drawRect((size - inner) / 2, size * 0.42, inner, inner)


def layer_add_icon(*, size: int | None = None) -> QIcon:
    return _resolve_icon(
        theme_names=("list-add", "document-new", "insert-object"),
        standard=QStyle.StandardPixmap.SP_FileDialogNewFolder,
        draw=_draw_plus,
        size=size,
    )


def layer_delete_icon(*, size: int | None = None) -> QIcon:
    return _resolve_icon(
        theme_names=("edit-delete", "edit-delete-remove", "list-remove"),
        standard=QStyle.StandardPixmap.SP_TrashIcon,
        draw=_draw_trash,
        size=size,
    )


def layer_copy_icon(*, size: int | None = None) -> QIcon:
    return _resolve_icon(theme_names=("edit-copy",), draw=_draw_copy, size=size)


def layer_paste_icon(*, size: int | None = None) -> QIcon:
    return _resolve_icon(theme_names=("edit-paste",), draw=_draw_paste, size=size)


def layer_eraser_icon(*, size: int | None = None) -> QIcon:
    pixel_size = size or toolbar_icon_size().width()
    icon = icon_from_assets("draw-eraser", prefer_symbolic=False)

    if not icon.isNull():
        return _monochrome_icon(icon, size=pixel_size)

    return _drawn_icon(_draw_eraser, size=pixel_size)


def layer_save_icon(*, size: int | None = None) -> QIcon:
    return _resolve_icon(
        theme_names=("document-save", "document-save-symbolic", "media-floppy"),
        standard=QStyle.StandardPixmap.SP_DialogSaveButton,
        draw=_draw_save,
        size=size,
    )


def _draw_arrow_up(painter: QPainter, size: int, color: QColor) -> None:
    pen = QPen(color, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    center = size / 2
    painter.drawLine(center, size * 0.28, center, size * 0.68)
    painter.drawLine(size * 0.32, size * 0.42, center, size * 0.26)
    painter.drawLine(size * 0.68, size * 0.42, center, size * 0.26)


def _draw_arrow_down(painter: QPainter, size: int, color: QColor) -> None:
    pen = QPen(color, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    center = size / 2
    painter.drawLine(center, size * 0.32, center, size * 0.72)
    painter.drawLine(size * 0.32, size * 0.58, center, size * 0.74)
    painter.drawLine(size * 0.68, size * 0.58, center, size * 0.74)


def layer_move_up_icon(*, size: int | None = None) -> QIcon:
    return _resolve_icon(
        theme_names=("go-up", "arrow-up", "up"),
        standard=QStyle.StandardPixmap.SP_ArrowUp,
        draw=_draw_arrow_up,
        size=size,
    )


def layer_visible_off_icon(*, size: int | None = None) -> QIcon:
    pixel_size = size or toolbar_icon_size().width()
    icon = icon_from_assets("layer-visible-off", prefer_symbolic=False)

    if not icon.isNull():
        return _monochrome_icon(icon, size=pixel_size)

    return QIcon()


def layer_move_down_icon(*, size: int | None = None) -> QIcon:
    return _resolve_icon(
        theme_names=("go-down", "arrow-down", "down"),
        standard=QStyle.StandardPixmap.SP_ArrowDown,
        draw=_draw_arrow_down,
        size=size,
    )
