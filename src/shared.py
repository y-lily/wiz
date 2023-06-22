import pathlib
from abc import abstractmethod
from enum import Enum
from typing import TypeAlias, TypeVar

from pygame import Surface

# TODO:
# import tuple_math
from src import tuple_math

Path: TypeAlias = str | pathlib.Path

T = TypeVar("T")
pair: TypeAlias = tuple[T, T]


def no_op(*args: object, **kwargs: object) -> None:
    pass


def build_transparent_surface(size: pair[int]) -> Surface:
    surface = Surface(size).convert_alpha()
    surface.fill((0, 0, 0, 0))
    return surface


def calculate_subsurface_size(surface: Surface, padding: tuple[int, int, int, int]) -> pair[int]:
    for p in padding:
        assert p >= 0

    abs_size = surface.get_size()
    return tuple_math.sub(surface.get_size(),
                          (padding[0] + padding[2], padding[1] + padding[3]))


class Controller:

    @abstractmethod
    def update(self, dt: float) -> None: ...


class Direction(Enum):

    UP = "up"
    RIGHT = "right"
    DOWN = "down"
    LEFT = "left"
    UPLEFT = "upleft"
    DOWNLEFT = "downleft"
    UPRIGHT = "upright"
    DOWNRIGHT = "downright"
