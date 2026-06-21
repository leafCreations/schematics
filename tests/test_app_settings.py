from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ui import app_settings
from ui.app_settings import EditorSettings, load_editor_settings, user_settings_path


@pytest.fixture(autouse=True)
def isolated_editor_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    user_file = tmp_path / "editor_settings.yaml"
    monkeypatch.setenv(app_settings._ENV_OVERRIDE, str(user_file))
    app_settings.reset_editor_settings_cache()
    yield
    app_settings.reset_editor_settings_cache()


def test_defaults_when_no_user_file():
    settings = load_editor_settings(force_reload=True)

    assert settings.block_tooltips is True
    assert settings.grid_axis_labels is True
    assert settings.panel_compass is True
    assert settings.panel_materials is True
    assert settings.panel_structure_settings is True
    assert settings.recent_structures == []
    assert user_settings_path().is_file()


def test_user_file_overrides_bundled_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    user_file = tmp_path / "custom.yaml"
    monkeypatch.setenv(app_settings._ENV_OVERRIDE, str(user_file))
    app_settings.reset_editor_settings_cache()

    user_file.write_text(
        yaml.safe_dump(
            {
                "display": {"grid_axis_labels": False},
                "panels": {"materials": False, "compass": False},
            }
        ),
        encoding="utf-8",
    )

    settings = load_editor_settings(force_reload=True)

    assert settings.grid_axis_labels is False
    assert settings.panel_materials is False
    assert settings.panel_compass is False
    assert settings.block_tooltips is True
    assert settings.panel_structure_settings is True


def test_save_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    user_file = tmp_path / "editor_settings.yaml"
    monkeypatch.setenv(app_settings._ENV_OVERRIDE, str(user_file))
    app_settings.reset_editor_settings_cache()

    app_settings.sync_editor_settings_from_ui(
        block_tooltips=False,
        grid_axis_labels=True,
        panel_compass=False,
        panel_materials=True,
        panel_structure_settings=False,
    )

    app_settings.reset_editor_settings_cache()
    settings = load_editor_settings(force_reload=True)

    assert settings == EditorSettings(
        block_tooltips=False,
        grid_axis_labels=True,
        panel_compass=False,
        panel_materials=True,
        panel_structure_settings=False,
    )


def test_recent_structures_round_trip_and_clear():
    app_settings.add_recent_structure("residence", 1)
    app_settings.add_recent_structure("well", 2)
    app_settings.add_recent_structure("residence", 1)

    app_settings.reset_editor_settings_cache()
    settings = load_editor_settings(force_reload=True)
    assert settings.recent_structures == [("residence", 1), ("well", 2)]

    app_settings.clear_recent_structures()
    app_settings.reset_editor_settings_cache()
    assert load_editor_settings(force_reload=True).recent_structures == []


def test_sync_editor_settings_from_ui_preserves_recent_structures():
    app_settings.add_recent_structure("residence", 1)
    app_settings.sync_editor_settings_from_ui(
        block_tooltips=True,
        grid_axis_labels=False,
        panel_compass=True,
        panel_materials=False,
        panel_structure_settings=True,
    )

    app_settings.reset_editor_settings_cache()
    settings = load_editor_settings(force_reload=True)
    assert settings.recent_structures == [("residence", 1)]
