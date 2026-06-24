from pathlib import Path

import pytest
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QSizePolicy

pytest.importorskip("PySide6")

import helpers.constants as constants
from renderers.registry import PREVIEW_RENDER_REGISTRY
from ui.widgets.preview_panel import _PREVIEW_COMBO_MAX_WIDTH, PreviewPanel


@pytest.fixture(scope="module")
def qapp():
    application = QApplication.instance() or QApplication([])
    yield application


def test_preview_panel_dropdown_lists_render_types(qapp):
    panel = PreviewPanel()

    assert panel._render_combo.count() == len(PREVIEW_RENDER_REGISTRY)
    assert panel._render_combo.itemText(0) == "Top Down"
    assert panel._render_combo.itemText(1) == "Structure Facades"
    assert panel._render_combo.itemText(2) == "Site Facades"
    assert panel._render_combo.itemText(3) == "Site Top Down"
    assert panel._render_combo.itemText(4) == "Materials List"
    assert panel.selected_render() == constants.RENDER_TOP_VIEW
    assert panel._render_combo.maximumWidth() == _PREVIEW_COMBO_MAX_WIDTH
    assert panel._render_combo.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Maximum


def test_preview_panel_group_combo_hidden_for_single_group(qapp):
    panel = PreviewPanel()
    panel.set_groups(["Floor 1"])

    assert panel.selected_group() == "Floor 1"
    assert not panel._group_combo.isVisible()


def test_preview_panel_group_combo_visible_for_multiple_groups(qapp):
    panel = PreviewPanel()
    panel.set_groups(["Floor 1", "Floor 2"])
    panel.show()

    assert panel._group_combo.isVisible()
    assert panel._group_combo.count() == 2


def test_preview_panel_emits_preview_group_changed(qapp):
    panel = PreviewPanel()
    panel.set_groups(["Floor 1", "Floor 2"])
    requested: list[str] = []
    panel.preview_group_changed.connect(requested.append)

    panel._group_combo.setCurrentIndex(1)

    assert requested == ["Floor 2"]


def test_preview_panel_group_combo_hidden_for_structure_facades(qapp):
    panel = PreviewPanel()
    panel.set_groups(["Floor 1", "Floor 2"])
    panel.show()

    facade_index = panel._render_combo.findData(constants.RENDER_STRUCTURE_FACADES)
    panel._render_combo.setCurrentIndex(facade_index)

    assert not panel._group_combo.isVisible()


def test_preview_panel_group_combo_hidden_for_site_facades(qapp):
    panel = PreviewPanel()
    panel.set_groups(["Floor 1", "Floor 2"])
    panel.show()

    site_index = panel._render_combo.findData(constants.RENDER_SITE_FACADES)
    panel._render_combo.setCurrentIndex(site_index)

    assert not panel._group_combo.isVisible()


def test_preview_panel_group_combo_hidden_for_site_top_down(qapp):
    panel = PreviewPanel()
    panel.set_groups(["Floor 1", "Floor 2"])
    panel.show()

    site_topdown_index = panel._render_combo.findData(constants.RENDER_PATH)
    panel._render_combo.setCurrentIndex(site_topdown_index)

    assert not panel._group_combo.isVisible()


def test_preview_panel_group_combo_hidden_for_materials_list(qapp):
    panel = PreviewPanel()
    panel.set_groups(["Floor 1", "Floor 2"])
    panel.show()

    materials_index = panel._render_combo.findData(constants.RENDER_MATERIALS)
    panel._render_combo.setCurrentIndex(materials_index)

    assert not panel._group_combo.isVisible()


def test_preview_panel_gallery_navigation(qapp, tmp_path: Path):
    paths: list[Path] = []
    for index in range(3):
        image_path = tmp_path / f"Structure_floor_y{index}.png"
        pixmap = QPixmap(48, 32)
        pixmap.fill()
        assert pixmap.save(str(image_path))
        paths.append(image_path)

    panel = PreviewPanel()
    panel.set_gallery(paths, select_index=0)

    assert panel._current_index == 0
    assert len(panel._thumbnail_buttons) == 3
    assert panel._prev_button.isEnabled() is False
    assert panel._next_button.isEnabled() is True

    panel._show_next_image()
    assert panel._current_index == 1

    panel._on_thumbnail_clicked(2)
    assert panel._current_index == 2


def test_preview_panel_selected_thumbnail_is_checked(qapp, tmp_path: Path):
    paths: list[Path] = []
    for index in range(3):
        image_path = tmp_path / f"Structure_floor_y{index}.png"
        pixmap = QPixmap(48, 32)
        pixmap.fill()
        assert pixmap.save(str(image_path))
        paths.append(image_path)

    panel = PreviewPanel()
    panel.set_gallery(paths, select_index=0)

    assert panel._thumbnail_buttons[0].isChecked()
    assert not panel._thumbnail_buttons[1].isChecked()

    panel._show_next_image()
    assert panel._thumbnail_buttons[1].isChecked()
    assert not panel._thumbnail_buttons[0].isChecked()

    assert "border" in panel._thumbnail_buttons[0].styleSheet()


def test_preview_panel_show_preview_shows_updated_timestamp_only(qapp, tmp_path: Path):
    image_path = tmp_path / "preview.png"
    pixmap = QPixmap(32, 24)
    pixmap.fill()
    assert pixmap.save(str(image_path))

    panel = PreviewPanel()
    panel.show_preview(image_path)

    updated_text = panel._updated_label.text()
    assert updated_text.startswith("Updated ")
    assert "preview.png" not in updated_text
    assert str(tmp_path) not in updated_text
    assert not panel._caption.isVisible()
    assert not panel._image_label.pixmap().isNull()


def test_preview_panel_clear(qapp):
    panel = PreviewPanel()
    panel.clear("No preview yet.")

    assert panel._caption.text() == "No preview yet."
    assert panel._updated_label.text() == ""
    assert panel._image_label.pixmap() is None or panel._image_label.pixmap().isNull()
