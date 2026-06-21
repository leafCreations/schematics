"""Structure identity fields in ``structure.yaml`` (not grid/layers)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_STRUCTURE_SLUG_RE = re.compile(r"[^a-z]+")
_STRUCTURE_SLUG_VALID = re.compile(r"^[a-z]+$")


def normalize_structure_slug(structure: str) -> str:
    """Lowercase a-z only — used in paths and ``output_folder``."""
    slug = _STRUCTURE_SLUG_RE.sub("", structure.strip().lower())
    return slug or "structure"


def derive_output_folder(structure: str, stage: int) -> str:
    """Return ``stage{N}_{structure}`` for schematic/world output directories."""
    return f"stage{int(stage)}_{normalize_structure_slug(structure)}"


def derive_structure_name(structure: str, stage: int) -> str:
    """Return display title from structure id and stage (e.g. ``Residence Stage 1``)."""
    slug = normalize_structure_slug(structure) or "structure"
    return f"{slug.title()} Stage {int(stage)}"


def identity_from_structure_path(path: Path) -> tuple[str, int] | None:
    """Read ``(structure, stage)`` from ``structures/{name}/stage{N}/stage.yaml``."""
    try:
        stage_dir = path.parent.name
        structure_dir = path.parent.parent.name
    except (IndexError, AttributeError):
        return None

    if not stage_dir.startswith("stage"):
        return None

    try:
        stage = int(stage_dir.removeprefix("stage"))
    except ValueError:
        return None

    if not structure_dir or structure_dir.startswith("."):
        return None

    return structure_dir, stage


def apply_structure_identity(
    metadata: dict[str, Any],
    *,
    structure: str,
    stage: int,
) -> dict[str, str]:
    """Write identity fields and derived ``name`` / ``output_folder`` into *metadata*."""
    slug = normalize_structure_slug(structure)
    stage_value = int(stage)
    metadata["structure"] = slug
    metadata["stage"] = stage_value
    metadata["name"] = derive_structure_name(slug, stage_value)
    metadata["output_folder"] = derive_output_folder(slug, stage_value)
    return {
        "structure": metadata["structure"],
        "stage": str(metadata["stage"]),
        "name": metadata["name"],
        "output_folder": metadata["output_folder"],
    }


def validate_structure_slug(structure: str) -> None:
    """Raise ``ValueError`` when *structure* is not a lowercase path slug."""
    slug = normalize_structure_slug(structure)

    if not slug:
        raise ValueError("structure must not be empty")

    if structure.strip() != slug or not _STRUCTURE_SLUG_VALID.fullmatch(slug):
        raise ValueError(f"structure must be lowercase letters a-z only (got {structure!r})")


def read_structure_identity(metadata: dict[str, Any]) -> tuple[str, int, str, str]:
    structure = normalize_structure_slug(str(metadata.get("structure", "")))
    stage = int(metadata.get("stage", 1))
    name = derive_structure_name(structure, stage)
    output_folder = derive_output_folder(structure, stage)
    return structure, stage, name, output_folder
