"""Layer group names, filtering, and render visibility in ``structure.yaml`` grid."""

from __future__ import annotations

from typing import Any

from helpers.layer_management import layer_label
from helpers.layer_visibility import is_layer_visible


def get_defined_groups(grid: dict[str, Any]) -> list[str]:
    """Empty groups stored on ``grid.groups`` (saved with site settings)."""
    raw = grid.get("groups")

    if not isinstance(raw, list):
        return []

    return [str(name).strip() for name in raw if str(name).strip()]


def collect_layer_groups(
    layers: list[dict[str, Any]],
    grid: dict[str, Any] | None = None,
) -> list[str]:
    """Unique group names in layer order, then any ``grid.groups`` without layers."""
    groups: list[str] = []

    for index, layer in enumerate(layers):
        name = layer_label(layer, index)

        if name not in groups:
            groups.append(name)

    if grid is not None:
        for name in get_defined_groups(grid):
            if name not in groups:
                groups.append(name)

    return groups


def layer_indices_in_group(layers: list[dict[str, Any]], group: str) -> list[int]:
    return [index for index, layer in enumerate(layers) if layer_label(layer, index) == group]


def group_name_exists(
    layers: list[dict[str, Any]],
    grid: dict[str, Any],
    name: str,
    *,
    except_name: str | None = None,
) -> bool:
    normalized = name.strip()

    if not normalized or normalized == except_name:
        return False

    return normalized in collect_layer_groups(layers, grid)


def add_defined_group(grid: dict[str, Any], name: str) -> None:
    """Register an empty group on ``grid.groups``."""
    normalized = name.strip()
    groups = get_defined_groups(grid)

    if normalized not in groups:
        groups.append(normalized)
        grid["groups"] = groups


def rename_group(
    layers: list[dict[str, Any]],
    grid: dict[str, Any],
    old_name: str,
    new_name: str,
) -> None:
    """Rename a group on layers, ``hidden_groups``, and ``grid.groups``."""
    normalized = new_name.strip()

    if not normalized or old_name == normalized:
        return

    for index, layer in enumerate(layers):
        if layer_label(layer, index) == old_name:
            layer["group"] = normalized

    defined = get_defined_groups(grid)

    if old_name in defined:
        grid["groups"] = [normalized if name == old_name else name for name in defined]

    hidden = get_hidden_groups(grid)

    if old_name in hidden:
        hidden.discard(old_name)
        hidden.add(normalized)
        grid["hidden_groups"] = sorted(hidden)


def remove_group(
    layers: list[dict[str, Any]],
    grid: dict[str, Any],
    name: str,
) -> None:
    """Remove a group; layers keep cells but lose the ``group`` field when it matched."""
    for index, layer in enumerate(layers):
        if layer_label(layer, index) == name:
            layer.pop("group", None)

    defined = [group for group in get_defined_groups(grid) if group != name]

    if defined:
        grid["groups"] = defined
    else:
        grid.pop("groups", None)

    set_group_hidden(grid, name, hidden=False)


def get_hidden_groups(grid: dict[str, Any]) -> set[str]:
    raw = grid.get("hidden_groups")

    if not isinstance(raw, list):
        return set()

    return {str(name) for name in raw}


def is_group_hidden(group: str, grid: dict[str, Any]) -> bool:
    return group in get_hidden_groups(grid)


def set_group_hidden(grid: dict[str, Any], group: str, *, hidden: bool) -> None:
    """Persist group visibility on ``grid.hidden_groups`` (saved with site settings)."""
    names = get_hidden_groups(grid)

    if hidden:
        names.add(group)
    else:
        names.discard(group)

    if names:
        grid["hidden_groups"] = sorted(names)
    else:
        grid.pop("hidden_groups", None)


def is_layer_render_visible(
    layer: dict[str, Any],
    list_index: int,
    grid: dict[str, Any],
) -> bool:
    """Layer is included in renders when both layer and its group are visible."""
    if not is_layer_visible(layer):
        return False

    return layer_label(layer, list_index) not in get_hidden_groups(grid)


def visible_layer_array_indices(
    layers: list[dict[str, Any]],
    grid: dict[str, Any] | None = None,
) -> list[int]:
    grid_data = grid or {}
    return [
        index
        for index, layer in enumerate(layers)
        if is_layer_render_visible(layer, index, grid_data)
    ]


def layer_matches_group_filter(
    layer: dict[str, Any],
    list_index: int,
    group_filter: str | None,
) -> bool:
    if group_filter is None:
        return True

    return layer_label(layer, list_index) == group_filter
