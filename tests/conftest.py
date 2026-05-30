from pathlib import Path

import pytest

from helpers.context import SchematicContext


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
