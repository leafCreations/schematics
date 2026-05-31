from pathlib import Path

import pytest

from helpers.context import SchematicContext
from helpers.paths import BLOCK_TEXTURES_FOLDER


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "requires_assets: test needs the local assets/ folder with Minecraft textures",
    )


@pytest.fixture
def assets_dir() -> Path:
    return BLOCK_TEXTURES_FOLDER


@pytest.fixture
def sprite_size() -> int:
    from helpers import constants

    return constants.BLOCK_PX


@pytest.fixture
def ctx() -> SchematicContext:
    return SchematicContext(
        structure="test",
        stage=1,
        name="Test Structure",
        layers=[
            {
                "cells": [
                    ["A", "B", "C"],
                    ["D", "E", "F"],
                ],
            },
            {
                "cells": [
                    ["1", "2"],
                    ["3", "4"],
                ],
            },
        ],
        grid={"site_size": 30, "offset_x": 10, "offset_z": 5},
        block_registry={},
        assets_dir=Path("."),
        worldgen_template_dir=Path("."),
        output_schematics_dir=Path("."),
        output_worldgen_dir=Path("."),
    )
