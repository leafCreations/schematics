from helpers.sprite_baker.compose_bed import compose_bed_entry
from helpers.sprite_baker.compose_chest import compose_chest_entry
from helpers.sprite_baker.compose_door import compose_door_entry
from helpers.sprite_baker.compose_fence import compose_fence_entry
from helpers.sprite_baker.compose_log import compose_log_entry
from helpers.sprite_baker.compose_simple import compose_simple_entry
from helpers.sprite_baker.compose_slab import compose_slab_entry
from helpers.sprite_baker.compose_stairs import compose_stairs_entry
from helpers.sprite_baker.compose_torch import compose_torch_entry
from helpers.sprite_baker.registry import register_composer


def register_default_composers() -> None:
    register_composer("solid", compose_simple_entry)
    register_composer("facing_block", compose_simple_entry)
    register_composer("slab", compose_slab_entry)
    register_composer("stairs", compose_stairs_entry)
    register_composer("door", compose_door_entry)
    register_composer("bed", compose_bed_entry)
    register_composer("chest", compose_chest_entry)
    register_composer("fence", compose_fence_entry)
    register_composer("log", compose_log_entry)
    register_composer("torch", compose_torch_entry)
