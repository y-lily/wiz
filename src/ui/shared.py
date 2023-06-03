
from enum import Enum
from typing import Any, TypeAlias, TypeVar

from pygame import Surface

from . import tuple_math

T = TypeVar("T")
pair: TypeAlias = tuple[T, T]


def no_op(*args: Any, **kwargs: Any) -> None:
    pass


def build_transparent_surface(size: pair[int]) -> Surface:
    surface = Surface(size).convert_alpha()
    surface.fill((0, 0, 0, 0))
    return surface


def calculate_subsurface_size(surface: Surface, padding: tuple[int, int, int, int]) -> pair[int]:
    for pad in padding:
        assert pad >= 0

    absolute_size = surface.get_size()
    return tuple_math.sub(absolute_size,
                          (padding[0] + padding[2], padding[1] + padding[3]))


class Direction(Enum):

    UP = "up"
    RIGHT = "right"
    DOWN = "down"
    LEFT = "left"
    UPLEFT = "upleft"
    DOWNLEFT = "downleft"
    UPRIGHT = "upright"
    DOWNRIGHT = "downright"
