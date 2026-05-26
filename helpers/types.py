# helpers/types.py

from typing import TypeAlias
from PIL import ImageFont

Renders: TypeAlias = list[str]

Token: TypeAlias = str
RawToken: TypeAlias = str
BlockId: TypeAlias = str

Panel: TypeAlias = dict[str, int]
Layout: TypeAlias = dict[str, int]
Rect: TypeAlias = list[int]
Cell: TypeAlias = dict[str, object]
BackgroundColor: TypeAlias = tuple[int, int, int]

Fonts: TypeAlias = dict[str, ImageFont.ImageFont]