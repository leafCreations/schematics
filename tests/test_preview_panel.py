from pathlib import Path

import pytest
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QSizePolicy

pytest.importorskip("PySide6")

import helpers.constants as constants
from renderers.registry import PREVIEW_RENDER_REGISTRY
from ui import app_settings
from ui.app_settings import load_editor_settings
from ui.widgets.preview_panel import (
    _PREVIEW_COMBO_MAX_WIDTH,
    PreviewPanel,
    clamp_zoom_factor,
    zoom_percent,
)


@pytest.fixture(scope="module")
def qapp():
    application = QApplication.instance() or QApplication([])
    yield application


@pytest.fixture(autouse=True)
def isolated_preview_editor_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    user_file = tmp_path / "editor_settings.yaml"
    monkeypatch.setenv(app_settings._ENV_OVERRIDE, str(user_file))
    app_settings.reset_editor_settings_cache()
    yield
    app_settings.reset_editor_settings_cache()


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
    assert panel._preview_toolbar._prev_button.isEnabled() is False
    assert panel._preview_toolbar._next_button.isEnabled() is True

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


def test_clamp_zoom_factor_limits_range():
    assert clamp_zoom_factor(0.1) == 0.25
    assert clamp_zoom_factor(10.0) == 4.0
    assert clamp_zoom_factor(1.0) == 1.0


def test_zoom_percent_rounds():
    assert zoom_percent(1.0) == 100
    assert zoom_percent(1.256) == 126


def test_preview_panel_default_zoom_is_100_percent(qapp):
    panel = PreviewPanel()
    assert panel.zoom_factor() == 1.0
    assert panel._preview_toolbar._zoom_label.text() == "100%"


def test_preview_panel_zoom_scales_pixmap(qapp, tmp_path: Path):
    image_path = tmp_path / "preview.png"
    pixmap = QPixmap(100, 50)
    pixmap.fill()
    assert pixmap.save(str(image_path))

    panel = PreviewPanel()
    panel.show_preview(image_path)

    assert panel._image_label.pixmap().width() == 100

    panel._set_zoom_factor(2.0)
    assert panel.zoom_factor() == 2.0
    assert panel._preview_toolbar._zoom_label.text() == "200%"
    assert panel._image_label.pixmap().width() == 200


def test_preview_panel_gallery_keeps_zoom_across_images(qapp, tmp_path: Path):
    paths: list[Path] = []
    for index in range(2):
        image_path = tmp_path / f"Structure_floor_y{index}.png"
        pixmap = QPixmap(40, 40)
        pixmap.fill()
        assert pixmap.save(str(image_path))
        paths.append(image_path)

    panel = PreviewPanel()
    panel.set_gallery(paths, select_index=0)
    panel._set_zoom_factor(1.5)

    panel._show_next_image()
    assert panel.zoom_factor() == 1.5
    assert panel._preview_toolbar._zoom_label.text() == "150%"


def test_preview_panel_reset_zoom_to_default(qapp, tmp_path: Path):
    image_path = tmp_path / "preview.png"
    pixmap = QPixmap(32, 32)
    pixmap.fill()
    assert pixmap.save(str(image_path))

    panel = PreviewPanel()
    panel.show_preview(image_path)
    panel._set_zoom_factor(2.0)
    panel.reset_zoom_to_default()

    assert panel.zoom_factor() == 1.0
    assert panel._preview_toolbar._zoom_label.text() == "100%"
    assert panel._preview_toolbar._zoom_slider.value() == 100
    assert panel._image_label.pixmap().width() == 32


def test_preview_panel_restores_saved_zoom_on_init(qapp, monkeypatch):
    monkeypatch.setattr("ui.widgets.preview_panel.preview_zoom_percent", lambda: 150)

    panel = PreviewPanel()
    assert panel.zoom_factor() == 1.5
    assert panel._preview_toolbar._zoom_label.text() == "150%"
    assert panel._preview_toolbar._zoom_slider.value() == 150


def test_preview_panel_restore_saved_zoom(qapp, monkeypatch):
    monkeypatch.setattr("ui.widgets.preview_panel.preview_zoom_percent", lambda: 125)

    panel = PreviewPanel()
    panel._set_zoom_factor(2.0)
    panel.restore_saved_zoom()

    assert panel.zoom_factor() == 1.25
    assert panel._preview_toolbar._zoom_slider.value() == 125


