"""Resolve schematic PNG paths for in-app render preview."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from uuid import UUID

import helpers.constants as constants
from helpers.layer_groups import collect_layer_groups
from helpers.paths import OUTPUT_SCHEMATICS_FOLDER, name_slug

_PREVIEW_Y_SUFFIX_RE = re.compile(r"_y(-?\d+)$")
_FACADE_DIRECTION_SUFFIX_RE = re.compile(r"_facades_([NSEW])$")

FACADE_PREVIEW_DIRECTIONS = ("N", "S", "W", "E")


def preview_session_dir(session_id: str | UUID) -> Path:
    """Directory for one editor session's in-app preview PNGs."""
    return OUTPUT_SCHEMATICS_FOLDER / "_preview" / str(session_id)


def clear_preview_session_dir(path: Path) -> None:
    """Remove one editor session's in-app preview PNG directory."""
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


def preview_floor_groups(layers: list[dict], grid: dict) -> list[str]:
    """Floor group names for the in-app preview selector (editor groups, no roofs)."""
    groups = collect_layer_groups(layers, grid)
    return [group for group in groups if "roof" not in group.lower()]


def y_index_from_preview_png(path: Path) -> int | None:
    match = _PREVIEW_Y_SUFFIX_RE.search(path.stem)
    if match is None:
        return None
    return int(match.group(1))


def list_facade_preview_pngs(schematics_dir: Path) -> list[Path]:
    """Per-direction structure facade preview PNGs in N → S → W → E order."""
    if not schematics_dir.is_dir():
        return []

    paths: list[Path] = []
    for direction in FACADE_PREVIEW_DIRECTIONS:
        path = schematics_dir / f"Structure_facades_{direction}.png"
        if path.is_file():
            paths.append(path)
    return paths


def list_site_facade_preview_pngs(schematics_dir: Path) -> list[Path]:
    """Per-direction site facade preview PNGs in N → S → W → E order."""
    if not schematics_dir.is_dir():
        return []

    paths: list[Path] = []
    for direction in FACADE_PREVIEW_DIRECTIONS:
        path = schematics_dir / f"Site_facades_{direction}.png"
        if path.is_file():
            paths.append(path)
    return paths


def list_materials_preview_pngs(schematics_dir: Path) -> list[Path]:
    """Materials list preview PNG in the preview session dir."""
    if not schematics_dir.is_dir():
        return []

    path = schematics_dir / "Materials_list.png"
    if path.is_file():
        return [path]
    return []


def list_site_topdown_preview_pngs(schematics_dir: Path) -> list[Path]:
    """Per-Y site top-down preview PNGs sorted ascending by Y (-1 → 0 → 1)."""
    if not schematics_dir.is_dir():
        return []

    paths = list(schematics_dir.glob("Site_topdown_y*.png"))
    return sorted(
        paths,
        key=lambda path: (
            y_index_from_preview_png(path) if y_index_from_preview_png(path) is not None else 0,
            path.name,
        ),
    )


def list_gallery_preview_pngs(
    schematics_dir: Path,
    render_name: str,
    *,
    group_name: str | None = None,
) -> list[Path]:
    """In-app preview gallery PNGs for the selected render type."""
    if render_name == constants.RENDER_STRUCTURE_FACADES:
        return list_facade_preview_pngs(schematics_dir)
    if render_name == constants.RENDER_SITE_FACADES:
        return list_site_facade_preview_pngs(schematics_dir)
    if render_name == constants.RENDER_PATH:
        return list_site_topdown_preview_pngs(schematics_dir)
    if render_name == constants.RENDER_MATERIALS:
        return list_materials_preview_pngs(schematics_dir)
    if render_name == constants.RENDER_TOP_VIEW and group_name is not None:
        return list_group_preview_pngs(schematics_dir, group_name)
    return []


def list_direction_facade_preview_pngs(schematics_dir: Path, render_name: str) -> list[Path]:
    if render_name == constants.RENDER_STRUCTURE_FACADES:
        return list_facade_preview_pngs(schematics_dir)
    if render_name == constants.RENDER_SITE_FACADES:
        return list_site_facade_preview_pngs(schematics_dir)
    return []


