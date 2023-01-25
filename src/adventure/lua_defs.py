from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Literal, Mapping, TypedDict

if TYPE_CHECKING:
    from .adventure_map import AdventureMap
    from .character import Character
    from .map_controller import MapViewer


class LuaTable(Mapping[str, object]):

    ...


class LuaMapTable(LuaTable):

    tmx: str
    entities: Mapping[str, LuaEntityTable]
    characters: Mapping[str, LuaCharacterTable]
    entryPoints: Mapping[str, LuaPositionTable]

    onLoad: Mapping[str, Callable[[LuaMapTable, AdventureMap], None]]


class LuaEntityTable(Mapping[str, object]):

    source: str
    alpha: bool
    framewidth: int
    frameheight: int
    flip: Literal[None, "right-left"]
    framerate: int
    face_direction: Literal["up", "upright", "right",
                            "downright", "down", "downleft", "left", "upleft"]
    frame: int
    movement_speed: int
    animations: Mapping[str, Mapping[str, Mapping[object, int]]]


class LuaCharacterTable(Mapping[str, object]):

    entity: LuaEntityTable
    state: str
    defined_states: Mapping[int, LuaStateTable]
    position: LuaPositionTable
    movement_speed: int | None


class LuaStateTable(Mapping[str, object]):

    # TODO
    name: str


class LuaPositionTable(TypedDict):

    x: int
    y: int


class Trigger:

    onEnter: Callable[[Trigger, Character, MapViewer], None]
    onExit: Callable[[Trigger, Character, MapViewer], None]
    onUse: Callable[[Trigger, Character, MapViewer], None]
