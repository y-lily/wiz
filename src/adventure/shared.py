import pathlib
from abc import abstractmethod
from enum import Enum
from typing import NoReturn, TypeAlias, TypeVar

from transitions.core import EventData

from .lua_defs import LuaTable

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


TLuaTable = TypeVar("TLuaTable", bound=LuaTable)


def load_table(path: Path) -> TLuaTable:
    path = pathlib.Path(path)
    import lupa
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    with open(path, "r") as file:
        return lua.execute(file.read())


def from_event(event: EventData, key: str, index: int = 0) -> object:
    try:
        return event.kwargs[key]
    except KeyError:
        return tuple(event.args)[index]


def from_event_row(event: EventData, *keys: str, index: int = 0) -> list[object]:
    return [from_event(event, key, i+index) for i, key in enumerate(keys)]