def direction_from_facade_preview_png(path: Path) -> str | None:
    match = _FACADE_DIRECTION_SUFFIX_RE.search(path.stem)
    if match is None:
        return None
    return match.group(1)


def list_group_preview_pngs(schematics_dir: Path, group_name: str) -> list[Path]:
    """Per-Y preview PNGs for a group, sorted by ascending worldgen Y index."""
    if not schematics_dir.is_dir():
        return []

    slug = name_slug(group_name)
    pattern = f"Structure_{slug}_y*.png"
    paths = list(schematics_dir.glob(pattern))
    return sorted(
        paths,
        key=lambda path: (
            y_index_from_preview_png(path) if y_index_from_preview_png(path) is not None else 0,
            path.name,
        ),
    )


# Preferred preview when multiple render types run (Phase A: top_view first).
_RENDER_PRIORITY = (
    constants.RENDER_TOP_VIEW,
    constants.RENDER_STRUCTURE_FACADES,
    constants.RENDER_PATH,
    constants.RENDER_SITE_FACADES,
    constants.RENDER_MATERIALS,
    constants.RENDER_ROOF,
)

# Fixed output suffixes from renderers (see renderers/*.py).
_FIXED_OUTPUT_SUFFIXES: dict[str, tuple[str, ...]] = {
    constants.RENDER_STRUCTURE_FACADES: ("structure_facades.png",),
    constants.RENDER_PATH: ("site_topdown.png",),
    constants.RENDER_SITE_FACADES: ("site_facades.png",),
    constants.RENDER_MATERIALS: ("materials_list.png",),
}


def _normalize_renders(renders: list[str]) -> set[str]:
    if constants.RENDER_ALL in renders:
        return set(_RENDER_PRIORITY)
    return set(renders)


def _structure_blueprint_pngs(schematics_dir: Path, *, roofs: bool) -> list[Path]:
    paths = sorted(schematics_dir.glob("Structure_*.png"))
    if roofs:
        return [path for path in paths if "roof" in path.stem.lower()]
    return [
        path
        for path in paths
        if "roof" not in path.stem.lower() and y_index_from_preview_png(path) is None
    ]


def _fixed_output_pngs(schematics_dir: Path, render_name: str) -> list[Path]:
    suffixes = _FIXED_OUTPUT_SUFFIXES.get(render_name, ())
    matches: list[Path] = []
    for suffix in suffixes:
        matches.extend(sorted(schematics_dir.glob(f"*_{suffix}")))
    return matches


def list_preview_pngs(schematics_dir: Path, renders: list[str]) -> list[Path]:
    """Return PNG paths produced by the given render selection, de-duplicated."""
    if not schematics_dir.is_dir():
        return []

    selected = _normalize_renders(renders)
    found: list[Path] = []
    seen: set[Path] = set()

    def add(paths: list[Path]) -> None:
        for path in paths:
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                found.append(path)

    for render_name in _RENDER_PRIORITY:
        if render_name not in selected:
            continue

        if render_name == constants.RENDER_TOP_VIEW:
            add(_structure_blueprint_pngs(schematics_dir, roofs=False))
        elif render_name == constants.RENDER_ROOF:
            add(_structure_blueprint_pngs(schematics_dir, roofs=True))
        else:
            add(_fixed_output_pngs(schematics_dir, render_name))

    return found


def primary_preview_png(
    schematics_dir: Path,
    renders: list[str],
    *,
    group_name: str | None = None,
) -> Path | None:
    """Pick the best single PNG for the Render tab preview."""
    if group_name is not None:
        previews = list_group_preview_pngs(schematics_dir, group_name)
        if previews:
            return previews[0]

    previews = list_preview_pngs(schematics_dir, renders)
    if previews:
        return previews[0]

    if not schematics_dir.is_dir():
        return None

    pngs = sorted(schematics_dir.glob("*.png"), key=lambda path: path.stat().st_mtime, reverse=True)
    return pngs[0] if pngs else None
