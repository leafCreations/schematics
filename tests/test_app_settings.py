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
    assert settings.preview_zoom_percent == 100
    assert settings.orbit_camera_poses == {}
    assert settings.orbit_camera_hud_visible is True
    assert settings.orbit_camera_hud_placement == "top_right"
    assert settings.orbit_camera_hud_crosshair_visible is True
    assert settings.orbit_camera_move_speed == pytest.approx(0.65)
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
        preview_zoom_percent=100,
        orbit_camera_poses={},
    )


def test_preview_zoom_percent_defaults_and_clamp():
    from ui.app_settings import clamp_preview_zoom_percent

    assert clamp_preview_zoom_percent(100) == 100
    assert clamp_preview_zoom_percent(10) == 25
    assert clamp_preview_zoom_percent(500) == 400
    assert clamp_preview_zoom_percent("bad") == 100


def test_preview_zoom_percent_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    user_file = tmp_path / "editor_settings.yaml"
    monkeypatch.setenv(app_settings._ENV_OVERRIDE, str(user_file))
    app_settings.reset_editor_settings_cache()

    user_file.write_text(
        yaml.safe_dump({"viewer": {"preview_zoom_percent": 175}}),
        encoding="utf-8",
    )

    settings = load_editor_settings(force_reload=True)
    assert settings.preview_zoom_percent == 175

    from ui.editor_prefs import set_preview_zoom_percent

    set_preview_zoom_percent(200)
    app_settings.reset_editor_settings_cache()
    assert load_editor_settings(force_reload=True).preview_zoom_percent == 200


def test_sync_preserves_preview_zoom_percent():
    from ui.editor_prefs import set_preview_zoom_percent

    set_preview_zoom_percent(150)
    app_settings.sync_editor_settings_from_ui(
        block_tooltips=True,
        grid_axis_labels=False,
        panel_compass=True,
        panel_materials=False,
        panel_structure_settings=True,
    )

    app_settings.reset_editor_settings_cache()
    settings = load_editor_settings(force_reload=True)
    assert settings.preview_zoom_percent == 150


def test_viewer_settings_round_trip_orbit_camera_pose():
    from ui.app_settings import OrbitCameraPose, orbit_camera_pose_storage_key
    from ui.editor_prefs import orbit_camera_pose, set_orbit_camera_pose

    pose = OrbitCameraPose(position=(1.5, 8.0, -3.25), azimuth=1.2, elevation=0.35)
    set_orbit_camera_pose("residence", 1, pose)

    app_settings.reset_editor_settings_cache()
    loaded = load_editor_settings(force_reload=True)
    key = orbit_camera_pose_storage_key("residence", 1)
    assert loaded.orbit_camera_poses[key] == pose
    assert orbit_camera_pose("residence", 1) == pose

    raw = yaml.safe_load(user_settings_path().read_text(encoding="utf-8"))
    entry = raw["viewer"]["orbit_camera_poses"]["residence/1"]
    assert entry["azimuth"] == pytest.approx(1.2)
    assert entry["elevation"] == pytest.approx(0.35)
    assert entry["position"] == pytest.approx([1.5, 8.0, -3.25])


def test_orbit_camera_poses_are_isolated_per_stage():
    from ui.app_settings import OrbitCameraPose
    from ui.editor_prefs import orbit_camera_pose, set_orbit_camera_pose

    pose_stage1 = OrbitCameraPose(position=(1.0, 2.0, 3.0), azimuth=0.1, elevation=0.2)
    pose_stage2 = OrbitCameraPose(position=(4.0, 5.0, 6.0), azimuth=0.9, elevation=-0.3)
    set_orbit_camera_pose("residence", 1, pose_stage1)
    set_orbit_camera_pose("residence", 2, pose_stage2)

    app_settings.reset_editor_settings_cache()
    assert orbit_camera_pose("residence", 1) == pose_stage1
    assert orbit_camera_pose("residence", 2) == pose_stage2


