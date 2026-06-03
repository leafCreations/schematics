from registries.loader import BLOCK_PALETTES, BLOCK_REGISTRY, reload_registries


def test_reload_registries_refreshes_shared_dict_objects():
    registry_id = id(BLOCK_REGISTRY)
    palettes_id = id(BLOCK_PALETTES)

    reload_registries()

    assert id(BLOCK_REGISTRY) == registry_id
    assert id(BLOCK_PALETTES) == palettes_id
    assert isinstance(BLOCK_REGISTRY, dict)
    assert isinstance(BLOCK_PALETTES, dict)
