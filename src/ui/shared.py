
from enum import Enum
from typing import NoReturn, TypeAlias

from pygame.surface import Surface

pair: TypeAlias = tuple[float, float]


def assert_never(value: NoReturn) -> NoReturn:
    assert False, f"Unexpected value {value} of type {type(value).__name__}"


def build_transparent_surface(size: pair) -> Surface:
    surface = Surface(size).convert_alpha()
    surface.fill((0, 0, 0, 0))
    return surface


class Direction(Enum):

    UP = "up"
    RIGHT = "right"
    DOWN = "down"
    LEFT = "left"
    UPLEFT = "upleft"
    DOWNLEFT = "downleft"
    UPRIGHT = "upright"
    DOWNRIGHT = "downright"
