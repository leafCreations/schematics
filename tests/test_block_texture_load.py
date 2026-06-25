from PIL import Image

from helpers.block_texture_load import animation_first_frame, load_block_texture_image
from registries.loader import BLOCK_TEXTURES_FOLDER


def test_animation_first_frame_crops_smoker_lit_strip():
    path = BLOCK_TEXTURES_FOLDER / "smoker_front_on.png"
    image = Image.open(path).convert("RGBA")
    cropped = animation_first_frame(image, path)

    assert cropped.size == (16, 16)
    assert image.size == (16, 48)


def test_animation_first_frame_leaves_single_frame_furnace_lit():
    path = BLOCK_TEXTURES_FOLDER / "furnace_front_on.png"
    image = Image.open(path).convert("RGBA")
    cropped = animation_first_frame(image, path)

    assert cropped.size == (16, 16)
    assert cropped.tobytes() == image.tobytes()


def test_load_block_texture_image_uses_first_frame_not_full_strip():
    path = BLOCK_TEXTURES_FOLDER / "blast_furnace_front_on.png"
    loaded = load_block_texture_image(path, 30)
    full_strip = Image.open(path).convert("RGBA").resize((30, 30), Image.Resampling.NEAREST)

    assert loaded.size == (30, 30)
    assert loaded.tobytes() != full_strip.tobytes()
