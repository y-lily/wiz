from __future__ import annotations

from typing import (
    Any,
    Iterable,
    MutableSequence,
    Self,
    SupportsIndex,
    TypeVar,
    overload,
)

from pygame import Rect
from pytmx import TiledElement, TiledMap

# TODO:
# from sprites import SpriteKeeper
from src.sprites import SpriteKeeper

from .blueprint import AdventureMapTrigger
from .character import Character
from .character_loader import CharacterBuilder
from .entity import Entity, MovingEntity


class Zone:

    def __init__(self, rect: Rect) -> None:
        self._rect = rect

    @property
    def rect(self) -> Rect:
        return self._rect


class TriggerZone(Zone):

    def __init__(self, rect: Rect, trigger: AdventureMapTrigger) -> None:
        super().__init__(rect)
        self._trigger = trigger

    @property
    def trigger(self) -> AdventureMapTrigger:
        return self._trigger


class CharacterTriggerZone(TriggerZone):

    def __init__(self, character: Character) -> None:
        assert character.trigger is not None
        super().__init__(rect=character.entity.collision_box,
                         trigger=character.trigger)
        self._character = character

    @property
    def character(self) -> Character:
        return self._character


TZone = TypeVar("TZone", bound=Zone)


class ZoneList(MutableSequence[TZone]):

    def __init__(self, zones: list[TZone] | None = None) -> None:
        self._zones = zones if zones is not None else []

    @overload
    def __getitem__(self, i: SupportsIndex, /) -> TZone: ...
    @overload
    def __getitem__(self, s: slice, /) -> Self: ...

    def __getitem__(self, it: SupportsIndex | slice, /) -> TZone | Self:
        if isinstance(it, SupportsIndex):
            return self._zones[it]
        return type(self)(self._zones[it])

    @overload
    def __setitem__(self, i: SupportsIndex, o: TZone, /) -> None: ...
    @overload
    def __setitem__(self, s: slice, o: Iterable[TZone], /) -> None: ...

    def __setitem__(self, it: Any, o: Any, /) -> None:
        self._zones[it] = o

    def __delitem__(self, i: SupportsIndex | slice, /) -> None:
        del (self._zones[i])

    def __len__(self) -> int:
        return len(self._zones)

    def insert(self, index: int, value: TZone) -> None:
        self._zones.insert(index, value)

    @property
    def rects(self) -> list[Rect]:
        return [zone.rect for zone in self._zones]

    def collides(self, entity: Entity) -> bool:
        if isinstance(entity, MovingEntity):
            return entity.find_collision(self.rects) > -1
        else:
            return entity.rect.collidelist(self.rects) > -1

    def get_colliding_zones(self, entity: Entity) -> Self:
        if isinstance(entity, MovingEntity):
            collisions = entity.find_all_collisions(self.rects)
        else:
            collisions = entity.rect.collidelistall(self.rects)

        return type(self)([self._zones[i] for i in collisions])


class AdventureMap:

    loaded: bool = False
    default_layer: int = 0
    _collision_zones: ZoneList[Zone]
    _trigger_zones: ZoneList[TriggerZone]

    def __init__(self, tmx: TiledMap, sprite_keeper: SpriteKeeper) -> None:
        self._tmx = tmx
        self._characters: set[Character] = set()
        self._character_builder = CharacterBuilder(sprite_keeper)

    @property
    def characters(self) -> tuple[Character, ...]:
        return tuple(self._characters)

    @property
    def character_builder(self) -> CharacterBuilder:
        return self._character_builder

    @property
    def collision_zones(self) -> ZoneList[Zone]:
        return self._collision_zones

    @property
    def tmx(self) -> TiledMap:
        return self._tmx

    @property
    def trigger_zones(self) -> ZoneList[TriggerZone]:
        return self._trigger_zones

    def add_characters(self, *characters: Character) -> None:
        self._characters.update(characters)

    def get_layer(self, name: str) -> TiledElement:
        return self._tmx.get_layer_by_name(name)

    def get_layer_index(self, name: str) -> int:
        return next(i for i, layer in enumerate(self.tmx.layers) if layer.name == name)

    def remove_characters(self, *characters: Character) -> None:
        self._characters.difference_update(characters)

    def set_collision_zones(self, new_zones: ZoneList[Zone]) -> None:
        self._collision_zones = new_zones

    def set_trigger_zones(self, new_zones: ZoneList[TriggerZone]) -> None:
        self._trigger_zones = new_zones

    def update(self, dt: float) -> None:
        for character in self.characters:
            character.update(dt)
