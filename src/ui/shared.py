
from enum import Enum
from typing import NoReturn, TypeAlias, TypeVar

from pygame.surface import Surface

T = TypeVar("T")
pair: TypeAlias = tuple[T, T]


def assert_never(value: NoReturn) -> NoReturn:
    assert False, f"Unexpected value {value} of type {type(value).__name__}"


def build_transparent_surface(size: pair[int]) -> Surface:
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
