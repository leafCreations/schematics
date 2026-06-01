#!/usr/bin/env python3
"""Convert stage{N}_structure.py files to stage{N}/structure.yaml + layers/*.yaml."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.structure_loader import load_structure_module


def _configure_yaml_quoting() -> None:
    def represent_str(representer, data: str):
        if any(char in data for char in "#@:!"):
            return representer.represent_scalar("tag:yaml.org,2002:str", data, style='"')

        return representer.represent_scalar("tag:yaml.org,2002:str", data)

    yaml.add_representer(str, represent_str)


def write_structure_yaml(
    config: dict,
    output_dir: Path,
    *,
    force: bool = False,
) -> None:
    if output_dir.exists() and not force:
        raise FileExistsError(f"Output directory already exists: {output_dir}")

    layers_dir = output_dir / "layers"
    layers_dir.mkdir(parents=True, exist_ok=True)

    layer_files: list[str] = []

    for layer in config["layers"]:
        layer_path = f"layers/layer_{int(layer['index']):02d}.yaml"
        layer_files.append(layer_path)

        with (output_dir / layer_path).open("w", encoding="utf-8") as handle:
            yaml.safe_dump(
                layer,
                handle,
                sort_keys=False,
                allow_unicode=True,
                default_flow_style=False,
            )

    metadata = {key: value for key, value in config.items() if key != "layers"}
    metadata["layer_files"] = layer_files

    with (output_dir / "structure.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(
            metadata,
            handle,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )


def migrate_structure(structure: str, stage: int, *, force: bool = False) -> Path:
    from helpers.paths import STRUCTURES_FOLDER

    source = STRUCTURES_FOLDER / structure / f"stage{stage}_structure.py"
    output_dir = STRUCTURES_FOLDER / structure / f"stage{stage}"

    config = load_structure_module(source.resolve())
    write_structure_yaml(config, output_dir, force=force)
    return output_dir


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate Python structure files to YAML.")
    parser.add_argument("structure", help="Structure name, e.g. residence")
    parser.add_argument("stage", type=int, help="Stage number, e.g. 1")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing stage directory",
    )
    return parser.parse_args()


def main() -> int:
    _configure_yaml_quoting()
    args = _parse_args()
    output_dir = migrate_structure(args.structure, args.stage, force=args.force)
    print(f"Migrated to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
