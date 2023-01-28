from __future__ import annotations

from typing import (
    Any,
    Iterable,
    MutableSequence,
    Optional,
    SupportsIndex,
    Type,
    TypeVar,
    overload,
)

from pygame.rect import Rect
from pygame.sprite import Sprite
from pytmx import TiledElement, TiledMap

from .animation import Animation
from .character import NPC, Character
from .entity import MovingEntity
from .lua_defs import LuaMapTable, Trigger
from .sprite_sheet import SpriteKeeper

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


class Zone:

    def __init__(self, rect: Rect) -> None:
        self.rect = rect


class TriggerZone(Zone):

    def __init__(self, rect: Rect, trigger: Trigger) -> None:
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
    Provides convenient interface to detect sprite's collisions."""

    def __init__(self, zones: list[T] | None) -> None:
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
        # FIXME: Consider storing rects and updating them on get/set invocations.
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

    def __init__(self, tmx: TiledMap) -> None:

        self._tmx = tmx
        self._characters: set[Character] = set()
        self._sprite_keeper = SpriteKeeper()

        # The default layers have to exist.
        assert self.collision_layer is not None
        assert self.roof_layer is not None
        assert self.sprite_layer is not None
        assert self.trigger_layer is not None

    @property
    def tmx(self) -> TiledMap:
        return self._tmx

    @property
    def characters(self) -> tuple[Character, ...]:
        """
        NB: If the map is attached to a viewer, the sprites of the characters
        won't be loaded automatically.
        You can add the sprites manually via the viewer interface.
        """
        return tuple(self._characters)

    @property
    def default_layer_index(self) -> int:
        return self.get_layer_index("sprites")

    @property
    def collision_layer(self) -> TiledElement:
        return self.get_layer("collisions")

    @property
    def roof_layer(self) -> TiledElement:
        return self.get_layer("roof")

    @property
    def sprite_layer(self) -> TiledElement:
        return self.get_layer("sprites")

    @property
    def trigger_layer(self) -> TiledElement:
        return self.get_layer("interaction_zones")

    def add_characters(self, *characters: Character) -> None:
        self._characters.update(characters)

    def get_layer(self, name: str) -> TiledElement:
        return self._tmx.get_layer_by_name(name)

    def get_layer_index(self, name: str) -> int:
        return next(i for i, layer in enumerate(self.tmx.layers) if layer.name == name)

    def update(self, dt: float) -> None:
        for character in self.characters:
            character.update(dt)

    TChar = TypeVar("TChar", bound=Character)

    def spawn_char_call(self, name: str, table: LuaMapTable, x: int | None = None, y: int | None = None, char_type: Type[TChar] = NPC) -> TChar:
        assert not self.loaded, "Cannot invoke onLoad calls while already loaded."

        char_table = table.characters[name]
        entity_table = char_table.entity

        atlas = self._sprite_keeper.sprite(
            entity_table.source, entity_table.alpha)
        animations = Animation.from_table(table=entity_table, atlas=atlas)
        movement_speed: float = char_table.movement_speed if char_table.movement_speed is not None else entity_table.movement_speed
        position = char_table.position if x is None or y is None else {
            "x": x, "y": y}

        entity = MovingEntity(animations=animations,
                              movement_speed=movement_speed,
                              state=char_table.state,
                              face_direction=entity_table.face_direction,
                              frame=entity_table.frame,
                              position=position,
                              )

        trigger = char_table.trigger
        char = char_type(name=name, entity=entity, trigger=trigger)
        char.load_controllers(char_table)
        self.add_characters(char)
        return char
