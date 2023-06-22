"""Representation of config APIs."""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Literal, Mapping, TypedDict

if TYPE_CHECKING:
    from src.game import Game

    from .adventure_map import AdventureMap, Zone
    from .character import Character


class Blueprint(Mapping[str, object]):

    ...


class AdventureMapBlueprint(Blueprint):

    tmx: str
    entities: Mapping[str, EntityBlueprint]
    characters: Mapping[str, CharacterBlueprint]
    entryPoints: Mapping[str, Position]

    onLoad: Mapping[str, Callable[[AdventureMap], None]]


class EntityBlueprint(Blueprint):

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


class CharacterBlueprint(Blueprint):

    name: str
    entity: EntityBlueprint
    state: str
    defined_states: Mapping[int, StateBlueprint]
    position: Position
    movement_speed: int | None
    trigger: AdventureMapTrigger


class StateBlueprint(Blueprint):

    # TODO
    name: str


class Position(TypedDict):

    x: int
    y: int


class AdventureMapTrigger(Blueprint):

    onEnter: Callable[[AdventureMapTrigger, Character, 'Game', Zone], None]
    onExit: Callable[[AdventureMapTrigger, Character, 'Game', Zone], None]
    onUse: Callable[[AdventureMapTrigger, Character, 'Game', Zone], None]