def test_preview_panel_slider_updates_zoom(qapp, tmp_path: Path):
    image_path = tmp_path / "preview.png"
    pixmap = QPixmap(100, 50)
    pixmap.fill()
    assert pixmap.save(str(image_path))

    panel = PreviewPanel()
    panel.show_preview(image_path)

    panel._preview_toolbar._zoom_slider.setValue(200)
    assert panel.zoom_factor() == 2.0
    assert panel._preview_toolbar._zoom_label.text() == "200%"
    assert panel._image_label.pixmap().width() == 200


def test_preview_panel_wheel_updates_slider(qapp, tmp_path: Path):
    image_path = tmp_path / "preview.png"
    pixmap = QPixmap(100, 50)
    pixmap.fill()
    assert pixmap.save(str(image_path))

    panel = PreviewPanel()
    panel.show_preview(image_path)
    panel._set_zoom_factor(1.75)

    assert panel._preview_toolbar._zoom_slider.value() == 175


def test_preview_panel_zoom_persists_to_settings(qapp, tmp_path: Path, monkeypatch):
    from ui import app_settings

    user_file = tmp_path / "editor_settings.yaml"
    monkeypatch.setenv(app_settings._ENV_OVERRIDE, str(user_file))
    app_settings.reset_editor_settings_cache()

    image_path = tmp_path / "preview.png"
    pixmap = QPixmap(32, 32)
    pixmap.fill()
    assert pixmap.save(str(image_path))

    panel = PreviewPanel()
    panel.show_preview(image_path)
    panel._set_zoom_factor(1.5)

    app_settings.reset_editor_settings_cache()
    assert load_editor_settings(force_reload=True).preview_zoom_percent == 150


def test_preview_panel_zoom_in_and_out(qapp, tmp_path: Path):
    image_path = tmp_path / "preview.png"
    pixmap = QPixmap(100, 50)
    pixmap.fill()
    assert pixmap.save(str(image_path))

    panel = PreviewPanel()
    panel.show_preview(image_path)

    panel.zoom_in()
    assert panel.zoom_factor() > 1.0
    factor_after_in = panel.zoom_factor()

    panel.zoom_out()
    assert panel.zoom_factor() < factor_after_in
    assert panel.zoom_factor() == pytest.approx(1.0, rel=0.01)


def test_preview_toolbar_reset_resets_zoom(qapp, tmp_path: Path, monkeypatch):
    from ui import app_settings

    user_file = tmp_path / "editor_settings.yaml"
    monkeypatch.setenv(app_settings._ENV_OVERRIDE, str(user_file))
    app_settings.reset_editor_settings_cache()

    image_path = tmp_path / "preview.png"
    pixmap = QPixmap(32, 32)
    pixmap.fill()
    assert pixmap.save(str(image_path))

    panel = PreviewPanel()
    panel.show_preview(image_path)
    panel._set_zoom_factor(2.0)

    panel._preview_toolbar.reset_clicked.emit()

    assert panel.zoom_factor() == 1.0
    assert panel._preview_toolbar._zoom_slider.value() == 100
    app_settings.reset_editor_settings_cache()
    assert load_editor_settings(force_reload=True).preview_zoom_percent == 100


def test_preview_panel_clear(qapp):
    panel = PreviewPanel()
    panel.clear("No preview yet.")

    assert panel._caption.text() == "No preview yet."
    assert panel._updated_label.text() == ""
    assert panel._image_label.pixmap() is None or panel._image_label.pixmap().isNull()


def test_preview_panel_2d_3d_toggle_defaults_to_2d(qapp):
    panel = PreviewPanel()
    panel.show()
    modes: list[str] = []
    panel.view_mode_changed.connect(modes.append)

    assert panel.is_3d_mode() is False
    assert panel._mode_2d_button.isChecked()
    assert panel._render_combo.isVisible()

    panel._mode_3d_button.click()

    assert panel.is_3d_mode() is True
    assert modes == ["3d"]
    assert not panel._preview_toolbar.isVisible()
