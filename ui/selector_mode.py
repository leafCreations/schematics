"""Structure grid selector tool modes."""

from __future__ import annotations

from enum import Enum


class SelectorMode(Enum):
    RECTANGLE = "rectangle"
    SAME_BLOCK = "same_block"