def test_orbit_camera_pose_invalid_yaml_ignored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    user_file = tmp_path / "editor_settings.yaml"
    monkeypatch.setenv(app_settings._ENV_OVERRIDE, str(user_file))
    app_settings.reset_editor_settings_cache()

    user_file.write_text(
        yaml.safe_dump(
            {
                "viewer": {
                    "orbit_camera_poses": {
                        "residence/1": {
                            "azimuth": 0.5,
                            "elevation": 99.0,
                            "position": [1.0, 2.0, 3.0],
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    settings = load_editor_settings(force_reload=True)
    assert settings.orbit_camera_poses == {}


def test_sync_preserves_orbit_camera_pose():
    from ui.app_settings import OrbitCameraPose
    from ui.editor_prefs import orbit_camera_pose, set_orbit_camera_pose

    pose = OrbitCameraPose(position=(0.0, 12.0, 0.0), azimuth=0.7, elevation=0.45)
    set_orbit_camera_pose("residence", 1, pose)
    app_settings.sync_editor_settings_from_ui(
        block_tooltips=True,
        grid_axis_labels=False,
        panel_compass=True,
        panel_materials=False,
        panel_structure_settings=True,
    )

    app_settings.reset_editor_settings_cache()
    assert orbit_camera_pose("residence", 1) == pose


def test_orbit_camera_hud_pref_default_true():
    from ui.editor_prefs import orbit_camera_hud_visible, set_orbit_camera_hud_visible

    assert orbit_camera_hud_visible() is True

    set_orbit_camera_hud_visible(False)
    app_settings.reset_editor_settings_cache()
    assert load_editor_settings(force_reload=True).orbit_camera_hud_visible is False

    raw = yaml.safe_load(user_settings_path().read_text(encoding="utf-8"))
    assert raw["viewer"]["orbit_camera_hud"] is False


def test_orbit_camera_move_speed_pref_round_trip():
    from ui.editor_prefs import orbit_camera_move_speed, set_orbit_camera_move_speed

    assert orbit_camera_move_speed() == pytest.approx(0.65)

    set_orbit_camera_move_speed(1.5)
    app_settings.reset_editor_settings_cache()
    assert load_editor_settings(force_reload=True).orbit_camera_move_speed == pytest.approx(1.0)

    raw = yaml.safe_load(user_settings_path().read_text(encoding="utf-8"))
    assert raw["viewer"]["orbit_camera_move_speed"] == pytest.approx(1.0)


def test_orbit_camera_hud_placement_and_crosshair_round_trip():
    from ui.editor_prefs import (
        orbit_camera_hud_crosshair_visible,
        orbit_camera_hud_placement,
        set_orbit_camera_hud_crosshair_visible,
        set_orbit_camera_hud_placement,
    )

    assert orbit_camera_hud_placement() == "top_right"
    assert orbit_camera_hud_crosshair_visible() is True

    set_orbit_camera_hud_placement("bottom_center")
    set_orbit_camera_hud_crosshair_visible(False)
    app_settings.reset_editor_settings_cache()
    settings = load_editor_settings(force_reload=True)
    assert settings.orbit_camera_hud_placement == "bottom_center"
    assert settings.orbit_camera_hud_crosshair_visible is False

    raw = yaml.safe_load(user_settings_path().read_text(encoding="utf-8"))
    assert raw["viewer"]["orbit_camera_hud_placement"] == "bottom_center"
    assert raw["viewer"]["orbit_camera_hud_crosshair"] is False


def test_clamp_orbit_camera_move_speed():
    from ui.app_settings import (
        ORBIT_CAMERA_MOVE_SPEED_WHEEL_STEP,
        clamp_orbit_camera_move_speed,
    )

    assert clamp_orbit_camera_move_speed(99.0) == pytest.approx(1.0)
    assert clamp_orbit_camera_move_speed(0.01) == pytest.approx(0.2)
    assert clamp_orbit_camera_move_speed("bad") == pytest.approx(0.65)
    assert pytest.approx(0.05) == ORBIT_CAMERA_MOVE_SPEED_WHEEL_STEP


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
