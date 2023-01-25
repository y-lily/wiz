import pathlib
from abc import abstractmethod
from enum import Enum
from typing import NoReturn, TypeAlias

Path: TypeAlias = str | pathlib.Path


RESOURCE_DIR = pathlib.Path(__file__).parent.parent.parent / "res"


def assert_never(value: NoReturn) -> NoReturn:
    assert False, f"Unexpected value {value} of type {type(value).__name__}"


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
