from helpers.materials import collect_raw_tokens_from_layers


def test_collect_raw_tokens_from_layers_skips_empty_cells():
    layers = [
        {
            "cells": [
                ["PLANKS:oak", "."],
                [".", "COBBLESTONE"],
            ],
        },
        {
            "cells": [["GRASS"]],
        },
    ]

    assert collect_raw_tokens_from_layers(layers) == [
        "PLANKS:oak",
        "COBBLESTONE",
        "GRASS",
    ]
