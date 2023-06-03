import pathlib
from abc import abstractmethod
from enum import Enum
from typing import TypeAlias

Path: TypeAlias = str | pathlib.Path


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
