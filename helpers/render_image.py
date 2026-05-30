from PIL import Image, ImageDraw

CANVAS_BACKGROUND = (255, 255, 255)


def create_canvas(width: int, height: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (width, height), CANVAS_BACKGROUND)
    draw = ImageDraw.Draw(img)
    return img, draw
