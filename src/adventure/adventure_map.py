from __future__ import annotations

from typing import (
    Any,
    Iterable,
    MutableSequence,
    Optional,
    SupportsIndex,
    TypeVar,
    overload,
)

from pygame.event import Event
from pygame.rect import Rect
from pygame.sprite import Sprite
from pytmx import TiledElement, TiledMap

from ..sprites import SpriteKeeper
from .blueprint import AdventureMapTrigger
from .character import Character
from .character_loader import CharacterBuilder
from .entity import MovingEntity

try:
    from typing import Self  # type: ignore [attr-defined]
except ImportError:
    from typing_extensions import Self


class Zone:

    def __init__(self, rect: Rect) -> None:
        self.rect = rect


class TriggerZone(Zone):

    def __init__(self, rect: Rect, trigger: AdventureMapTrigger) -> None:
        super().__init__(rect)
        self.trigger = trigger


class CharacterTriggerZone(TriggerZone):

    def __init__(self, character: Character) -> None:
        assert character.trigger is not None
        super().__init__(rect=character.entity.collision_box, trigger=character.trigger)
        self.character = character


T = TypeVar("T", bound=Zone)


class ZoneList(MutableSequence[T]):
    """
    Provides a convenient interface to detect sprite's collisions.
    """

    def __init__(self, zones: list[T] | None = None) -> None:
        self._zones = zones if zones is not None else []

    @overload
    def __getitem__(self, i: SupportsIndex, /) -> T: ...
    @overload
    def __getitem__(self, s: slice, /) -> Self[T]: ...

    def __getitem__(self, it: SupportsIndex | slice, /) -> T | Self[T]:
        if isinstance(it, SupportsIndex):
            return self._zones[it]
        return type(self)(self._zones[it])

    @overload
    def __setitem__(self, i: SupportsIndex, o: T, /) -> None: ...
    @overload
    def __setitem__(self, s: slice, o: Iterable[T], /) -> None: ...

    def __setitem__(self, it: Any, o: Any, /) -> None:
        self._zones[it] = o

    def __delitem__(self, i: SupportsIndex | slice, /) -> None:
        del (self._zones[i])

    def __len__(self) -> int:
        return len(self._zones)

    def insert(self, index: int, value: T) -> None:
        self._zones.insert(index, value)

    @property
    def rects(self) -> list[Rect]:
        # NOTE: Consider storing rects and updating them on get/set invocations.
        return [zone.rect for zone in self._zones]

    def collides_sprite(self, sprite: Sprite) -> bool:
        if isinstance(sprite, MovingEntity):
            return sprite.find_collision(self.rects) > -1
        else:
            assert sprite.rect is not None
            return sprite.rect.collidelist(self.rects) > -1

    def get_colliding_zone(self, sprite: Sprite) -> Optional[T]:
        if isinstance(sprite, MovingEntity):
            collision_index = sprite.find_collision(self.rects)
        else:
            assert sprite.rect is not None
            collision_index = sprite.rect.collidelist(self.rects)

        if collision_index < 0:
            return None

        return self._zones[collision_index]

    def get_all_colliding_zones(self, sprite: Sprite) -> Self[T]:
        if isinstance(sprite, MovingEntity):
            collisions = sprite.find_all_collisions(self.rects)
        else:
            assert sprite.rect is not None
            collisions = sprite.rect.collidelistall(self.rects)

        return type(self)([self._zones[i] for i in collisions])


class AdventureMap:

    loaded: bool = False

    def __init__(self, tmx: TiledMap, sprite_keeper: SpriteKeeper) -> None:
        self._tmx = tmx
        self._characters: set[Character] = set()
        self._sprite_keeper = sprite_keeper
        self._char_builder = CharacterBuilder(sprite_keeper)
        self.default_layer = 0

    def set_trigger_zones(self, zones: ZoneList[TriggerZone]) -> None:
        self._trigger_zones = zones

    def set_collision_zones(self, zones: ZoneList[Zone]) -> None:
        self._collision_zones = zones

    @property
    def char_builder(self) -> CharacterBuilder:
        return self._char_builder

    @property
    def trigger_zones(self) -> ZoneList[TriggerZone]:
        return self._trigger_zones

    @property
    def collision_zones(self) -> ZoneList[Zone]:
        return self._collision_zones

    @property
    def tmx(self) -> TiledMap:
        return self._tmx

    @property
    def characters(self) -> tuple[Character, ...]:
        return tuple(self._characters)

    def add_characters(self, *characters: Character) -> None:
        self._characters.update(characters)

    def remove_characters(self, *characters: Character) -> None:
        self._characters.difference_update(characters)

    def get_layer(self, name: str) -> TiledElement:
        return self._tmx.get_layer_by_name(name)

    def get_layer_index(self, name: str) -> int:
        return next(i for i, layer in enumerate(self.tmx.layers) if layer.name == name)

    def update(self, dt: float) -> None:
        for character in self.characters:
            character.update(dt)
